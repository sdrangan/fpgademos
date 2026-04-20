---
title: Design
parent: 2D Convolution Accelerator
nav_order: 2
has_children: false
---

# IP Design

## Overview

The Conv2D accelerator is defined in the file in the repo location:

```bash
hwdesign/demos/conv2d/conv2d.cpp
```

The kernel is controlled by a `Conv2DCmd` message that supplies:

- The input image dimensions, `nrows x ncols`
- The square kernel size `K = kernel_size`
- The external-memory base addresses for the input image, output image, and kernel


The implementation first validates the command fields. It checks that the image dimensions and kernel size are within the hardware limits and that all memory addresses are aligned to the AXI memory word width. If any check fails, the kernel returns immediately with an error code in `Conv2DResp`.

After validation, the kernel operates in four stages:

1. It reads the `K x K` kernel coefficients from external memory into a local buffer `kernel_buf`.
2. It initializes a `K x ncols` line buffer with zeros so the top image boundary is handled with zero padding.
3. It iterates across the image rows, maintaining the most recent `K` rows in a circular line buffer. For each output row it:
   - Loads one new input row from memory, or inserts a zero row once the bottom of the image has been reached
   - Forms the first `K x K` sliding window for that output row, including zero padding at the left and right boundaries
   - Sweeps across the columns, producing one output pixel per cycle in the pipelined inner loop
   - Stores the completed output row back to external memory
4. When all output rows are written, it emits a `Conv2DResp` message.

The operation is a same-size 2D correlation with zero padding. In other words, the kernel coefficients are applied in their stored order rather than being spatially flipped as in a mathematical convolution. The padding origin is determined by

$$
	ext{kernel\_anchor} = \left\lfloor \frac{K-1}{2} \right\rfloor
$$

so odd-sized kernels are centered naturally, while even-sized kernels use the anchor convention implemented in the code.

## Sliding-Window MAC Kernel

The computational core is a fully unrolled multiply-accumulate array built around a sliding `window_buf`:

- `kernel_buf` and `window_buf` are fully partitioned, so all `K x K` products are available in parallel
- The helper function `systolic_mac()` multiplies corresponding entries of the image window and kernel and reduces them to a single accumulation value
- After each output pixel is computed, the window shifts left by one column and the next input column is inserted on the right
- The column loop is pipelined with initiation interval `II=1`, so once the pipeline is full the kernel can produce one output pixel per clock cycle

The accumulator uses a 24-bit signed intermediate type. After accumulation, the result is shifted right by `kernel_fbits = 7` to compensate for the fixed-point scaling of the signed 8-bit kernel coefficients, then saturated to the 8-bit output pixel range `[0, 255]`.

For observability, the kernel also emits debug events on a separate AXI4-Stream interface. These events mark the start and end of the main routine and each per-row load, compute, and store phase, which is useful when inspecting timing traces or VCD captures.



