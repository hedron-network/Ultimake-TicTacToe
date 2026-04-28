#include "Game.h"

#include <iostream>

Game::Game()
    : bigX(0), bigO(0), currentPlayer(1), activeBoard(-1), gameOver(false), winner(0)
{
    for (int i = 0; i < 9; ++i) {
        subX[i] = 0;
        subO[i] = 0;
    }
    NeuralNet::loadWeights(".\\model_weights.json");
}
float Game::eval() {
    // build 90-float feature vector (same logic as Python extract_features)
    float input[90];
    for (int b = 0; b < 9; b++)
        for (int c = 0; c < 9; c++) {
            int idx = b*9+c, mask = 1<<c;
            input[idx] = (subX[b]&mask) ? 1.f : (subO[b]&mask) ? -1.f : 0.f;
        }
    for (int i = 0; i < 9; i++) {
        int mask = 1<<i;
        input[81+i] = (bigX&mask) ? 1.f : (bigO&mask) ? -1.f : 0.f;
    }
    float score = NeuralNet::evaluate_global(input);  // new function, same structure
    return currentPlayer == 1 ? score : -score;
}
// In your Game class, add:
std::vector<float> Game::get_features() const {
    std::vector<float> feats(90);
    for (int b = 0; b < 9; b++)
        for (int c = 0; c < 9; c++) {
            int mask = 1 << c;
            feats[b*9+c] = (subX[b]&mask) ? 1.f : (subO[b]&mask) ? -1.f : 0.f;
        }
    for (int i = 0; i < 9; i++) {
        int mask = 1 << i;
        feats[81+i] = (bigX&mask) ? 1.f : (bigO&mask) ? -1.f : 0.f;
    }
    return feats;
}
bool Game::IsBoardFull(const int &boardIndex) const
{
    return BoardHandling::hasTied(subX[boardIndex],subO[boardIndex]);
}

bool Game::IsBoardFinished(const int &boardIndex) const
{
    return BoardHandling::HasWon(subX[boardIndex]) ||
           BoardHandling::HasWon(subO[boardIndex]) ||
           BoardHandling::hasTied(subX[boardIndex],subO[boardIndex]);
}

void Game::UpdateSubBoardStatus(const int &boardIndex)
{
    if ((bigX | bigO) & BoardHandling::IntToBoard(boardIndex)) {
        return; // already recorded
    }

    if (BoardHandling::HasWon(subX[boardIndex])) {
        bigX |= BoardHandling::IntToBoard(boardIndex);
    } else if (BoardHandling::HasWon(subO[boardIndex])) {
        bigO |= BoardHandling::IntToBoard(boardIndex);
    }
}

void Game::UpdateBigBoard()
{
    for (int i = 0; i < 9; ++i) {
        if (!((bigX | bigO) & BoardHandling::IntToBoard(i)) && IsBoardFinished(i)) {
            UpdateSubBoardStatus(i);
        }
    }
}

bool Game::HasWonBig(const board &player) const
{
    return BoardHandling::HasWon(player);
}

