#ifndef CONV2D_DF_HPP
#define CONV2D_DF_HPP

#include "conv2d.hpp"

void conv2d_df(
	hls::stream<axis_word_t>& in_stream,
	hls::stream<axis_word_t>& out_stream,
	hls::stream<axis_word_t>& debug_stream,
	mem_word_t* mem,
	ap_uint<32>& row_ind
);

#endif  // CONV2D_DF_HPP