#include "Game.h"
#include <algorithm>
#include <iostream>

Game::Game()
    : bigX(0), bigO(0), currentPlayer(1), activeBoard(-1), gameOver(false), winner(0)
{
    for (int i = 0; i < 9; ++i) {
        subX[i] = 0;
        subO[i] = 0;
    }
    NeuralNet::loadWeights("./model_weights.json");
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
// Eval
float Game::eval() {
    float big   = EvaluateBigBoard();
    float sub   = 0;
    float tempo = EvaluateForcedMovePressure();

    for (int i = 0; i < 9; i++) {
        sub += BoardWeight(i) * EvaluateSubBoard(i);
    }

    float score = 5.0f * big + 1.0f * sub + 2.0f * tempo;
    score = std::clamp(score, -900000.0f, 900000.0f);

    // Negamax requires score from the perspective of the player TO MOVE
    return score;
}
float Game::EvaluateForcedMovePressure() {
    if (activeBoard == -1)
        return 0;

    float score = 0;
    // "opponent" board is whichever player is NOT moving
    board* oppBoard = (currentPlayer == 1) ? subO : subX;
    board* myBoard  = (currentPlayer == 1) ? subX : subO;

    // Forcing opponent into a board they've already won is great for us
    if (BoardHandling::HasWon(oppBoard[activeBoard]))
        score += 3000;

    // Forcing opponent into a board WE've won is bad for us
    if (BoardHandling::HasWon(myBoard[activeBoard]))
        score -= 3000;

    if (IsBoardFinished(activeBoard))
        score += 500;

    return score;
}
float Game::BoardWeight(int i) {
    if ((bigX | bigO) & BoardHandling::IntToBoard(i))
        return 0.2f; // finished boards matter less

    if (i == activeBoard)
        return 1.5f; // forced board is CRITICAL

    return 1.0f;
}
float Game::EvaluateSubBoard(int i) {
    const board X = subX[i];
    const board O = subO[i];

    if (BoardHandling::HasWon(X)) return 10000;
    if (BoardHandling::HasWon(O)) return -10000;

    float score = 0;

    const board winning[8] = {
        0x007, 0x038, 0x1C0,
        0x049, 0x092, 0x124,
        0x111, 0x054
    };

    for (auto line : winning) {
        int x = popcount(X & line);
        int o = popcount(O & line);

        if (x && o) continue;

        if (x == 2 && o == 0) score += 200;
        if (x == 1 && o == 0) score += 20;

        if (o == 2 && x == 0) score -= 200;
        if (o == 1 && x == 0) score -= 20;
    }

    return score;
}
int Game::popcount(uint64_t x) {
    int c = 0;
    while (x) {
        x &= (x - 1);
        c++;
    }
    return c;
}
float Game::EvaluateBigBoard() {
    const float WIN = 1e6;

    if (BoardHandling::HasWon(bigX)) return WIN;
    if (BoardHandling::HasWon(bigO)) return -WIN;

    float score = 0;

    const board winning[8] = {
        0x007, 0x038, 0x1C0,
        0x049, 0x092, 0x124,
        0x111, 0x054
    };

    for (auto line : winning) {
        int x = popcount(bigX & line);
        int o = popcount(bigO & line);

        if (x && o) continue; // blocked line

        if (x == 2 && o == 0) score += 50000;
        if (x == 1 && o == 0) score += 5000;

        if (o == 2 && x == 0) score -= 50000;
        if (o == 1 && x == 0) score -= 5000;
    }

    return score;
}

   // Zobrist table




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
            #ifdef _WIN32
                _BitScanForward(&idx, mx);
            #else
                idx = __builtin_ctz(mx);
            #endif
            h ^= ZOBRIST[b][idx][0];
            mx &= mx - 1;
        }
        while (mo) {
            #ifdef _WIN32
                _BitScanForward(&idx, mo);
            #else
                idx = __builtin_ctz(mo);
            #endif
            h ^= ZOBRIST[b][idx][1];
            mo &= mo - 1;
        }
    }
    h ^= ZOBRIST_ACTIVE[activeBoard == -1 ? 9 : activeBoard];
    if (currentPlayer != 1) h ^= ZOBRIST_PLAYER;
    return h;
}
