#include <iostream>
#include <limits>
#include "Game.h"

int main()
{
    std::cout<<"test"<<std::endl;
    unsigned short board = 0;
    BoardHandling::MakeUncheckedMove(BoardHandling::IntToBoard(1),board);
    BoardHandling::MakeUncheckedMove(BoardHandling::IntToBoard(5),board);
    auto moves = BoardHandling::AviableMoves(board,0);
    for(int move:moves){
        std::cout<<move<<" |";
    }
    return 0;
}
