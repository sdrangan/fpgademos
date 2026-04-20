#include <cstdint>
#include <fstream>
#include <iterator>
#include <stdexcept>
#include <string>

#ifdef PYSILICON_CONV2D_DF
#include "conv2d_df.hpp"
#else
#include "conv2d.hpp"
#endif
#include "include/conv2d_event_tb.h"
#include "include/int8_array_utils_tb.h"
#include "include/memmgr_tb.hpp"
#include "include/streamutils_tb.h"
#include "include/uint8_array_utils_tb.h"

static const int MEM_SIZE = max_mem_words;

#ifdef PYSILICON_CONV2D_DF
static void run_conv2d_kernel(
    hls::stream<axis_word_t>& in_stream,
    hls::stream<axis_word_t>& out_stream,
    hls::stream<axis_word_t>& debug_stream,
    mem_word_t* mem,
    ap_uint<32>& row_ind
) {
    conv2d_df(in_stream, out_stream, debug_stream, mem, row_ind);
}
#else
static void run_conv2d_kernel(
    hls::stream<axis_word_t>& in_stream,
    hls::stream<axis_word_t>& out_stream,
    hls::stream<axis_word_t>& debug_stream,
    mem_word_t* mem,
    ap_uint<32>& row_ind
) {
    conv2d(in_stream, out_stream, debug_stream, mem, row_ind);
}
#endif

