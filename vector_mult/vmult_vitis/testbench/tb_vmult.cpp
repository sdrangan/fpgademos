# include "../include/vmult.h"
#include <iostream>

int main() {
    int a[VecMultConfig::MAX_SIZE], b[VecMultConfig::MAX_SIZE], c[VecMultConfig::MAX_SIZE];
    int n = 256;

    for (int i = 0; i < n; i++) {
        a[i] = i;
        b[i] = 2 * i;
    }

    vec_mult(a, b, c, n);

    bool pass = true;
    for (int i = 0; i < n; i++) {
        if (c[i] != a[i] * b[i]) {
            std::cout << "Mismatch at " << i << ": " << c[i] << " != " << a[i] * b[i] << std::endl;
            pass = false;
        }
    }

    std::cout << (pass ? "Test passed!" : "Test failed!") << std::endl;
    return 0;
}
