#include <ap_int.h>

static const int nrow = 512;
static const int nw = 16;
static const int ncol = 8;

void matmult_naive() {
    
    float X[nrow][nw];
    float W[nw][ncol];
    float Y[nrow][ncol];

    for (int i = 0; i < nrow; ++i) {
        for (int j = 0; j < ncol; ++j) {
            Y[i][j] = 0.0;
            for (int k = 0; k < nw; ++k) {
                Y[i][j] += X[i][k] * W[k][j];
            }
        }
    }
}

void matmult_broadcast() {
    
    // Assume X and Y are partitioned along each row, so all elements 
    // of a row can be accessed in parallel
    // These would be filled with some data in a real testbench; 
    // here we just declare them to show the structure of the code
    float X[nrow][nw];
    float Y[nrow][ncol];
    #pragma HLS ARRAY_PARTITION variable=X type=complete dim=2
    #pragma HLS ARRAY_PARTITION variable=Y type=complete dim=2

    // Copy W to a local array with full partitioning
    float W[nw][ncol];
    float Wlocal[nw][ncol];
    #pragma HLS ARRAY_PARTITION variable=Wlocal type=complete dim=1
    #pragma HLS ARRAY_PARTITION variable=Wlocal type=complete dim=2
    for (int i = 0; i < nw; ++i) {
        for (int j = 0; j < ncol; ++j) {
            Wlocal[i][j] = W[i][j];
        }
    }

    // Create local array for each row of X and Y
    float Yrow[ncol];
    float Xrow[nw];
    #pragma HLS ARRAY_PARTITION variable=Yrow type=complete dim=0
    #pragma HLS ARRAY_PARTITION variable=Xrow type=complete dim=0
    
   
    for (int i = 0; i < nrow; ++i) {
#pragma HLS PIPELINE II=1

        // Copy the current row of X to a local array
        // Done in parallel since the row is fully partitioned
        for (int k = 0; k < nw; ++k) {
#pragma HLS UNROLL
            Xrow[k] = X[i][k];
        }

        // Compute current row of Y 
        for (int j = 0; j < ncol; ++j) {
#pragma HLS UNROLL
            Yrow[j] = 0.0;
            for (int k = 0; k < nw; ++k) {
#pragma HLS UNROLL
                Yrow[j] += Xrow[k] * Wlocal[k][j];
            }
            Y[i][j] = Yrow[j];
        }

        // Store the current row of Y back to the output array
        // Done in parallel since the row is fully partitioned
        for (int j = 0; j < ncol; ++j) {
#pragma HLS UNROLL
            Y[i][j] = Yrow[j];
        }
    }
}

static const int BW = 16;
static const int ACCW = 2 * BW + 8;

void matmul_systolic() {

    // Local arrays for the input, output, and intermediate values in the systolic array
    // These are partitioned along the columns to allow parallel access to all elements in a row
    ap_int<BW> X[nrow][nw];
    ap_int<ACCW> Y[nrow][ncol];
#pragma HLS ARRAY_PARTITION variable=X type=complete dim=2
#pragma HLS ARRAY_PARTITION variable=Y type=complete dim=2

    // The weight matrix is fully partitioned to allow parallel access to all elements in the systolic array
    ap_int<BW> W[nw][ncol];
#pragma HLS ARRAY_PARTITION variable=W type=complete dim=0

    // Local arrays for the delayed inputs and partial sums in the systolic array
    ap_int<BW> Xdly[nw][ncol];
    ap_int<ACCW> S[nw][ncol];
#pragma HLS ARRAY_PARTITION variable=Xdly type=complete dim=0
#pragma HLS ARRAY_PARTITION variable=S type=complete dim=0

    const int nt = nrow + nw + ncol - 2;

    
    // Initialize the Xdly and S arrays to 0
    for (int k = 0; k < nw; ++k) {
#pragma HLS UNROLL
        for (int j = 0; j < ncol; ++j) {
#pragma HLS UNROLL
            Xdly[k][j] = 0;
            S[k][j] = 0;
        }
    }

    for (int t = 0; t < nt; ++t) {
#pragma HLS PIPELINE II=1

        // Shift the Xdly array to the right
        for (int d = ncol - 1; d > 0; --d) {
#pragma HLS UNROLL
            for (int k = 0; k < nw; ++k) {
#pragma HLS UNROLL
                Xdly[k][d] = Xdly[k][d - 1];
            }
        }

        // Shift in the new row of X into the leftmost column of Xdly
        // Note unrolling is possible here since each row of X is fully partitioned
        for (int k = 0; k < nw; ++k) {
#pragma HLS UNROLL
            const int i = t - k;
            if (i >= 0 && i < nrow) {
                Xdly[k][0] = X[i][k];
            } else {
                Xdly[k][0] = 0;
            }
        }

        // Perform the systolic array computation for the current time step
        // Perform the products accumulate and shift along the rows
        for (int k = nw - 1; k > 0; --k) {
#pragma HLS UNROLL
            for (int j = 0; j < ncol; ++j) {
#pragma HLS UNROLL
                S[k][j] = Xdly[k][j] * W[k][j]+ S[k - 1][j];
            }
        }

        // Shift in the new products for the first row of the systolic array
        for (int j = 0; j < ncol; ++j) {
#pragma HLS UNROLL
            S[0][j] = Xdly[0][j] * W[0][j];
        }

        // Shift out the results from the bottom row of the systolic array to the output array Y
        // Note unrolling is possible here since each row of Y is fully partitioned
        for (int j = 0; j < ncol; ++j) {
#pragma HLS UNROLL
            const int i = t - nw - j + 1;
            if (i >= 0 && i < nrow) {
                Y[i][j] = S[nw - 1][j];
            }
        }
    }
}



       