bool Game::AllSubBoardsFinished() const
{
    for (int i = 0; i < 9; ++i) {
        if (!IsBoardFinished(i)) {
            return false;
        }
    }
    return true;
}
    std::vector<float> Game::get_state() {
        std::vector<float> state;
        state.reserve(406);

        // Determine "my" and "opp" boards based on current player
        board* myBoards  = (currentPlayer == 1) ? subX : subO;
        board* oppBoards = (currentPlayer == 1) ? subO : subX;
        board  myBig     = (currentPlayer == 1) ? bigX  : bigO;
        board  oppBig    = (currentPlayer == 1) ? bigO  : bigX;

        // Plane 0: current player's pieces (81 cells)
        for (int b = 0; b < 9; ++b)
            for (int c = 0; c < 9; ++c)
                state.push_back((myBoards[b] & BoardHandling::IntToBoard(c)) ? 1.f : 0.f);

        // Plane 1: opponent's pieces (81 cells)
        for (int b = 0; b < 9; ++b)
            for (int c = 0; c < 9; ++c)
                state.push_back((oppBoards[b] & BoardHandling::IntToBoard(c)) ? 1.f : 0.f);

        // Plane 2: sub-boards won by current player (81 cells, entire board = 1)
        for (int b = 0; b < 9; ++b) {
            float val = (myBig & BoardHandling::IntToBoard(b)) ? 1.f : 0.f;
            for (int c = 0; c < 9; ++c) state.push_back(val);
        }

        // Plane 3: sub-boards won by opponent (81 cells)
        for (int b = 0; b < 9; ++b) {
            float val = (oppBig & BoardHandling::IntToBoard(b)) ? 1.f : 0.f;
            for (int c = 0; c < 9; ++c) state.push_back(val);
        }

        // Plane 4: valid target boards (81 cells)
        for (int b = 0; b < 9; ++b) {
            float val = (activeBoard == -1 || activeBoard == b) && !IsBoardFinished(b) ? 1.f : 0.f;
            for (int c = 0; c < 9; ++c) state.push_back(val);
        }

        // Scalar: current player
        state.push_back(currentPlayer == 1 ? 1.f : 0.f);

        return state; // length 406
    }
    void Game::undo(){
        Move lastMove = moveHistory.back();
        if(currentPlayer==1){
            currentPlayer=0;
        }
        else{
            currentPlayer=1;
        }
        bigX=lastMove.prevBX;
        bigO=lastMove.prevBO;
        activeBoard=lastMove.prevActiveBoard;
        if(currentPlayer==1){
            subX[lastMove.chosenBoard]=lastMove.prevBoard;
        }
        else{
            subO[lastMove.chosenBoard]=lastMove.prevBoard;
        }
        moveHistory.pop_back();
    }
    std::vector<int> Game::get_legal_moves(){
        if(currentPlayer==1){
            return CalculateMoves(subX,subO);
        }
        return CalculateMoves(subO,subX);
    }
    std::vector<int> Game::CalculateMoves(board* X, board* Y){
        if(activeBoard!=-1){
            return BoardHandling::AviableMoves(activeBoard,X[activeBoard],Y[activeBoard]);
        }
        else{
            std::vector<int> moves;
            for(int i =0;i<9;i++){
                if(IsBoardFinished(i)){
                    continue;
                }
                auto newMoves= BoardHandling::AviableMoves(i,X[i],Y[i]);
                moves.insert(moves.end(), newMoves.begin(), newMoves.end());
            }
            return moves;
        }
    }
    void Game::apply_move(int move){
        RecordMove(move);
        MakeMoveAndCheckIfWon(move/9,move%9);
        if(currentPlayer==1){
            currentPlayer=0;
        }
        else{
            currentPlayer=1;
        }
        SetActiveBoard(move%9);
    }
    void Game::RecordMove(int move){
        Move currentMove;
        currentMove.prevBX = bigX;
        currentMove.prevBO = bigO;
        currentMove.prevActiveBoard = activeBoard;
        currentMove.chosenBoard=move/9;
        if(currentPlayer==1){
            currentMove.prevBoard=subX[currentMove.chosenBoard];
        }
        else{
            currentMove.prevBoard=subO[currentMove.chosenBoard];
        }
        moveHistory.push_back(currentMove);
    }

    bool Game::MakeMoveAndCheckIfWon(int board, int move){
        if(currentPlayer==1){
            BoardHandling::MakeUncheckedMove(BoardHandling::IntToBoard(move),subX[board]);
            if(BoardHandling::HasWon(subX[board])){
                bigX |= BoardHandling::IntToBoard(board);
                return true;
            }
            return false;
        }
        BoardHandling::MakeUncheckedMove(BoardHandling::IntToBoard(move),subO[board]);
        if(BoardHandling::HasWon(subO[board])){
            bigO |= BoardHandling::IntToBoard(board);
            return true;
        }
        return false;
    }

    void Game::SetActiveBoard(int board){
        if(IsBoardFinished(board)){
            activeBoard=-1;
            return;
        }
        activeBoard =board;
    }
    
    int Game::get_winner(){
        if(BoardHandling::HasWon(bigX)){
            return 1;
        }
        if(BoardHandling::HasWon(bigO)){
            return -1;
        }
        return 0;
    }
    bool Game::is_done(){
        if(BoardHandling::HasWon(bigX) || BoardHandling::HasWon(bigO)){
            return true;
        }
        for(int i=0;i<9;i++){
            if(!IsBoardFinished(i)){
                return false;
            }
        }
        return true;
    }

    int Game::ExtractBoardFromMove(int move){
        return move/9;
    }


