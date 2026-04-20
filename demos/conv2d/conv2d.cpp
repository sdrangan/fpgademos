#include "conv2d.hpp"

namespace memmgr = pysilicon::memmgr;

using pixel_t = uint8_array_utils::value_type;
using kernel_t = int8_array_utils::value_type;
using accum_t = ap_int<24>;


static void write_debug_event(
	hls::stream<axis_word_t>& debug_stream,
	ap_uint<32> row_ind,
	Conv2DEvent event,
	bool tlast = true
) {
#pragma HLS INLINE
	Conv2DDebug debug;
	debug.row_ind = static_cast<decltype(debug.row_ind)>(row_ind);
	debug.event = event;
	debug.write_axi4_stream<stream_dwidth>(debug_stream, tlast);
}


static pixel_t saturate_output(accum_t acc) {
#pragma HLS INLINE
	const accum_t shifted = acc >> kernel_fbits;
	if (shifted <= 0) {
		return 0;
	}

	const accum_t pixel_max = (1 << pixel_bitwidth) - 1;
	if (shifted >= pixel_max) {
		return static_cast<pixel_t>(pixel_max);
	}

	return static_cast<pixel_t>(shifted);
}


static accum_t systolic_mac(
	const pixel_t window_buf[max_kernel_size][max_kernel_size],
	const kernel_t kernel_buf[max_kernel_size][max_kernel_size],
	int kernel_size
) {
#pragma HLS INLINE
	accum_t row_sum[max_kernel_size];
#pragma HLS ARRAY_PARTITION variable=row_sum complete dim=1

	for (int kr = 0; kr < max_kernel_size; ++kr) {
#pragma HLS UNROLL
		accum_t acc_row = 0;
		for (int kc = 0; kc < max_kernel_size; ++kc) {
#pragma HLS UNROLL
			accum_t product = 0;
			if (kr < kernel_size && kc < kernel_size) {
				product = static_cast<accum_t>(window_buf[kr][kc]) * static_cast<accum_t>(kernel_buf[kr][kc]);
			}
			acc_row += product;
		}
		row_sum[kr] = acc_row;
	}

	accum_t total = 0;
	for (int kr = 0; kr < max_kernel_size; ++kr) {
#pragma HLS UNROLL
		total += row_sum[kr];
	}

	return total;
}


