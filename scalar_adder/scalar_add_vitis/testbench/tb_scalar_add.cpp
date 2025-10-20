#include <iostream>

void add(int a, int b, int& c);

int main() {
    int result;
    add(7, 5, result);
    std::cout << "Result: " << result << std::endl;
    return 0;
}