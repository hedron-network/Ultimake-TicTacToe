#include <stdio.h>
#include <stdint.h>
#include "board.h"

void print_board(uint16_t board) {
    for (int i = 0; i < 9; i++) {
        // Check if bit i is set
        if (board & (1 << i))
            printf(" X ");
        else
            printf(" . ");

        // Newline after every 3 cells
        if (i % 3 == 2)
            printf("\n");
    }
}
int main(){
    print_board(BoardHandling::IntToBoard(5));
    return 0;
}