void conv2d(
	hls::stream<axis_word_t>& in_stream,
	hls::stream<axis_word_t>& out_stream,
	hls::stream<axis_word_t>& debug_stream,
	mem_word_t* mem,
	ap_uint<32>& row_ind
) {
#pragma HLS INTERFACE axis port=in_stream
#pragma HLS INTERFACE axis port=out_stream
#pragma HLS INTERFACE axis port=debug_stream
#pragma HLS INTERFACE m_axi port=mem offset=slave bundle=gmem depth=max_mem_words
#pragma HLS INTERFACE ap_none port=row_ind
#pragma HLS INTERFACE ap_ctrl_hs port=return

	Conv2DCmd cmd;
	streamutils::tlast_status cmd_tlast = streamutils::tlast_status::no_tlast;
	cmd.read_axi4_stream<stream_dwidth>(in_stream, cmd_tlast);

	Conv2DResp resp;
	resp.error_code = Conv2DError::NO_ERROR;

	row_ind = 0;
	write_debug_event(debug_stream, row_ind, Conv2DEvent::MAIN_START);

	// Buffer for the last max_kernel_size rows of the input image.
	static pixel_t line_buf_in[max_kernel_size][max_ncol];
#pragma HLS ARRAY_PARTITION variable=line_buf_in complete dim=1

	// Buffer for the programmed kernel. This is fully partitioned so the MAC
	// array can consume every coefficient in parallel.
	static kernel_t kernel_linear_buf[max_kernel_size * max_kernel_size];
	static kernel_t kernel_buf[max_kernel_size][max_kernel_size];
#pragma HLS ARRAY_PARTITION variable=kernel_buf complete dim=1
#pragma HLS ARRAY_PARTITION variable=kernel_buf complete dim=2

	// Output buffer for one row of the output image.
	static pixel_t line_buf_out[max_ncol];

	// Get dimensions and validate parameters.
    // If there is an error, set the error code in the response, 
    // write the response to the output stream, and return immediately.
	const int nrows = static_cast<int>(cmd.nrows);
	const int ncols = static_cast<int>(cmd.ncols);
	const int kernel_size = static_cast<int>(cmd.kernel_size);
	const int kernel_elems = kernel_size * kernel_size;
	const int kernel_anchor = (kernel_size - 1) / 2;
	const int kernel_tail = kernel_size - kernel_anchor - 1;

	if (nrows <= 0 || nrows > max_nrow) {
		resp.error_code = Conv2DError::INVALID_NROWS;
		write_debug_event(debug_stream, row_ind, Conv2DEvent::MAIN_END, true);
		resp.write_axi4_stream<stream_dwidth>(out_stream, true);
		return;
	}

	if (ncols <= 0 || ncols > max_ncol) {
		resp.error_code = Conv2DError::INVALID_NCOLS;
		write_debug_event(debug_stream, row_ind, Conv2DEvent::MAIN_END, true);
		resp.write_axi4_stream<stream_dwidth>(out_stream, true);
		return;
	}

	if (kernel_size <= 0 || kernel_size > max_kernel_size) {
		resp.error_code = Conv2DError::INVALID_KSIZE;
		write_debug_event(debug_stream, row_ind, Conv2DEvent::MAIN_END, true);
		resp.write_axi4_stream<stream_dwidth>(out_stream, true);
		return;
	}

	if (!memmgr::is_word_aligned<mem_dwidth>(cmd.input_addr) ||
		!memmgr::is_word_aligned<mem_dwidth>(cmd.output_addr) ||
		!memmgr::is_word_aligned<mem_dwidth>(cmd.kernel_addr)) {
		resp.error_code = Conv2DError::ADDRESS_ERROR;
		write_debug_event(debug_stream, row_ind, Conv2DEvent::MAIN_END, true);
		resp.write_axi4_stream<stream_dwidth>(out_stream, true);
		return;
	}

    // Get address in memory
	const int input_word_idx = memmgr::byte_addr_to_word_index<mem_dwidth>(cmd.input_addr);
	const int output_word_idx = memmgr::byte_addr_to_word_index<mem_dwidth>(cmd.output_addr);
	const int kernel_word_idx = memmgr::byte_addr_to_word_index<mem_dwidth>(cmd.kernel_addr);
	const int row_word_count = uint8_array_utils::get_nwords<mem_dwidth>(ncols);

	// Read the packed kernel into a dense linear buffer first, then reshape it
	// into the padded 2D kernel buffer. This avoids stride and packing issues
	// when kernel_size is smaller than max_kernel_size.
	write_debug_event(debug_stream, row_ind, Conv2DEvent::LOAD_START);
	int8_array_utils::read_array<mem_dwidth>(mem + kernel_word_idx, kernel_linear_buf, kernel_elems);
	for (int kr = 0; kr < max_kernel_size; ++kr) {
#pragma HLS UNROLL
		for (int kc = 0; kc < max_kernel_size; ++kc) {
#pragma HLS UNROLL
			if (kr < kernel_size && kc < kernel_size) {
				kernel_buf[kr][kc] = kernel_linear_buf[kr * kernel_size + kc];
			}
			else {
				kernel_buf[kr][kc] = 0;
			}
		}
	}
	write_debug_event(debug_stream, row_ind, Conv2DEvent::LOAD_END);

	// Initialize the line buffer to zeros so the top padding naturally appears
	// before enough image rows have been loaded.
	for (int ic = 0; ic < max_ncol; ++ic) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=max_ncol
#pragma HLS PIPELINE II=1
		for (int bank = 0; bank < max_kernel_size; ++bank) {
#pragma HLS UNROLL
			line_buf_in[bank][ic] = 0;
        }
    }

	int wp = 0;
	int input_row_mem_idx = input_word_idx;
	int output_row_mem_idx = output_word_idx;

    // Main loop over the rows of the input image.
	load_and_convolve:
	for (int load_step = 0; load_step < nrows + kernel_tail; ++load_step) {

        // Load a row of the input image into the line buffer, 
        // unless we've already loaded all the rows of the image (load_step < nrows).
        // If we've loaded all the rows of the image, we need to insert 
        // zero rows into the line buffer to account for the bottom padding.
#pragma HLS LOOP_TRIPCOUNT min=1 max=max_nrow + max_kernel_size
		write_debug_event(debug_stream, static_cast<ap_uint<32>>(load_step), Conv2DEvent::LOAD_START);
		if (load_step < nrows) {
			uint8_array_utils::read_array<mem_dwidth>(mem + input_row_mem_idx, line_buf_in[wp], ncols);
			input_row_mem_idx += row_word_count;
		}
		else {
			clear_bottom_padding_row:
			for (int col = 0; col < ncols; ++col) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=max_ncol
#pragma HLS PIPELINE II=1
				line_buf_in[wp][col] = 0;
			}
		}

		wp = (wp + 1) % max_kernel_size;
		write_debug_event(debug_stream, static_cast<ap_uint<32>>(load_step), Conv2DEvent::LOAD_END);

		if (load_step < kernel_tail) {
			continue;
		}

        // Initialize the window buffer for the first convolution
		pixel_t window_buf[max_kernel_size][max_kernel_size];
