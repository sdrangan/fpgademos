#include <ap_int.h>

void kernel_tb() {

    ap_uint<64> mem[1024];  // The Native BRAM interface
    ap_uint<32> read_ind = 0;   // Control registers (AXI4-Lite)
    ap_uint<32> write_ind = 100;
    int n = 100;

    // Intialize memory with some data
    for (int i = 0; i < n; i++) {
        mem[read_ind + i] = ...;
    }

    kernel(mem, read_ind, write_ind, n);

    // Check results in mem[write_ind ... write_ind+n-1]
    for (int i = 0; i < n; i++) {
        assert(mem[write_ind + i] == ...);
    }
)

void kernel(
    ap_uint<64> mem[1024],  // The Native BRAM interface
    ap_uint<32> read_ind,   // Control registers (AXI4-Lite)
    ap_uint<32> write_ind,
    int n                   
) {
    // 1. Define the Native BRAM interface for the memory
    #pragma HLS INTERFACE bram port=mem
    
    // 2. Define the Control Interface (AXI4-Lite) for scalars and kernel control
    #pragma HLS INTERFACE s_axilite port=read_ind
    #pragma HLS INTERFACE s_axilite port=write_ind
    #pragma HLS INTERFACE s_axilite port=n
    #pragma HLS INTERFACE s_axilite port=return

    for (int i = 0; i < n; i++) {
        #pragma HLS PIPELINE II=1
        
        // Native access: Address is sent, data returns next cycle
        ap_uint<64> data = mem[read_ind + i];

        // ... do some computation ...

        mem[write_ind + i] = data;
    }
}