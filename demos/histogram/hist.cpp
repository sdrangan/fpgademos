#include "hist.hpp"

namespace memmgr = pysilicon::memmgr;


void hist(
    hls::stream<axis_word_t>& in_stream, 
    hls::stream<axis_word_t>& out_stream, 
    mem_word_t* mem) {
#pragma HLS INTERFACE axis port=in_stream
#pragma HLS INTERFACE axis port=out_stream
#pragma HLS INTERFACE m_axi port=mem offset=slave bundle=gmem depth=max_mem_words
#pragma HLS INTERFACE ap_ctrl_hs port=return

    HistCmd cmd;
    streamutils::tlast_status cmd_tlast = streamutils::tlast_status::no_tlast;
    cmd.read_axi4_stream<stream_dwidth>(in_stream, cmd_tlast);

    HistResp resp;
    resp.tx_id = cmd.tx_id;
    resp.status = HistError::NO_ERROR;

    static float data_buf[max_ndata];
    static float edge_buf[(max_nbins > 1) ? (max_nbins - 1) : 1];
    static ap_uint<32> count_buf[max_nbins];

    const int ndata = static_cast<int>(cmd.ndata);
    const int nbins = static_cast<int>(cmd.nbins);

    if (ndata <= 0 || ndata > max_ndata) {
        resp.status = HistError::INVALID_NDATA;
        resp.write_axi4_stream<stream_dwidth>(out_stream, true);
        return;
    }

    if (nbins <= 0 || nbins > max_nbins) {
        resp.status = HistError::INVALID_NBINS;
        resp.write_axi4_stream<stream_dwidth>(out_stream, true);
        return;
    }

    if (!memmgr::is_word_aligned<mem_dwidth>(cmd.data_addr) ||
        !memmgr::is_word_aligned<mem_dwidth>(cmd.bin_edges_addr) ||
        !memmgr::is_word_aligned<mem_dwidth>(cmd.cnt_addr)) {
        resp.status = HistError::ADDRESS_ERROR;
        resp.write_axi4_stream<stream_dwidth>(out_stream, true);
        return;
    }

    const int data_word_idx = memmgr::byte_addr_to_word_index<mem_dwidth>(cmd.data_addr);
    const int edge_word_idx = memmgr::byte_addr_to_word_index<mem_dwidth>(cmd.bin_edges_addr);
    const int count_word_idx = memmgr::byte_addr_to_word_index<mem_dwidth>(cmd.cnt_addr);

    float32_array_utils::read_array<mem_dwidth>(mem + data_word_idx, data_buf, ndata);
    if (nbins > 1) {
        float32_array_utils::read_array<mem_dwidth>(mem + edge_word_idx, edge_buf, nbins - 1);
    }

    for (int i = 0; i < max_nbins; ++i) {
#pragma HLS PIPELINE II=1
        count_buf[i] = 0;
    }

    // For each sample, find the appropriate bin and increment the count.
    // Note that only the inner loop that searches for the correct bin is 
    // pipelined with II=1. 
    for (int i = 0; i < ndata; ++i) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=max_ndata

        float sample = data_buf[i];
        int bin = 0;

        hist_search:  for (int b = 0; b < nbins - 1; ++b) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=max_nbins
#pragma HLS PIPELINE II=1
            if (sample >= edge_buf[b]) 
                bin = b + 1;
        }

        count_buf[bin] = count_buf[bin] + 1;
    }

    uint32_array_utils::write_array<mem_dwidth>(count_buf, mem + count_word_idx, nbins);
    resp.write_axi4_stream<stream_dwidth>(out_stream, true);
}