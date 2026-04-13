#include <cstdint>
typedef uint16_t board;

namespace BordHandling
{
    bool MakeMove(const board &move, board &playerMove, board &oponentBoard){
        const board blockedSpaces = playerMove |oponentBoard;
        const board Empty=0;
        if(move & blockedSpaces != Empty){//check for overlap
            return false;
        }
        playerMove |= move; // add the move
        return true;
    }
    bool HasWon(board &player){
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
    const board emptyBoard[9]{
        0,0,0,
        0,0,0,
        0,0,0
    };
}
