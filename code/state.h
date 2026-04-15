
#pragma once;
typedef unsigned short board;
typedef bool bit;
namespace State{
    struct MoveRecord
    {
        board prev_board;
        short affectedBoardIndex;
        short prev_activeBoard;
        bit prev_activePlayer;
        bool prev_isFreeMove;
    };
};