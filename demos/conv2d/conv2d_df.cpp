#include "conv2d_df.hpp"

namespace memmgr = pysilicon::memmgr;

using pixel_t = uint8_array_utils::value_type;
using kernel_t = int8_array_utils::value_type;
using accum_t = ap_int<24>;
using df_bank_t = int;

static const int df_ping_pong_banks = 2;
static const int df_line_buf_rows = max_kernel_size + 1;


static void write_debug_event(
	hls::stream<axis_word_t>& debug_stream,
	ap_uint<32> row_ind,
	Conv2DEvent event,
	bool tlast = true
) {
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


#ifndef AESL_SYN
struct df_input_row_sw_t {
	pixel_t pixels[max_ncol];
};


struct df_output_row_sw_t {
	pixel_t pixels[max_ncol];
};


static void load_rows_df_csim(
	mem_word_t* mem,
	int input_word_idx,
	int row_word_count,
	int nrows,
	int ncols,
	int kernel_tail,
	hls::stream<df_input_row_sw_t>& row_stream,
	hls::stream<Conv2DDebug>& debug_stream
) {
	int input_row_mem_idx = input_word_idx;

	load_rows_csim:
	for (int load_step = 0; load_step < nrows + kernel_tail; ++load_step) {
		df_input_row_sw_t row_packet;

		Conv2DDebug debug_start;
		debug_start.row_ind = static_cast<ap_uint<32>>(load_step);
		debug_start.event = Conv2DEvent::LOAD_START;
		debug_stream.write(debug_start);

		if (load_step < nrows) {
			uint8_array_utils::read_array<mem_dwidth>(mem + input_row_mem_idx, row_packet.pixels, ncols);
			input_row_mem_idx += row_word_count;
		}
		else {
			clear_bottom_padding_row_csim:
			for (int col = 0; col < ncols; ++col) {
				row_packet.pixels[col] = 0;
			}
		}

		row_stream.write(row_packet);

		Conv2DDebug debug_end;
		debug_end.row_ind = static_cast<ap_uint<32>>(load_step);
		debug_end.event = Conv2DEvent::LOAD_END;
		debug_stream.write(debug_end);
	}
}


static void compute_rows_df_csim(
	hls::stream<df_input_row_sw_t>& row_stream,
	const kernel_t kernel_buf[max_kernel_size][max_kernel_size],
	int nrows,
	int ncols,
	int kernel_size,
	hls::stream<df_output_row_sw_t>& out_stream,
	hls::stream<Conv2DDebug>& debug_stream
) {
	const int kernel_anchor = (kernel_size - 1) / 2;
	const int kernel_tail = kernel_size - kernel_anchor - 1;

	static pixel_t line_buf_in[df_line_buf_rows][max_ncol];
	pixel_t window_buf[max_kernel_size][max_kernel_size];

	for (int bank = 0; bank < df_line_buf_rows; ++bank) {
		for (int col = 0; col < max_ncol; ++col) {
			line_buf_in[bank][col] = 0;
		}
	}

	int wp = 0;

	compute_rows_csim:
	for (int load_step = 0; load_step < nrows + kernel_tail; ++load_step) {
		df_input_row_sw_t in_row = row_stream.read();

		copy_loaded_row_csim:
		for (int col = 0; col < ncols; ++col) {
			line_buf_in[wp][col] = in_row.pixels[col];
		}

		wp += 1;
		if (wp == df_line_buf_rows) {
			wp = 0;
		}

		if (load_step < kernel_tail) {
			continue;
		}

		const int out_row = load_step - kernel_tail;
		const int start_bank = (wp + df_line_buf_rows - kernel_size) % df_line_buf_rows;

		Conv2DDebug debug_start;
		debug_start.row_ind = static_cast<ap_uint<32>>(out_row);
		debug_start.event = Conv2DEvent::COMPUTE_START;
		debug_stream.write(debug_start);

		for (int kr = 0; kr < max_kernel_size; ++kr) {
			int bank = start_bank + kr;
			if (bank >= df_line_buf_rows) {
				bank -= df_line_buf_rows;
			}

			for (int kc = 0; kc < max_kernel_size; ++kc) {
				pixel_t pixel = 0;
				if (kr < kernel_size && kc < kernel_size) {
					const int in_col = kc - kernel_anchor;
					if (in_col >= 0 && in_col < ncols) {
						pixel = line_buf_in[bank][in_col];
					}
				}
				window_buf[kr][kc] = pixel;
			}
		}

		df_output_row_sw_t out_row_packet;
		for (int oc = 0; oc < ncols; ++oc) {
			const accum_t acc = systolic_mac(window_buf, kernel_buf, kernel_size);
			out_row_packet.pixels[oc] = saturate_output(acc);

			const int next_col = oc + kernel_tail + 1;
			const bool insert_pix = (next_col >= 0) && (next_col < ncols);

			for (int kr = 0; kr < max_kernel_size; ++kr) {
				int bank = start_bank + kr;
				if (bank >= df_line_buf_rows) {
					bank -= df_line_buf_rows;
				}

				pixel_t next_pixel = 0;
				if (kr < kernel_size && insert_pix) {
					next_pixel = line_buf_in[bank][next_col];
				}

				for (int kc = 0; kc < max_kernel_size; ++kc) {
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
			}
		}

		out_stream.write(out_row_packet);

		Conv2DDebug debug_end;
		debug_end.row_ind = static_cast<ap_uint<32>>(out_row);
		debug_end.event = Conv2DEvent::COMPUTE_END;
		debug_stream.write(debug_end);
	}
}


static void store_rows_df_csim(
	hls::stream<df_output_row_sw_t>& in_stream,
	mem_word_t* mem,
	int output_word_idx,
	int row_word_count,
	int nrows,
	int ncols,
	ap_uint<32>& row_ind,
	hls::stream<Conv2DDebug>& debug_stream,
	hls::stream<bool>& ctrl_stream
) {
	int output_row_mem_idx = output_word_idx;

	for (int out_row = 0; out_row < nrows; ++out_row) {
		df_output_row_sw_t current_row = in_stream.read();

		row_ind = static_cast<ap_uint<32>>(out_row);
		Conv2DDebug debug_start;
		debug_start.row_ind = static_cast<ap_uint<32>>(out_row);
		debug_start.event = Conv2DEvent::STORE_START;
		debug_stream.write(debug_start);

		uint8_array_utils::write_array<mem_dwidth>(current_row.pixels, mem + output_row_mem_idx, ncols);
		output_row_mem_idx += row_word_count;

		Conv2DDebug debug_end;
		debug_end.row_ind = static_cast<ap_uint<32>>(out_row);
		debug_end.event = Conv2DEvent::STORE_END;
		debug_stream.write(debug_end);
	}

	ctrl_stream.write(true);
}
#endif


static void load_rows_df(
	mem_word_t* mem,
	int input_word_idx,
	int row_word_count,
	int nrows,
	int ncols,
	int kernel_tail,
	pixel_t row_buffers[df_ping_pong_banks][max_ncol],
	hls::stream<df_bank_t>& recycled_bank_stream,
	hls::stream<df_bank_t>& ready_bank_stream,
	hls::stream<Conv2DDebug>& debug_stream
) {
	int input_row_mem_idx = input_word_idx;

	load_rows:
	for (int load_step = 0; load_step < nrows + kernel_tail; ++load_step) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=max_nrow + max_kernel_size
		const int bank =
			(load_step < df_ping_pong_banks)
				? load_step
				: recycled_bank_stream.read();

		Conv2DDebug debug_start;
		debug_start.row_ind = static_cast<ap_uint<32>>(load_step);
		debug_start.event = Conv2DEvent::LOAD_START;
		debug_stream.write(debug_start);

		if (load_step < nrows) {
			uint8_array_utils::read_array<mem_dwidth>(mem + input_row_mem_idx, row_buffers[bank], ncols);
			input_row_mem_idx += row_word_count;
		}
		else {
			clear_bottom_padding_row:
			for (int col = 0; col < ncols; ++col) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=max_ncol
#pragma HLS PIPELINE II=1
				row_buffers[bank][col] = 0;
			}
		}

		ready_bank_stream.write(bank);

		Conv2DDebug debug_end;
		debug_end.row_ind = static_cast<ap_uint<32>>(load_step);
		debug_end.event = Conv2DEvent::LOAD_END;
		debug_stream.write(debug_end);
	}
}


