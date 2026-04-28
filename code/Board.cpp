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
    bool CheckMove(const board &move, board &playerBoard,const board &oponentBoard){
        const board blockedSpaces = playerBoard |oponentBoard;
        const board Empty=0;
        const board Overlap = move & blockedSpaces;
        if(Overlap != Empty){//check for overlap
            return false;
        }
        return true;
    }
    void MakeUncheckedMove(const board &move, board &playerBoard){
        playerBoard |=move;
    }
    bool hasTied(const board &p1,const board &p2){
        const board allMoves=p1|p2;
        return allMoves==AllOnes;
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
    board AviableSpaces(const board &playerBoard, const board &OpponentBoard){
        return ~(playerBoard|OpponentBoard)& FULL_MASK;
    }
    
    board IntToBoard(const int& pos){
        return 1<<pos;
    }


    std::vector<int> AviableMoves(const int& boardNumber,const board &playerBoard, const board &OpponentBoard){
        board b = AviableSpaces(playerBoard,OpponentBoard);

        std::vector<int> result;
        while (b) {
            unsigned long index;
            #ifdef _WIN32
                _BitScanForward(&index, b);
            #else
                index = __builtin_ctz(b);
            #endif
            int pos =int(index);// count trailing zeros
            result.push_back(boardNumber*9+pos);
            b &= (b - 1); // clear lowest set bit
        }
        return result;
    }
    void MakeAllOnes(board &board){
        board |= AllOnes;//All ones = 0x1FF
    }
    void MakeAllZeros(board &board){
        board &= 0;
    }
   
    
}
