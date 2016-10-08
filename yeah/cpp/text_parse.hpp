#ifndef _YEAH_CPP_TEXT_PARSE_HPP_
#define _YEAH_CPP_TEXT_PARSE_HPP_


#include <iostream>
#include <string>
#include <vector>


static void trim(std::string &s)
{
    size_t p;
    p = s.find_first_not_of(" \t");
    s.erase(0, p);

    p = s.find_last_not_of(" \t");
    if (std::string::npos != p)
        s.erase(p + 1);
}

// usage:
// std::vector<std::string> tokens = tokenlize(lines, ',');
// std::vector<std::string> tokens = tokenlize(lines, ' ');
std::vector<std::string> tokenlize(std::string &line, char delim)
{
    std::vector<std::string> tokens;
    std::stringstream ss(line);
    std::string t;

    // cout << line << endl;

    while (getline(ss, t, delim)) {
        trim(t);
        tokens.push_back(t);
    }

#if 0
#define NTOKEN 15
    const int n = tokens.size();
    if (n != NTOKEN) {
        std::cout << "number of tokens is wrong" << std::endl;
        exit(EXIT_FAILURE);
    }
#endif

    return tokens;
}


/*
std::istringstream iss(line);
std::vector<std::string> tokens;
while (iss) {
    std::string t;
    iss >> t;
    tokens.push_back(t);
}
*/


#endif