static void compute_rows_df(
	pixel_t load_buffers[df_ping_pong_banks][max_ncol],
	hls::stream<df_bank_t>& load_ready_bank_stream,
	hls::stream<df_bank_t>& load_recycled_bank_stream,
	const kernel_t kernel_buf[max_kernel_size][max_kernel_size],
	int nrows,
	int ncols,
	int kernel_size,
	pixel_t store_buffers[df_ping_pong_banks][max_ncol],
	hls::stream<df_bank_t>& store_recycled_bank_stream,
	hls::stream<df_bank_t>& store_ready_bank_stream,
	hls::stream<Conv2DDebug>& debug_stream
) {
	const int kernel_anchor = (kernel_size - 1) / 2;
	const int kernel_tail = kernel_size - kernel_anchor - 1;

	static pixel_t line_buf_in[df_line_buf_rows][max_ncol];
	pixel_t window_buf[max_kernel_size][max_kernel_size];
#pragma HLS ARRAY_PARTITION variable=line_buf_in complete dim=1
#pragma HLS ARRAY_PARTITION variable=window_buf complete dim=1
#pragma HLS ARRAY_PARTITION variable=window_buf complete dim=2

	init_line_buf:
	for (int bank = 0; bank < df_line_buf_rows; ++bank) {
#pragma HLS UNROLL
		for (int col = 0; col < max_ncol; ++col) {
#pragma HLS PIPELINE II=1
			line_buf_in[bank][col] = 0;
		}
	}

	int wp = 0;

	compute_rows:
	for (int load_step = 0; load_step < nrows + kernel_tail; ++load_step) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=max_nrow + max_kernel_size
		const df_bank_t load_bank = load_ready_bank_stream.read();

		copy_loaded_row:
		for (int col = 0; col < ncols; ++col) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=max_ncol
#pragma HLS PIPELINE II=1
			line_buf_in[wp][col] = load_buffers[load_bank][col];
		}
		load_recycled_bank_stream.write(load_bank);

		wp += 1;
		if (wp == df_line_buf_rows) {
			wp = 0;
		}

		if (load_step < kernel_tail) {
			continue;
		}

		const int out_row = load_step - kernel_tail;
		const int start_bank = (wp + df_line_buf_rows - kernel_size) % df_line_buf_rows;

		Conv2DDebug debug_start;
		debug_start.row_ind = static_cast<ap_uint<32>>(out_row);
		debug_start.event = Conv2DEvent::COMPUTE_START;
		debug_stream.write(debug_start);

		init_window:
		for (int kr = 0; kr < max_kernel_size; ++kr) {
#pragma HLS UNROLL
			int bank = start_bank + kr;
			if (bank >= df_line_buf_rows) {
				bank -= df_line_buf_rows;
			}

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
		}

		const int store_bank =
			(out_row < df_ping_pong_banks)
				? out_row
				: store_recycled_bank_stream.read();

		convolve_row:
		for (int oc = 0; oc < ncols; ++oc) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=max_ncol
