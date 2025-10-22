#include "../include/vmult.h"

// Vector multiplication function
void vec_mult(int *a, int *b, int *c, int n) {

    // HLS pragmas for optimization
#pragma HLS INTERFACE m_axi port=a offset=slave bundle=gmem
#pragma HLS INTERFACE m_axi port=b offset=slave bundle=gmem
#pragma HLS INTERFACE m_axi port=c offset=slave bundle=gmem
#pragma HLS INTERFACE s_axilite port=a bundle=control
#pragma HLS INTERFACE s_axilite port=b bundle=control
#pragma HLS INTERFACE s_axilite port=c bundle=control
#pragma HLS INTERFACE s_axilite port=n bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control


    // Buffering to optimize memory access
    int a_buf[VecMultConfig::MAX_SIZE], b_buf[VecMultConfig::MAX_SIZE];
    int c_buf[VecMultConfig::MAX_SIZE];

#pragma HLS ARRAY_PARTITION variable=a_buf block factor=VecMultConfig::UNROLL_FACTOR
#pragma HLS ARRAY_PARTITION variable=b_buf block factor=VecMultConfig::UNROLL_FACTOR
#pragma HLS ARRAY_PARTITION variable=c_buf block factor=VecMultConfig::UNROLL_FACTOR


    // Check for size limit
    if (n > VecMultConfig::MAX_SIZE) 
        n = VecMultConfig::MAX_SIZE;

    // Load into local buffers
    for (int i = 0; i < n; i++) {
#pragma HLS PIPELINE
        a_buf[i] = a[i];
        b_buf[i] = b[i];
    }

    // Unrolled compute loop
    for (int i = 0; i < n; i += VecMultConfig::UNROLL_FACTOR) {
#pragma HLS PIPELINE II=1
        for (int j = 0; j < VecMultConfig::UNROLL_FACTOR; j++) {
#pragma HLS UNROLL
            c_buf[i + j] = a_buf[i + j] * b_buf[i + j];
        }
    }
    
    // Store results back to global memory
    for (int i = 0; i < n; i++) {
#pragma HLS PIPELINE
        c[i] = c_buf[i];
    }
}