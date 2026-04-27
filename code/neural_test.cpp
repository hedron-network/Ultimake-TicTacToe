#include <iostream>
#include "board.h"
#include "neural_net.h"

int main() {
    NeuralNet::loadWeights("model_weights.json");
    
    // Position vide
    unsigned short p1 = 0, p2 = 0;
    std::cout << "Score position vide: " << NeuralNet::evaluate(p1, p2) << std::endl;
    
    // X gagne ligne du haut
    p1 = 0b000000111;
    p2 = 0;
    std::cout << "Score X gagne: " << NeuralNet::evaluate(p1, p2) << std::endl;
    
    // O gagne ligne du haut
    p1 = 0;
    p2 = 0b000000111;
    std::cout << "Score O gagne: " << NeuralNet::evaluate(p1, p2) << std::endl;
    
    return 0;
}