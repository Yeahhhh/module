#include <string>
#include <iostream>
#include <sstream>
#include <vector>

#include <yeah/cpp/text_io.hpp>
#include <yeah/cpp/text_parse.hpp>


#define DELIM ','
//#define DELIM ' '


void func2(std::vector<std::string> lines)
{
    const int n = lines.size();  // number of lines
    for (int i = 0; i < n; ++i) {
        std::vector<std::string> tokens = tokenlize(lines[i], DELIM);

        const int nn = tokens.size();
        for (int i = 0; i < nn; ++i) {
            std::cout << "token" << "\t" << i << "\t";
            std::cout << tokens[i] << std::endl;
        }
        std::cout << std::endl;
    }
}


int main(int argc, char **argv)
{
    if (argc == 1) {
        printf("%s <INPUTFILE>\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    std::vector<std::string> lines;
    load_fn_to_vecstr(argv[1], lines);
    func2(lines);

    return EXIT_SUCCESS;
}
