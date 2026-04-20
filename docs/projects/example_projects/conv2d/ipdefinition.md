---
title: IP Definition
parent: 2D Convolution Accelerator
nav_order: 1
has_children: false
---

# IP Definition

## Convolution Operation

The accelerator performs a simple 2D-convolution.  Specifically, given an input array `x[n0,n1]` and kernel `ker[k0,k1]`, the function computes the 2D convolution:

```
y[n0,n1] = \sum_{i0,i1} ker[i0,i1]*x[n0+i1,n0+i2]
```

For simplicity in this example, the accelerator makes the following restrictions:

- Input `x` and kernel `ker` are fixed point with constant total bits and fractional bits
- Only a single input and output channel are supported
- Only `same` mode is supported so that `y` has the same shape as the `x`.
- In the current implementation, the hardware supports images up to ` max_nrow x max_ncols = 512 x 512` pixels and kernels up to `max_kernel_size x max_kernel_size = 4 x 4`.  Kernels are restricted to be square.


## Interface Definition

The kernel definion can be found in `conv2d/conv2d.cpp` and has three 

- `mem`:  A shared memory interface to retrieve the kernel and input data, and to retrieve the output data
- `in_stream`:  An AXI4 stream for getting the command data
- `out_stream`:  An AXI4 strem for transmitting back the response at the end of the operation
- `debug_stream`:  An AXI4 stream for outputting events during the processing. This stream is used for debugging and profiling

## Interface protocol

The operation with a test bench (TB) is as follows:

- TB sends a `Conv2DCmd` message with:
    - a transaction ID, 
    - read pointer in the shared memory for the kernel and data
    - size information such `nrows` and `ncols`
    - write pointer in the shared memory for the output
- Kernel fetches the input and kernel data, computes the output and writes the output data to shared memory.  
    - As the kernel is processing, it sends `Conv2DDebug` messages indicating which stage of processing (`load`, `compute` or `store`) the kernel is executing and the row index.  This information can be used for profiling
- When complete, the kernels sends a `Conv2DResp` message to the TB that echoes the transaction ID and also provides error codes, if any.

All messages are defined with the PySilicon DataList class to enable auto-generation of the related Vitis include files.  See `conv2d_demo.py` for details of the schema definitions.



