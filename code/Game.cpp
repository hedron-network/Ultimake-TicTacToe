#include "Game.h"

#include <iostream>

Game::Game()
    : bigX(0), bigO(0), currentPlayer(1), activeBoard(-1), gameOver(false), winner(0)
{
    for (int i = 0; i < 9; ++i) {
        subX[i] = 0;
        subO[i] = 0;
    }
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
    }
    void Game::RecordMove(int move){
        Move currentMove;
        currentMove.prevBX = bigX;
        currentMove.prevBO = bigO;
        currentMove.prevActiveBoard = activeBoard;
        currentMove.chosenBoard=move/9;
        if(currentPlayer==1){
            currentMove.prevBoard=subX[move%9];
        }
        else{
            currentMove.prevBoard=subO[move%9];
        }
        moveHistory.push_back(currentMove);
    }

    bool Game::MakeMoveAndCheckIfWon(int board, int move){
        if(currentPlayer==1){
            BoardHandling::MakeUncheckedMove(BoardHandling::IntToBoard(move),subX[board]);
            if(BoardHandling::HasWon(subX[board])){
                bigX |= BoardHandling::IntToBoard(move);
                return true;
            }
            return false;
        }
        BoardHandling::MakeUncheckedMove(BoardHandling::IntToBoard(move),subO[board]);
        if(BoardHandling::HasWon(subX[board])){
            bigO |= BoardHandling::IntToBoard(move);
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
        if(BoardHandling::HasWon(bigX)||BoardHandling::HasWon(bigO)||BoardHandling::hasTied(bigO,bigX))
        {
            return true;
        }
        return false;
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


