#ifndef CONV2D_HPP
#define CONV2D_HPP

#include <ap_axi_sdata.h>
#include <ap_int.h>
#include <hls_stream.h>

#include "include/streamutils_hls.h"
#include "include/conv2d_cmd.h"
#include "include/conv2d_resp.h"
#include "include/conv2d_event.h"
#include "include/conv2d_debug.h"
#include "include/int8_array_utils.h"
#include "include/memmgr.hpp"
#include "include/uint8_array_utils.h"

static const int max_nrow = 512;
static const int max_ncol = 512;
static const int max_kernel_size = 4;
static const int max_bank_rows = (max_nrow + max_kernel_size - 1) / max_kernel_size;

static const int pixel_bitwidth = 8;
static const int kernel_bitwidth = 8;
static const int kernel_fbits = 7;

static const int stream_dwidth = 32;
static const int mem_dwidth = 32;
static const int mem_awidth = 64;

static const int max_image_words = (max_nrow * max_ncol * pixel_bitwidth + mem_dwidth - 1) / mem_dwidth;
static const int max_kernel_words = (max_kernel_size * max_kernel_size * kernel_bitwidth + mem_dwidth - 1) / mem_dwidth;
static const int max_mem_words = max_image_words * 2 + max_kernel_words;

static_assert(stream_dwidth == 32 || stream_dwidth == 64, "stream_dwidth must be 32 or 64");
static_assert(mem_dwidth == 32 || mem_dwidth == 64, "mem_dwidth must be 32 or 64");

using axis_word_t = streamutils::axi4s_word<stream_dwidth>;
using mem_word_t = ap_uint<mem_dwidth>;

void conv2d(
	hls::stream<axis_word_t>& in_stream,
	hls::stream<axis_word_t>& out_stream,
	hls::stream<axis_word_t>& debug_stream,
	mem_word_t* mem,
	ap_uint<32>& row_ind
);

#endif  // CONV2D_HPP