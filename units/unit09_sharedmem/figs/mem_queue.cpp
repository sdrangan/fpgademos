// ------------------------------------------------------------
// Free‑running kernel with AXI‑Lite control + AXI‑MM queue
// ------------------------------------------------------------
#include <ap_int.h>
#include <hls_stream.h>

struct Command {
    ap_uint<64> src_addr;
    ap_uint<64> dst_addr;
    ap_uint<32> length;
    ap_uint<32> opcode;
};

// ------------------------------------------------------------
// Kernel
// ------------------------------------------------------------
void kernel(
    ap_uint<64>  queue_base_addr,   // AXI‑Lite: base of descriptor ring
    ap_uint<32>  queue_write_ind,   // AXI‑Lite: producer index (PS)
    ap_uint<32>  queue_len,         // AXI‑Lite: ring capacity
    ap_uint<32> *queue_read_ind,    // AXI‑Lite: consumer index (kernel)
    ap_uint<64> *mem                // AXI‑MM: descriptor + data memory
) {
#pragma HLS INTERFACE s_axilite port=queue_base_addr
#pragma HLS INTERFACE s_axilite port=queue_write_ind
#pragma HLS INTERFACE s_axilite port=queue_len
#pragma HLS INTERFACE s_axilite port=queue_read_ind
#pragma HLS INTERFACE m_axi     port=mem offset=slave
#pragma HLS INTERFACE ap_ctrl_none port=return

    // Local copy of read pointer
    ap_uint<32> rd = 0;

    while (1) {
        // Poll AXI‑Lite registers
        ap_uint<32> wr = queue_write_ind;

        // Check if queue has outstanding commands
        if (rd != wr) {

            // Compute descriptor address
            ap_uint<64> cmd_addr =
                queue_base_addr + rd * sizeof(Command);

            // Deserialize command from memory
            Command cmd;
            ap_uint<64> *cmd_ptr = (ap_uint<64>*)cmd_addr;

            cmd.src_addr = mem[cmd_ptr - mem + 0];
            cmd.dst_addr = mem[cmd_ptr - mem + 1];
            cmd.length   = mem[cmd_ptr - mem + 2];
            cmd.opcode   = mem[cmd_ptr - mem + 3];

            // ------------------------------------------------
            // Process command (read → compute → write)
            // ------------------------------------------------
            // ... your computation here ...
            // ------------------------------------------------

            // Advance read pointer (circular buffer)
            rd = (rd + 1) % queue_len;

            // Publish updated read pointer to AXI‑Lite
            *queue_read_ind = rd;
        }
    }
}
