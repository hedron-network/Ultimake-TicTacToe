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

    std::vector<float> Game::get_state(){  // vector<float> 
    }
    void Game::undo(){
        
    }
    std::vector<int> Game::get_legal_moves(){

    }
    bool Game::apply_move(int board, int move){
        if(currentPlayer==1){
            BoardHandling::MakeUncheckedMove(BoardHandling::IntToBoard(move),subX[board]);
            if(BoardHandling::HasWon(subX[board])){
                bigX |= BoardHandling::IntToBoard(move);
                return true;
            }
            currentPlayer=0;
            return false;
        }
        BoardHandling::MakeUncheckedMove(BoardHandling::IntToBoard(move),subO[board]);
        if(BoardHandling::HasWon(subX[board])){
            bigO |= BoardHandling::IntToBoard(move);
            return true;
        }
        currentPlayer=1;
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