#pragma HLS PIPELINE II=1
			const accum_t acc = systolic_mac(window_buf, kernel_buf, kernel_size);
			store_buffers[store_bank][oc] = saturate_output(acc);

			const int next_col = oc + kernel_tail + 1;
			const bool insert_pix = (next_col >= 0) && (next_col < ncols);

			advance_window_rows:
			for (int kr = 0; kr < max_kernel_size; ++kr) {
#pragma HLS UNROLL
				int bank = start_bank + kr;
				if (bank >= df_line_buf_rows) {
					bank -= df_line_buf_rows;
				}

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
			}
		}

		store_ready_bank_stream.write(store_bank);

		Conv2DDebug debug_end;
		debug_end.row_ind = static_cast<ap_uint<32>>(out_row);
		debug_end.event = Conv2DEvent::COMPUTE_END;
		debug_stream.write(debug_end);
	}
}


static void store_rows_df(
	pixel_t store_buffers[df_ping_pong_banks][max_ncol],
	hls::stream<df_bank_t>& ready_bank_stream,
	hls::stream<df_bank_t>& recycled_bank_stream,
	mem_word_t* mem,
	int output_word_idx,
	int row_word_count,
	int nrows,
	int ncols,
	ap_uint<32>& row_ind,
	hls::stream<Conv2DDebug>& debug_stream,
	hls::stream<bool>& ctrl_stream
) {
	int output_row_mem_idx = output_word_idx;

	if (nrows <= 0) {
		return;
	}

	store_rows:
	for (int out_row = 0; out_row < nrows; ++out_row) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=max_nrow
		const int store_bank = ready_bank_stream.read();

		row_ind = static_cast<ap_uint<32>>(out_row);
		Conv2DDebug debug_start;
		debug_start.row_ind = static_cast<ap_uint<32>>(out_row);
		debug_start.event = Conv2DEvent::STORE_START;
		debug_stream.write(debug_start);

		uint8_array_utils::write_array<mem_dwidth>(store_buffers[store_bank], mem + output_row_mem_idx, ncols);
		output_row_mem_idx += row_word_count;

		Conv2DDebug debug_end;
		debug_end.row_ind = static_cast<ap_uint<32>>(out_row);
		debug_end.event = Conv2DEvent::STORE_END;
		debug_stream.write(debug_end);
		if (out_row + 1 == nrows) {
			ctrl_stream.write(true);
		}

		recycled_bank_stream.write(store_bank);
	}
}


