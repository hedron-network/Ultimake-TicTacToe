#pragma once
#include "board.h"

class Game {
public:
    Game();

    bool TryMove(int boardIndex, int cellIndex);
    void PrintGame() const;
    bool IsGameOver() const;
    int GetWinner() const;
    int GetCurrentPlayer() const;
    int GetActiveBoard() const;

private:
    board subX[9];
    board subO[9];
    board bigX;
    board bigO;
    int currentPlayer;
    int activeBoard;
    bool gameOver;
    int winner;

    bool IsBoardFinished(int boardIndex) const;
    bool IsBoardFull(int boardIndex) const;
    void UpdateSubBoardStatus(int boardIndex);
    void UpdateBigBoard();
    bool HasWonBig(const board player) const;
    bool AllSubBoardsFinished() const;
    char CellChar(int boardIndex, int cellIndex) const;
};
