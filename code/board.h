#pragma once

namespace BordHandling {

    void MakeMove(const unsigned short& player,
                  unsigned short& x,
                  unsigned short& y);

    bool HasWon(unsigned short& board);

    unsigned short IntToBoard(const int& value);

}