static void merge_debug_events_df(
	hls::stream<Conv2DDebug>& load_debug_stream,
	hls::stream<Conv2DDebug>& compute_debug_stream,
	hls::stream<Conv2DDebug>& store_debug_stream,
	hls::stream<bool>& ctrl_stream,
	hls::stream<axis_word_t>& debug_stream
) {
	bool done_seen = false;

	merge_debug:
	while (true) {
#pragma HLS PIPELINE II=1
		Conv2DDebug debug_event;
		bool emitted = false;
		bool ctrl_done = false;

		ctrl_stream.read_nb(ctrl_done);
		done_seen = done_seen || ctrl_done;

		if (load_debug_stream.read_nb(debug_event)) {
			emitted = true;
		}
		else if (compute_debug_stream.read_nb(debug_event)) {
			emitted = true;
		}
		else if (store_debug_stream.read_nb(debug_event)) {
			emitted = true;
		}

		if (emitted) {
			write_debug_event(debug_stream, debug_event.row_ind, debug_event.event, true);
		}

		if (done_seen && !emitted && load_debug_stream.empty() && compute_debug_stream.empty() && store_debug_stream.empty()) {
			break;
		}
	}
}


static void run_conv2d_df_dataflow(
	mem_word_t* mem,
	int input_word_idx,
	int output_word_idx,
	int row_word_count,
	int nrows,
	int ncols,
	int kernel_size,
	int kernel_tail,
	const kernel_t kernel_buf[max_kernel_size][max_kernel_size],
	pixel_t load_to_compute[df_ping_pong_banks][max_ncol],
	pixel_t compute_to_store[df_ping_pong_banks][max_ncol],
	ap_uint<32>& store_row_ind,
	hls::stream<axis_word_t>& debug_stream
) {
	hls::stream<df_bank_t> load_recycled_bank_stream("load_recycled_bank_stream");
	hls::stream<df_bank_t> load_ready_bank_stream("load_ready_bank_stream");
	hls::stream<df_bank_t> store_recycled_bank_stream("store_recycled_bank_stream");
	hls::stream<df_bank_t> store_ready_bank_stream("store_ready_bank_stream");
	hls::stream<Conv2DDebug> load_debug_stream("load_debug_stream");
	hls::stream<Conv2DDebug> compute_debug_stream("compute_debug_stream");
	hls::stream<Conv2DDebug> store_debug_stream("store_debug_stream");
	hls::stream<bool> debug_ctrl_stream("debug_ctrl_stream");
#pragma HLS STREAM variable=load_recycled_bank_stream depth=2
#pragma HLS STREAM variable=load_ready_bank_stream depth=2
#pragma HLS STREAM variable=store_recycled_bank_stream depth=2
#pragma HLS STREAM variable=store_ready_bank_stream depth=2
#pragma HLS STREAM variable=load_debug_stream depth=8
#pragma HLS STREAM variable=compute_debug_stream depth=8
#pragma HLS STREAM variable=store_debug_stream depth=8
#pragma HLS STREAM variable=debug_ctrl_stream depth=2

#pragma HLS DATAFLOW
	load_rows_df(
		mem,
		input_word_idx,
		row_word_count,
		nrows,
		ncols,
		kernel_tail,
		load_to_compute,
		load_recycled_bank_stream,
		load_ready_bank_stream,
		load_debug_stream
	);
	compute_rows_df(
		load_to_compute,
		load_ready_bank_stream,
		load_recycled_bank_stream,
		kernel_buf,
		nrows,
		ncols,
		kernel_size,
		compute_to_store,
		store_recycled_bank_stream,
		store_ready_bank_stream,
		compute_debug_stream
	);
	store_rows_df(
		compute_to_store,
		store_ready_bank_stream,
		store_recycled_bank_stream,
		mem,
		output_word_idx,
		row_word_count,
		nrows,
		ncols,
		store_row_ind,
		store_debug_stream,
		debug_ctrl_stream
	);
	merge_debug_events_df(
		load_debug_stream,
		compute_debug_stream,
		store_debug_stream,
		debug_ctrl_stream,
		debug_stream
	);
}