#pragma HLS ARRAY_PARTITION variable=window_buf complete dim=1
#pragma HLS ARRAY_PARTITION variable=window_buf complete dim=2

		const int start_bank = (wp + max_kernel_size - kernel_size) % max_kernel_size;
		const int bank0 = start_bank;
		int bank = bank0;

		init_window:
		for (int kr = 0; kr < max_kernel_size; ++kr) {
#pragma HLS UNROLL
			for (int kc = 0; kc < max_kernel_size; ++kc) {
#pragma HLS UNROLL
				pixel_t pixel = 0;
				if (kr < kernel_size && kc < kernel_size) {
					const int in_col = kc - kernel_anchor;
					if (in_col >= 0 && in_col < ncols) {
						pixel = line_buf_in[bank][in_col];
					}
				}
				window_buf[kr][kc] = pixel;
			}

			bank += 1;
			if (bank == max_kernel_size) {
				bank = 0;
			}
		}

        // Loop over the columns of the output image
		write_debug_event(debug_stream, static_cast<ap_uint<32>>(load_step), Conv2DEvent::COMPUTE_START);
		convolve_row:
		for (int oc = 0; oc < ncols; ++oc) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=max_ncol
#pragma HLS PIPELINE II=1
            // Run the systolic MAC on the current window and kernel
			const accum_t acc = systolic_mac(window_buf, kernel_buf, kernel_size);
			line_buf_out[oc] = saturate_output(acc);

            // Compute the next colunm to insert based on the kernel tail
			const int next_col = oc + kernel_tail + 1;
			const bool insert_pix = (next_col >= 0) && (next_col < ncols);
			int bank = bank0;

            // Shift the window and insert the next pixel
			advance_window_rows:
			for (int kr = 0; kr < max_kernel_size; ++kr) {
#pragma HLS UNROLL
					pixel_t next_pixel = 0;
					if (kr < kernel_size && insert_pix) {
						next_pixel = line_buf_in[bank][next_col];
					}

					advance_window_cols:
					for (int kc = 0; kc < max_kernel_size; ++kc) {
#pragma HLS UNROLL
						if (kc + 1 < kernel_size) {
							window_buf[kr][kc] = window_buf[kr][kc + 1];
						}
						else if (kc + 1 == kernel_size) {
							window_buf[kr][kc] = next_pixel;
						}
						else {
							window_buf[kr][kc] = 0;
						}
					}

					bank += 1;
					if (bank == max_kernel_size) {
						bank = 0;
					}
				}
		}
		write_debug_event(debug_stream, static_cast<ap_uint<32>>(load_step), Conv2DEvent::COMPUTE_END);

        // Update the row index for visibility in the testbench 
		row_ind = static_cast<ap_uint<32>>(load_step);
		write_debug_event(debug_stream, row_ind, Conv2DEvent::STORE_START);

        // Write the convolved row to memory
		uint8_array_utils::write_array<mem_dwidth>(line_buf_out, mem + output_row_mem_idx, ncols);
		output_row_mem_idx += row_word_count;
		write_debug_event(debug_stream, row_ind, Conv2DEvent::STORE_END);
	}

	write_debug_event(debug_stream, row_ind, Conv2DEvent::MAIN_END, true);
	resp.write_axi4_stream<stream_dwidth>(out_stream, true);
}
