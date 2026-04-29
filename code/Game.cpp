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
            subX[lastMove.chosenBoard]=lastMove.prevBoardX;
        }
        else{
            subO[lastMove.chosenBoard]=lastMove.prevBoardO;
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
            currentMove.prevBoardX=subX[currentMove.chosenBoard];
        }
        else{
            currentMove.prevBoardO=subO[currentMove.chosenBoard];
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

    std::cout << "BigO :"<< bigO<<std::endl;
    std::cout << "BigX :"<< bigX<<std::endl;
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
 
    float score = 1.5f * big + 1.0f * sub + 0.5f * tempo;
    score = std::clamp(score, -800000.0f, 800000.0f);
 
    // Score is always from X's perspective.
    // The Python minimax wrapper flips it for O's turn.
    return score;
}
 
float Game::EvaluateForcedMovePressure() {
    // Returns a score from X's perspective.
    // Positive = good for X, negative = bad for X.
    if (activeBoard == -1)
        return 0;
 
    float score = 0;
 
    // If we're forcing the opponent into a board where THEY have won,
    // they can play anywhere — this is good FOR THEM, bad for us.
    // If we're forcing them into a board where WE have won,
    // they can play anywhere — also good for them, bad for us.
    // The really meaningful thing: forcing them into a *finished* board
    // means they can play anywhere, which hurts us. Forcing them into
    // a board where we have a strong position is good.
 
    // From X's absolute perspective:
    bool xWonActive = BoardHandling::HasWon(subX[activeBoard]);
    bool oWonActive = BoardHandling::HasWon(subO[activeBoard]);
    bool finished   = IsBoardFinished(activeBoard);
 
    // If the active board is finished, opponent plays anywhere — mild negative
    if (finished) {
        // Slight penalty: we gave opponent freedom
        score -= 200;
    } else {
        // Extra value for having a strong presence on the forced board
        score += EvaluateSubBoard(activeBoard) * 0.3f;
    }
 
    // If it's X's turn and active board is one X is winning on, good for X
    // If it's O's turn and active board is one O is winning on, bad for X
    if (currentPlayer == 1) {
        // X is moving into activeBoard — reward X's presence there
        // (already captured in the sub-board eval above)
    } else {
        // O is being forced into activeBoard — if X controls it, great for X
        if (!finished) {
            score += EvaluateSubBoard(activeBoard) * 0.5f; // X perspective: positive if X leads there
        }
    }
 
    return score;
}
 
float Game::BoardWeight(int i) {
    if ((bigX | bigO) & BoardHandling::IntToBoard(i))
        return 0.1f; // finished boards barely matter
 
    if (i == activeBoard)
        return 1.5f; // the forced board is critical
 
    // Centre board is worth more than corners, corners more than edges
    if (i == 4) return 1.3f;                      // centre
    if (i == 0 || i == 2 || i == 6 || i == 8)
        return 1.1f;                               // corners
    return 1.0f;                                   // edges
}
 
float Game::EvaluateSubBoard(int i) {
    const board X = subX[i];
    const board O = subO[i];
 
    if (BoardHandling::HasWon(X)) return  10000;
    if (BoardHandling::HasWon(O)) return -10000;
 
    float score = 0;
 
    // All 8 winning lines in a 3×3 board (bit positions 0-8)
    const board winning[8] = {
        0x007, 0x038, 0x1C0,   // rows
        0x049, 0x092, 0x124,   // cols
        0x111, 0x054           // diagonals
    };
 
    for (auto line : winning) {
        int x = popcount(X & line);
        int o = popcount(O & line);
 
        if (x && o) continue; // blocked — no value
 
        if (x == 2) score += 200;
        if (x == 1) score +=  20;
        if (o == 2) score -= 200;
        if (o == 1) score -=  20;
    }
 
    // Small bonus for centre cell control
    const board centre = BoardHandling::IntToBoard(4);
    if (X & centre) score +=  15;
    if (O & centre) score -=  15;
 
    return score;
}
 
float Game::EvaluateBigBoard() {
    const float WIN = 900000;

    if (BoardHandling::HasWon(bigX)) return  WIN;
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

        if (x && o) continue;

        if (x == 2) score += 50000;
        if (x == 1) score +=  5000;
        if (o == 2) score -= 50000;
        if (o == 1) score -=  5000;

        // Alignment nudge: for each unclaimed board on this line,
        // add a fraction of its sub-board eval so the AI prefers
        // targeting boards that extend an existing chain.
        board remaining = line & ~bigX & ~bigO;
        while (remaining) {
            unsigned long idx;
            #ifdef _WIN32
                _BitScanForward(&idx, remaining);
            #else
                idx = __builtin_ctz(remaining);
            #endif
            remaining &= remaining - 1;
            float sub = EvaluateSubBoard(idx);
            // Scale down heavily — this is purely a tie-breaker
            if (!o) score += sub * 0.05f;
            if (!x) score -= sub * 0.05f;
        }
    }

    // Centre meta-board is especially valuable
    const board centre = BoardHandling::IntToBoard(4);
    if (bigX & centre) score +=  8000;
    if (bigO & centre) score -=  8000;

    return score;
}
   // Zobrist table
int Game::popcount(uint64_t x) {
#ifdef _WIN32
    return __popcnt64(x);
#else
    return __builtin_popcountll(x);
#endif
}



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
