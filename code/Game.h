#pragma once
#include "board.h"
#include <vector>

class Game {
public:
    Game();

    std::vector<float> get_state();
    void undo();
    std::vector<int> get_legal_moves();
    bool apply_move(int board, int move);
    int get_winner();
    bool is_done();

private:
    bool TryMove(const int& boardIndex, const int& cellIndex);
    void PrintGame() const;
    bool IsGameOver() const;
    int GetWinner() const;
    int GetCurrentPlayer() const;
    int GetActiveBoard() const;


    board subX[9];
    board subO[9];
    board bigX;
    board bigO;
    int currentPlayer;
    int activeBoard;
    bool gameOver;
    int winner;
    void SetActiveBoard(int board);

    bool IsBoardFinished(const int& boardIndex) const;
    bool IsBoardFull(const int& boardIndex) const;
    void UpdateSubBoardStatus(const int& boardIndex);
    void UpdateBigBoard();
    bool HasWonBig(const board& player) const;
    bool AllSubBoardsFinished() const;
    char CellChar(const int& boardIndex, const int& cellIndex) const;
};
