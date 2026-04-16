#include <iostream>
#include <limits>
#include "Game.h"

int main()
{
    Game game;
    game.PrintGame();

    while (!game.IsGameOver()) {
        int boardIndex;
        int cellIndex;
        int activeBoard = game.GetActiveBoard();
        char playerMark = (game.GetCurrentPlayer() == 1) ? 'X' : 'O';

        if (activeBoard >= 0) {
            std::cout << "Player " << playerMark << " turn on board " << activeBoard << ". Enter cell (0-8): ";
            std::cin >> cellIndex;
            boardIndex = activeBoard;
        } else {
            std::cout << "Player " << playerMark << " choose board (0-8) and cell (0-8): ";
            std::cin >> boardIndex >> cellIndex;
        }

        if (!std::cin || !game.TryMove(boardIndex, cellIndex)) {
            std::cin.clear();
            std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
            std::cout << "Invalid move. Please try again.\n";
            continue;
        }

        game.PrintGame();
    }

    int winner = game.GetWinner();
    if (winner == 1) {
        std::cout << "X wins the Ultimate Tic-Tac-Toe!\n";
    } else if (winner == 2) {
        std::cout << "O wins the Ultimate Tic-Tac-Toe!\n";
    } else {
        std::cout << "The game is a tie.\n";
    }

    return 0;
}