int main(int argc, char** argv) {
    const std::string data_dir = (argc > 1) ? argv[1] : "data";

    int nrows = 0;
    int ncols = 0;
    int kernel_size = 0;
    {
        std::ifstream params_ifs(data_dir + "/params.json");
        if (!params_ifs) {
            throw std::runtime_error("Failed to open params.json for reading.");
        }

        const std::string params_json(
            (std::istreambuf_iterator<char>(params_ifs)),
            std::istreambuf_iterator<char>()
        );

        size_t pos = 0;
        streamutils::json_expect_char(params_json, pos, '{');
        while (true) {
            streamutils::json_skip_ws(params_json, pos);
            if (pos < params_json.size() && params_json[pos] == '}') {
                break;
            }

            const std::string key = streamutils::json_parse_string(params_json, pos);
            streamutils::json_expect_char(params_json, pos, ':');
            const int val = static_cast<int>(streamutils::json_parse_number(params_json, pos));

            if (key == "nrows") {
                nrows = val;
            }
            else if (key == "ncols") {
                ncols = val;
            }
            else if (key == "kernel_size") {
                kernel_size = val;
            }

            streamutils::json_skip_ws(params_json, pos);
            if (pos < params_json.size() && params_json[pos] == ',') {
                ++pos;
            }
        }
    }

    if (nrows <= 0 || nrows > max_nrow) {
        throw std::runtime_error("params.json contains an invalid nrows value.");
    }
    if (ncols <= 0 || ncols > max_ncol) {
        throw std::runtime_error("params.json contains an invalid ncols value.");
    }
    if (kernel_size <= 0 || kernel_size > max_kernel_size) {
        throw std::runtime_error("params.json contains an invalid kernel_size value.");
    }

    const int image_elems = nrows * ncols;
    const int kernel_elems = kernel_size * kernel_size;

    static uint8_array_utils::value_type image_buf[max_nrow * max_ncol] = {};
    static int8_array_utils::value_type kernel_buf[max_kernel_size * max_kernel_size] = {};
    uint8_array_utils::read_uint32_file_array(image_buf, (data_dir + "/im_in_array.bin").c_str(), image_elems);
    int8_array_utils::read_uint32_file_array(kernel_buf, (data_dir + "/kernel_array.bin").c_str(), kernel_elems);

    static mem_word_t mem[MEM_SIZE] = {};
    pysilicon::memmgr::MemMgr<mem_dwidth> mgr(mem, MEM_SIZE);

    const int nwords_image = uint8_array_utils::get_nwords<mem_dwidth>(image_elems);
    const int nwords_kernel = int8_array_utils::get_nwords<mem_dwidth>(kernel_elems);
    const int nwords_output = uint8_array_utils::get_nwords<mem_dwidth>(image_elems);

    const int input_word_idx = mgr.alloc(nwords_image);
    const int kernel_word_idx = mgr.alloc(nwords_kernel);
    const int output_word_idx = mgr.alloc(nwords_output);

    const int bytes_per_word = mem_dwidth / 8;
    const ap_uint<mem_awidth> input_byte_addr = input_word_idx * bytes_per_word;
    const ap_uint<mem_awidth> kernel_byte_addr = kernel_word_idx * bytes_per_word;
    const ap_uint<mem_awidth> output_byte_addr = output_word_idx * bytes_per_word;

    uint8_array_utils::write_array<mem_dwidth>(image_buf, mem + input_word_idx, image_elems);
    int8_array_utils::write_array<mem_dwidth>(kernel_buf, mem + kernel_word_idx, kernel_elems);

    Conv2DCmd cmd;
    cmd.nrows = nrows;
    cmd.ncols = ncols;
    cmd.kernel_size = kernel_size;
    cmd.input_addr = input_byte_addr;
    cmd.output_addr = output_byte_addr;
    cmd.kernel_addr = kernel_byte_addr;

    hls::stream<axis_word_t> in_stream;
    hls::stream<axis_word_t> out_stream;
    hls::stream<axis_word_t> debug_stream;
    ap_uint<32> row_ind = 0;
    cmd.write_axi4_stream<stream_dwidth>(in_stream, true);
    run_conv2d_kernel(in_stream, out_stream, debug_stream, mem, row_ind);

    Conv2DResp resp;
    streamutils::tlast_status resp_tlast = streamutils::tlast_status::no_tlast;
    resp.read_axi4_stream<stream_dwidth>(out_stream, resp_tlast);

    std::vector<Conv2DDebug> debug_events;
    std::vector<ap_uint<32>> debug_words;
    streamutils::tlast_status debug_tlast = streamutils::tlast_status::no_tlast;
    while (!debug_stream.empty()) {
        Conv2DDebug debug_event;
        debug_event.read_axi4_stream<stream_dwidth>(debug_stream, debug_tlast);
        if (debug_tlast != streamutils::tlast_status::tlast_at_end) {
            throw std::runtime_error("Debug stream event did not terminate with TLAST.");
        }

        ap_uint<32> debug_word = 0;
        debug_event.write_array<32>(&debug_word);
        debug_words.push_back(debug_word);
        debug_events.push_back(debug_event);
    }

    static uint8_array_utils::value_type output_buf[max_nrow * max_ncol] = {};
    uint8_array_utils::read_array<mem_dwidth>(mem + output_word_idx, output_buf, image_elems);

    streamutils::write_uint32_file(resp, (data_dir + "/resp_data.bin").c_str());
    uint8_array_utils::write_uint32_file_array(output_buf, (data_dir + "/im_out_array.bin").c_str(), image_elems);
    {
        std::ofstream debug_ofs(data_dir + "/debug_data.bin", std::ios::binary);
        if (!debug_ofs) {
            throw std::runtime_error("Failed to open debug_data.bin for writing.");
        }
        for (const auto& word : debug_words) {
            streamutils::write_le_uint32(debug_ofs, static_cast<uint32_t>(word));
        }
    }

    const Conv2DDebug last_debug_event = debug_events.empty() ? Conv2DDebug() : debug_events.back();

    std::ofstream sync_ofs(data_dir + "/sync_status.json");
    if (!sync_ofs) {
        throw std::runtime_error("Failed to open sync_status.json for writing.");
    }

    sync_ofs
        << "{\n"
        << "  \"resp_tlast\": \"" << streamutils::to_string(resp_tlast) << "\",\n"
        << "  \"row_ind\": " << static_cast<unsigned>(row_ind) << ",\n"
        << "  \"debug_tlast\": \"" << streamutils::to_string(debug_tlast) << "\",\n"
        << "  \"debug_event_count\": " << debug_words.size() << ",\n"
        << "  \"event\": " << static_cast<unsigned>(last_debug_event.event) << ",\n"
        << "  \"event_name\": \"" << enum_to_string(last_debug_event.event) << "\",\n"
        << "  \"debug_row_ind\": " << static_cast<unsigned>(last_debug_event.row_ind) << "\n"
        << "}\n";

    return 0;
}