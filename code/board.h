#pragma once
typedef unsigned short board;

namespace BoardHandling {

    bool MakeMove(const board &move, board &playerBoard, const board &oponentBoard);
    bool hasTied(const board &p1,const board &p2);
    bool HasWon(const board& board);

    board IntToBoard(const int& value);
    void MakeAllOnes(board &board);
    void MakeAllZeros(board &board);

    const board emptyBigBoard[9]{
        0,0,0,
        0,0,0,
        0,0,0
    };
    const board AllOnes = 0x1FF;

}