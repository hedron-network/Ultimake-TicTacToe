#pragma once
#include <vector>
#include <string>
#include "board.h"

namespace NeuralNet {
    
    void loadWeights(const std::string& path);
    float evaluate(unsigned short p1, unsigned short p2);
    float evaluate_raw(const float* input, int size);
    float evaluate_global(const float* input);
}