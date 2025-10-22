#ifndef VMULT_H
#define VMULT_H

namespace VecMultConfig {
    constexpr int MAX_SIZE = 1024;
    constexpr int UNROLL_FACTOR = 4;
}


void vec_mult(int *a, int *b, int *c, int n);

#endif
