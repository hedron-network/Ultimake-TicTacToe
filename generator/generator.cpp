#include "generator.h"
#include <fstream>

namespace Generator{
    void explore(board p1, board p2, int tour , std::ofstream& file)
    {
        //Premier condition : p1 gagne 
        if(BoardHandling::HasWon(p1)){
            for(int i = 0; i < 9; i++){
                if(p1 & (1 << i))
                    file << 1 << ", ";
                else if(p2 & (1 << i))
                    file << -1 << ", ";
                else
                    file << 0 << ", ";
            }
            file << 1 << "\n"; // X gagne
            return;
        }
        //Deuxime condition : p2 gagne 
        if(BoardHandling::HasWon(p2)){
            for(int i = 0; i < 9; i++){
                if(p1 & (1 << i))
                    file << 1 << ", ";
                else if(p2 & (1 << i))
                    file << -1 << ", ";
                else
                    file << 0 << ", ";
            }
            file << -1 << "\n"; // O gagne
            return;
        }
        // 3 eme condition : égalité 
        if(BoardHandling::hasTied(p1,p2)){
            for(int i = 0; i < 9; i++){
                if(p1 & (1 << i))
                    file << 1 << ", ";
                else if(p2 & (1 << i))
                    file << -1 << ", ";
                else
                    file << 0 << ", ";
            }
            file << 0 << "\n"; // personne gagne
            return;

        }

        //Récursivité
        for(int i =0;i<9;i++){
            board move = BoardHandling::IntToBoard(i);
            if(tour%2==0)
            {
                if(BoardHandling::MakeMove(move,p1,p2))
                {
                    explore(p1, p2, tour + 1, file);
                    p1 ^= move; // annuler le coup
                }

            }
            else { // O joue
                if(BoardHandling::MakeMove(move, p2, p1)){
                    explore(p1, p2, tour + 1, file);
                    p2 ^= move; // annuler le coup
                }
            }

        }
        


    }
}