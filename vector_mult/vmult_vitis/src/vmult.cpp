// Vector multiplication function
#include "../include/vmult.h"

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
    int a_buf[MAX_SIZE], b_buf[MAX_SIZE];
    int c_buf[MAX_SIZE];

#pragma HLS ARRAY_PARTITION variable=a_buf type=cyclic factor=UNROLL_FACTOR  dim=1
#pragma HLS ARRAY_PARTITION variable=b_buf type=cyclic factor=UNROLL_FACTOR  dim=1
#pragma HLS ARRAY_PARTITION variable=c_buf type=cyclic factor=UNROLL_FACTOR  dim=1


    // Check for size limit
    if (n > MAX_SIZE) 
        n = MAX_SIZE;

    // Load into local buffers
    // We need an II=2 since there are two arrays to read into
    input_loop:  for (int i = 0; i < n; i++) {
#pragma HLS PIPELINE II=2
        a_buf[i] = a[i];
        b_buf[i] = b[i];
    }

    // Multiplication loop with optional pipelining / unrolling
    mult_loop:
#if UNROLL_FACTOR > 1
#pragma HLS unroll factor=UNROLL_FACTOR
#elif PIPELINE_EN
#pragma HLS pipeline
#endif
    for (int i = 0; i < n; i++) {
        c_buf[i] = a_buf[i] * b_buf[i];
    }


    // Store results back to global memory
    output_loop:  for (int i = 0; i < n; i++) {
#pragma HLS PIPELINE
        c[i] = c_buf[i];
    }
}