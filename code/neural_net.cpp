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
    void reloadWeights(const std::string& path) {
        loadWeights(path);  // just call it again, it overwrites the statics
    }
    float evaluate_raw(const float* input, int input_size) {
        
        float h1[128], h2[64];

        // FC1: 90 → 128
        for (int i = 0; i < 128; i++) {
            h1[i] = fc1_b[i];
            for (int j = 0; j < input_size; j++)
                h1[i] += fc1_w[i][j] * input[j];
            h1[i] = relu(h1[i]);
        }

        // FC2: 128 → 64
        for (int i = 0; i < 64; i++) {
            h2[i] = fc2_b[i];
            for (int j = 0; j < 128; j++)
                h2[i] += fc2_w[i][j] * h1[j];
            h2[i] = relu(h2[i]);
        }

        // FC3: 64 → 1
        float output = fc3_b[0];
        for (int j = 0; j < 64; j++)
            output += fc3_w[0][j] * h2[j];

        return std::tanh(output);
    }

    float evaluate_global(const float* input) {
        return evaluate_raw(input, 90);
    }
}