#pragma once
#include "board.h"
#include "neural_net.h"

#ifdef _WIN32
    #include <intrin.h>
#else
    #include <x86intrin.h>
#endif  
#include <cstdint>
#include <vector>
struct Move{
    board prevBX;
    board prevBO;
    short prevActiveBoard;
    short chosenBoard;
    board prevBoard;
};
class Game {
public:
    Game();

    std::vector<float> get_state();
    void undo();
    std::vector<int> get_legal_moves();
    void apply_move(int move);
    int get_winner();
    bool is_done();
    float eval();
    void PrintGame() const;
    uint64_t get_hash() const;
    int GetCurrentPlayer() const;
    std::vector<float> get_features() const ;

private:
    void RecordMove(int move);
    bool MakeMoveAndCheckIfWon(int board, int move);
    std::vector<int> CalculateMoves(board* X,board* Y);
    int ExtractBoardFromMove(int move);
    bool TryMove(const int& boardIndex, const int& cellIndex);
    bool IsGameOver() const;
    int GetWinner() const;
    int GetActiveBoard() const;
    std::vector<Move> moveHistory;

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