static void conv2d_df_impl(
	hls::stream<axis_word_t>& in_stream,
	hls::stream<axis_word_t>& out_stream,
	hls::stream<axis_word_t>& debug_stream,
	mem_word_t* mem,
	ap_uint<32>& row_ind
) {
	Conv2DCmd cmd;
	streamutils::tlast_status cmd_tlast = streamutils::tlast_status::no_tlast;
	cmd.read_axi4_stream<stream_dwidth>(in_stream, cmd_tlast);

	Conv2DResp resp;
	resp.error_code = Conv2DError::NO_ERROR;

	ap_uint<32> final_row_ind = 0;
	write_debug_event(debug_stream, final_row_ind, Conv2DEvent::MAIN_START, true);

	static kernel_t kernel_linear_buf[max_kernel_size * max_kernel_size];
	static kernel_t kernel_buf[max_kernel_size][max_kernel_size];
	static pixel_t load_to_compute[df_ping_pong_banks][max_ncol];
	static pixel_t compute_to_store[df_ping_pong_banks][max_ncol];
	ap_uint<32> store_row_ind = 0;
#pragma HLS ARRAY_PARTITION variable=kernel_buf complete dim=1
#pragma HLS ARRAY_PARTITION variable=kernel_buf complete dim=2
#pragma HLS ARRAY_PARTITION variable=load_to_compute complete dim=1
#pragma HLS ARRAY_PARTITION variable=compute_to_store complete dim=1
#pragma HLS BIND_STORAGE variable=load_to_compute type=ram_2p impl=bram
#pragma HLS BIND_STORAGE variable=compute_to_store type=ram_2p impl=bram

	const int nrows = static_cast<int>(cmd.nrows);
	const int ncols = static_cast<int>(cmd.ncols);
	const int kernel_size = static_cast<int>(cmd.kernel_size);
	int kernel_elems = 0;
	switch (kernel_size) {
	case 1:
		kernel_elems = 1;
		break;
	case 2:
		kernel_elems = 4;
		break;
	case 3:
		kernel_elems = 9;
		break;
	default:
		kernel_elems = 16;
		break;
	}
	const int kernel_anchor = (kernel_size - 1) / 2;
	const int kernel_tail = kernel_size - kernel_anchor - 1;

	if (nrows <= 0 || nrows > max_nrow) {
		resp.error_code = Conv2DError::INVALID_NROWS;
		row_ind = final_row_ind;
		write_debug_event(debug_stream, final_row_ind, Conv2DEvent::MAIN_END, true);
		resp.write_axi4_stream<stream_dwidth>(out_stream, true);
		return;
	}

	if (ncols <= 0 || ncols > max_ncol) {
		resp.error_code = Conv2DError::INVALID_NCOLS;
		row_ind = final_row_ind;
		write_debug_event(debug_stream, final_row_ind, Conv2DEvent::MAIN_END, true);
		resp.write_axi4_stream<stream_dwidth>(out_stream, true);
		return;
	}

	if (kernel_size <= 0 || kernel_size > max_kernel_size) {
		resp.error_code = Conv2DError::INVALID_KSIZE;
		row_ind = final_row_ind;
		write_debug_event(debug_stream, final_row_ind, Conv2DEvent::MAIN_END, true);
		resp.write_axi4_stream<stream_dwidth>(out_stream, true);
		return;
	}

	if (!memmgr::is_word_aligned<mem_dwidth>(cmd.input_addr) ||
		!memmgr::is_word_aligned<mem_dwidth>(cmd.output_addr) ||
		!memmgr::is_word_aligned<mem_dwidth>(cmd.kernel_addr)) {
		resp.error_code = Conv2DError::ADDRESS_ERROR;
		row_ind = final_row_ind;
		write_debug_event(debug_stream, final_row_ind, Conv2DEvent::MAIN_END, true);
		resp.write_axi4_stream<stream_dwidth>(out_stream, true);
		return;
	}

	const int input_word_idx = memmgr::byte_addr_to_word_index<mem_dwidth>(cmd.input_addr);
	const int output_word_idx = memmgr::byte_addr_to_word_index<mem_dwidth>(cmd.output_addr);
	const int kernel_word_idx = memmgr::byte_addr_to_word_index<mem_dwidth>(cmd.kernel_addr);
	const int row_word_count = uint8_array_utils::get_nwords<mem_dwidth>(ncols);

	int8_array_utils::read_array<mem_dwidth>(mem + kernel_word_idx, kernel_linear_buf, kernel_elems);
	int kernel_linear_idx = 0;
	for (int kr = 0; kr < max_kernel_size; ++kr) {
#pragma HLS UNROLL
		int kernel_idx = kernel_linear_idx;
		for (int kc = 0; kc < max_kernel_size; ++kc) {
#pragma HLS UNROLL
			if (kr < kernel_size && kc < kernel_size) {
				kernel_buf[kr][kc] = kernel_linear_buf[kernel_idx];
				++kernel_idx;
			}
			else {
				kernel_buf[kr][kc] = 0;
			}
		}
		if (kr < kernel_size) {
			kernel_linear_idx = kernel_idx;
		}
	}

	#ifndef AESL_SYN
	hls::stream<df_input_row_sw_t> load_to_compute_stream("load_to_compute_stream");
	hls::stream<df_output_row_sw_t> compute_to_store_stream("compute_to_store_stream");
	hls::stream<Conv2DDebug> load_debug_stream("load_debug_stream");
	hls::stream<Conv2DDebug> compute_debug_stream("compute_debug_stream");
	hls::stream<Conv2DDebug> store_debug_stream("store_debug_stream");
	hls::stream<bool> debug_ctrl_stream("debug_ctrl_stream");

	load_rows_df_csim(
		mem,
		input_word_idx,
		row_word_count,
		nrows,
		ncols,
		kernel_tail,
		load_to_compute_stream,
		load_debug_stream
	);
	compute_rows_df_csim(
		load_to_compute_stream,
		kernel_buf,
		nrows,
		ncols,
		kernel_size,
		compute_to_store_stream,
		compute_debug_stream
	);
	store_rows_df_csim(
		compute_to_store_stream,
		mem,
		output_word_idx,
		row_word_count,
		nrows,
		ncols,
		final_row_ind,
		store_debug_stream,
		debug_ctrl_stream
	);
	merge_debug_events_df(
		load_debug_stream,
		compute_debug_stream,
		store_debug_stream,
		debug_ctrl_stream,
		debug_stream
	);

	row_ind = final_row_ind;
	write_debug_event(debug_stream, final_row_ind, Conv2DEvent::MAIN_END, true);
	resp.write_axi4_stream<stream_dwidth>(out_stream, true);
	return;
	#else
	run_conv2d_df_dataflow(
		mem,
		input_word_idx,
		output_word_idx,
		row_word_count,
		nrows,
		ncols,
		kernel_size,
		kernel_tail,
		kernel_buf,
		load_to_compute,
		compute_to_store,
		store_row_ind,
		debug_stream
	);

	final_row_ind = store_row_ind;
	row_ind = final_row_ind;
	write_debug_event(debug_stream, final_row_ind, Conv2DEvent::MAIN_END, true);
	resp.write_axi4_stream<stream_dwidth>(out_stream, true);
	#endif
}


void conv2d_df(
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

	ap_uint<32> final_row_ind = 0;
	conv2d_df_impl(in_stream, out_stream, debug_stream, mem, final_row_ind);
	row_ind = final_row_ind;
}