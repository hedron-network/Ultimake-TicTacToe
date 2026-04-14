#include <stdio.h>
#include <iostream>
#include <stdint.h>
#include "board.h"

void print_board(uint16_t boardX, uint16_t boardO) {
    for (int i = 0; i < 9; i++) {
        // Check if bit i is set
        if (boardX & (1 << i))
            printf(" X ");
        else if(boardO & (1 << i)){
            printf(" O ");
        }
        else
            printf(" . ");

        // Newline after every 3 cells
        if (i % 3 == 2)
            printf("\n");
    }
}
int main(){
    unsigned short p1=0;
    unsigned short p2=0;
    while (!BoardHandling::hasTied(p1,p2))
    {
        int move;
        printf("move p1:\n");
        std::cin>>move;
        BoardHandling::MakeMove(BoardHandling::IntToBoard(move),p1,p2);   
        print_board(p1,p2);
        if(BoardHandling::HasWon(p1)){
            BoardHandling::MakeAllOnes(p1);
            break;
        }
        move=-1;
        printf("move p2:\n");
        std::cin>>move;
        BoardHandling::MakeMove(BoardHandling::IntToBoard(move),p2,p1); 
        print_board(p1,p2);  
        if(BoardHandling::HasWon(p2)){
            BoardHandling::MakeAllOnes(p2);
            break;
        }
    }
    if(p1==BoardHandling::AllOnes){
        printf("X won");
    }
    else if (p2==BoardHandling::AllOnes){
        printf("O won");
    }
    else{
        printf("tied");
    }
    
    return 0;
}