#pragma once
typedef unsigned short board;

namespace BoardHandling {

    bool MakeMove(const board &move, board &playerMove, board &oponentBoard);

    bool HasWon(board& board);

    board IntToBoard(const int& value);

}