char Game::CellChar(const int &boardIndex, const int &cellIndex) const
{
    const board mask = BoardHandling::IntToBoard(cellIndex);
    if (subX[boardIndex] & mask) {
        return 'X';
    }
    if (subO[boardIndex] & mask) {
        return 'O';
    }
    return '.';
}

void Game::PrintGame() const
{
    std::cout << "Ultimate Tic-Tac-Toe\n";
    for (int bigRow = 0; bigRow < 3; ++bigRow) {
        for (int smallRow = 0; smallRow < 3; ++smallRow) {
            for (int bigCol = 0; bigCol < 3; ++bigCol) {
                int boardIndex = bigRow * 3 + bigCol;
                for (int smallCol = 0; smallCol < 3; ++smallCol) {
                    int cellIndex = smallRow * 3 + smallCol;
                    std::cout << ' ' << CellChar(boardIndex, cellIndex) << ' ';
                }
                if (bigCol < 2) {
                    std::cout << "|";
                }
            }
            std::cout << '\n';
        }
        if (bigRow < 2) {
            std::cout << "-----------\n";
        }
    }
    if (activeBoard >= 0) {
        std::cout << "Active board: " << activeBoard << "\n";
    } else {
        std::cout << "Active board: any unfinished board\n";
    }
    std::cout << "Next player: " << (currentPlayer == 1 ? 'X' : 'O') << '\n';
}

bool Game::IsGameOver() const
{
    return gameOver;
}

int Game::GetWinner() const
{
    return winner;
}

int Game::GetCurrentPlayer() const
{
    return currentPlayer;
}

int Game::GetActiveBoard() const
{
    return activeBoard;
}

    // Zobrist table — initialized once at program start
    static uint64_t ZOBRIST[9][9][2];  // [board][cell][player 0=X,1=O]
    static uint64_t ZOBRIST_ACTIVE[10]; // active board: 0–8, or 9 for "any"
    static uint64_t ZOBRIST_PLAYER;    // XOR in when it's O's turn
    static bool zobrist_ready = false;

    static void init_zobrist() {
        // Simple xorshift64 seeded deterministically
        uint64_t s = 0xDEADBEEFCAFEBABEULL;
        auto rng = [&]() {
            s ^= s << 13; s ^= s >> 7; s ^= s << 17; return s;
        };
        for (auto& b : ZOBRIST)
            for (auto& c : b)
                for (auto& p : c) p = rng();
        for (auto& v : ZOBRIST_ACTIVE) v = rng();
        ZOBRIST_PLAYER = rng();
        zobrist_ready = true;
    }

    uint64_t Game::get_hash() const {
    if (!zobrist_ready) init_zobrist();

    uint64_t h = 0;
    for (int b = 0; b < 9; ++b) {
        unsigned long idx;
        board mx = subX[b], mo = subO[b];
        while (mx) {
            _BitScanForward(&idx, mx);
            h ^= ZOBRIST[b][idx][0];
            mx &= mx - 1;
        }
        while (mo) {
            _BitScanForward(&idx, mo);
            h ^= ZOBRIST[b][idx][1];
            mo &= mo - 1;
        }
    }
    h ^= ZOBRIST_ACTIVE[activeBoard == -1 ? 9 : activeBoard];
    if (currentPlayer != 1) h ^= ZOBRIST_PLAYER;
    return h;
}
