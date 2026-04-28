#pragma once
#ifdef _WIN32
    #include <intrin.h>
#else
    #include <x86intrin.h>
#endif
#include <vector>
typedef unsigned short board;

namespace BoardHandling {

    bool MakeMove(const board &move, board &playerBoard, const board &oponentBoard);
    void MakeUncheckedMove(const board &move, board &playerBoard);
    bool CheckMove(const board &move, board &playerBoard, const board &oponentBoard);
    bool hasTied(const board &p1,const board &p2);
    bool HasWon(const board& board);

    board AviableSpaces(const board &playerBoard, const board &OpponentBoard);
    board IntToBoard(const int& value);
    std::vector<int> AviableMoves(const int &boardNumber, const board &playerBoard, const board &OpponentBoard);
    void MakeAllOnes(board &board);
    void MakeAllZeros(board &board);
    int CompactMove(const int &board,const int &move);
    constexpr  board emptyBigBoard[9]{
        0,0,0,
        0,0,0,
        0,0,0
    };
    constexpr board AllOnes = 0x1FF;
    constexpr board FULL_MASK = (1 << 9) - 1;
}