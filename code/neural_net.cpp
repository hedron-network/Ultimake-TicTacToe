#include "neural_net.h"
#include "nlohmann/json.hpp"
#include <fstream>
#include <cmath>

using json = nlohmann::json;

namespace NeuralNet {
    std::vector<std::vector<float>> fc1_w, fc2_w, fc3_w;
    std::vector<float> fc1_b, fc2_b, fc3_b;

    float relu(float x) { return x > 0 ? x : 0; }

    void loadWeights(const std::string& path) {
        std::ifstream f(path);
        json data = json::parse(f);

        fc1_w = data["fc1.weight"].get<std::vector<std::vector<float>>>();
        fc1_b = data["fc1.bias"].get<std::vector<float>>();
        fc2_w = data["fc2.weight"].get<std::vector<std::vector<float>>>();
        fc2_b = data["fc2.bias"].get<std::vector<float>>();
        fc3_w = data["fc3.weight"].get<std::vector<std::vector<float>>>();
        fc3_b = data["fc3.bias"].get<std::vector<float>>();
    }

    float evaluate(unsigned short p1, unsigned short p2) {
        std::vector<float> input(9);
        for (int i = 0; i < 9; i++) {
            if (p1 & (1 << i)) input[i] = 1.0f;
            else if (p2 & (1 << i)) input[i] = -1.0f;
            else input[i] = 0.0f;
        }

        std::vector<float> h1(64);
        for (int i = 0; i < 64; i++) {
            h1[i] = fc1_b[i];
            for (int j = 0; j < 9; j++)
                h1[i] += fc1_w[i][j] * input[j];
            h1[i] = relu(h1[i]);
        }

        std::vector<float> h2(64);
        for (int i = 0; i < 64; i++) {
            h2[i] = fc2_b[i];
            for (int j = 0; j < 64; j++)
                h2[i] += fc2_w[i][j] * h1[j];
            h2[i] = relu(h2[i]);
        }

        float output = fc3_b[0];
        for (int j = 0; j < 64; j++)
            output += fc3_w[0][j] * h2[j];

        return tanh(output);
    }
}