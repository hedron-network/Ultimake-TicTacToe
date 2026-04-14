#include "board.h"

namespace BoardHandling
{
    bool MakeMove(const board &move, board &playerBoard,const board &oponentBoard){
        const board blockedSpaces = playerBoard |oponentBoard;
        const board Empty=0;
        const board Overlap = move & blockedSpaces;
        if(Overlap != Empty){//check for overlap
            return false;
        }
        playerBoard |= move; // add the move
        return true;
    }
    bool hasTied(const board &p1,const board &p2){
        const board allMoves=p1|p2;
        const board unplayedMoves = allMoves^AllOnes;
        return unplayedMoves==0;
    }
    bool HasWon(const board &player){
        const board winningPositions[8] = {
        0x007, 0x038, 0x1C0, //rows
        0x049, 0x092, 0x124, //collums
        0x111, 0x054 //diagonals
        };
        for(board winningPosition: winningPositions){
            if((player & winningPosition) == winningPosition){
                return true;
            }
        }
        return false;
    }
    
    board IntToBoard(const int& pos){
        return 1<<pos;
    }
    void MakeAllOnes(board &board){
        board |= AllOnes;//All ones = 0x1FF
    }
    void MakeAllZeros(board &board){
        board &= 0;
    }
    
}
