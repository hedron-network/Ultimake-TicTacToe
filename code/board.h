#pragma once
typedef unsigned short board;

namespace BoardHandling {

    bool MakeMove(const board &move, board &playerBoard, const board &oponentBoard);

    bool HasWon(const board& board);

    board IntToBoard(const int& value);

}