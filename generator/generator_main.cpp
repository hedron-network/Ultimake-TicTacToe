#include "generator.h"

int main(){
    unsigned short p1=0;
    unsigned short p2=0;
    std::ofstream file("dataset.csv");

    Generator::explore(p1,p2,0,file);
    file.close();
    return 0;
}