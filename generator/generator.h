#pragma once
#include "board.h"
#include <fstream>

namespace Generator{
    void explore(board p1, board p2, int tour, std::ofstream& file);
}