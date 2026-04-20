---
title: Timing and Resource Results
parent: 2D Convolution Accelerator
nav_order: 4
has_children: false
---

# Timing and Resource Results

## Synthesis Results

The core loop in the 2D convolution accelerator is the loop over the pixels in each row.  Each iteration of the loop performs one step of the systolic array to output a kernel - window product and shifts the data into for the next column.  The C synthesis report confirms that the loop was pipelined with `II=1`.

| metric        |   value |
|:--------------|--------:|
| PipelineII    |       1 |
| PipelineDepth |       6 |
| TripCountMin  |       1 |
| TripCountMax  |     512 |
| LatencyMin    |       5 |
| LatencyMax    |     516 |



## Timing Analysis

The key timing analysis metrics are below:

| metric       | value    |
|:-------------|:---------|
| shape        | 16 x 128 |
| clock period | 10 ns    |
| latency      | 47260 ns |
| cycles       | 4726     |

| stage   |   nrows |   median_time |   mean_time |
|:--------|--------:|--------------:|------------:|
| load    |      17 |           460 |     510.588 |
| compute |      17 |          1340 |    1261.18  |
| store   |      17 |           610 |     574.118 |


The following are key points:

- Compute time is consistent with a pipeline of `II=1` obtain approximately one column per cycle
- Load and store times are consistent with reading and writing 4 pixels / cycle (pixels are 8 bits and AXI4 memory interface is 32 bits)


## Resource usage

The kernel was synthesized for a `xc7z020clg484-1` Xilinx FPGA,
the FPGA on a student Pynq-Z2 board. The total usage is as follows:

| Module                                   |   BRAM_18K |   DSP |     FF |   LUT |   URAM |
|:-----------------------------------------|-----------:|------:|-------:|------:|-------:|
| read_axi4_stream_impl                    |          0 |     0 |    647 |   159 |      0 |
| write_axi4_stream_32_s                   |          0 |     0 |      2 |    25 |      0 |
| conv2d_Pipeline_VITIS_LOOP_617_1         |          0 |     0 |     77 |   188 |      0 |
| conv2d_Pipeline_VITIS_LOOP_178_3         |          0 |     0 |     12 |    52 |      0 |
| conv2d_Pipeline_clear_bottom_padding_row |          0 |     0 |     18 |    73 |      0 |
| conv2d_Pipeline_VITIS_LOOP_617_11        |          0 |     0 |    105 |   231 |      0 |
| conv2d_Pipeline_convolve_row             |          0 |     0 |    805 |  2290 |      0 |
| conv2d_Pipeline_VITIS_LOOP_658_1         |          0 |     0 |    121 |   363 |      0 |
| conv2d                                   |         12 |     0 |   4556 |  8551 |      0 |
| Total                                    |         12 |     0 |   4556 |  8551 |      0 |
| Available                                |        280 |   220 | 106400 | 53200 |      0 |


Some key points:



-  The `conv2d` module itself is small, implying that, for such a simple kernel, the interconnect to the kernel is the bottleneck.
-  The resources are also a small fraction of the
overall resources.  The low utilization implies that greater unrolling or larger kernels (and hence greater throughput) would be easily possible
- There are no DSP48 slices used since the multiplications are 8 bits, and hence likely mapped to LUTs.


