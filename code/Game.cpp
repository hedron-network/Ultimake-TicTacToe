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

bool Game::IsBoardFull(int boardIndex) const
{
    const board allMoves = subX[boardIndex] | subO[boardIndex];
    return allMoves == BoardHandling::AllOnes;
}

bool Game::IsBoardFinished(int boardIndex) const
{
    return BoardHandling::HasWon(subX[boardIndex]) ||
           BoardHandling::HasWon(subO[boardIndex]) ||
           IsBoardFull(boardIndex);
}

void Game::UpdateSubBoardStatus(int boardIndex)
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

bool Game::HasWonBig(const board player) const
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

char Game::CellChar(int boardIndex, int cellIndex) const
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

bool Game::TryMove(int boardIndex, int cellIndex)
{
    if (boardIndex < 0 || boardIndex > 8 || cellIndex < 0 || cellIndex > 8) {
        return false;
    }

    if (activeBoard >= 0 && boardIndex != activeBoard) {
        if (!IsBoardFinished(activeBoard)) {
            return false;
        }
    }

    if (IsBoardFinished(boardIndex)) {
        return false;
    }

    board moveMask = BoardHandling::IntToBoard(cellIndex);
    board &playerBoard = (currentPlayer == 1) ? subX[boardIndex] : subO[boardIndex];
    board &opponentBoard = (currentPlayer == 1) ? subO[boardIndex] : subX[boardIndex];

    if (!BoardHandling::MakeMove(moveMask, playerBoard, opponentBoard)) {
        return false;
    }

    UpdateSubBoardStatus(boardIndex);
    UpdateBigBoard();

    int nextTarget = cellIndex;
    if (nextTarget < 0 || nextTarget > 8 || IsBoardFinished(nextTarget)) {
        activeBoard = -1;
    } else {
        activeBoard = nextTarget;
    }

    if (HasWonBig(currentPlayer == 1 ? bigX : bigO)) {
        gameOver = true;
        winner = currentPlayer;
    } else if (AllSubBoardsFinished()) {
        gameOver = true;
        winner = 3;
    } else {
        currentPlayer = 3 - currentPlayer;
    }
    return true;
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


