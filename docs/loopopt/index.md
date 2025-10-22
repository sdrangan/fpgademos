---
title: Loop optimization
parent: FPGA Demos
nav_order: 3
has_children: true
---

# Loop Optimization

Hardware acceleration is particularly strong when repeating some task multiple times -- equivalent to a loop in software.
While a standard processor can only perform one task in each clock cycle, hardware can replicate many units to operate in parallel.  The challenge is how to coordinate mutliple units and ensure they are fully utilized.  In this unit, we will illustrate these concepts with a simple vector multiplication.   

In going through this unit, you will learn to:
- **Identify and synthesize loop constructs** in Vitis HLS for hardware implementation
- **Analyze loop performance** using *initiation interval (II)*, *latency*, and *resource utilization* from synthesis reports
- **Apply loop pipelining directives** to reduce initiation interval and improve throughput
- **Use loop unrolling** to increase parallelism and reduce total latency

## A simple example:  multiplying two vectors
To illustrate the concepts, we consider the implementation of a simple multiplcation of two vectors.   The code can be found in `fpgademos/vector_mult/vmult_vitis`.  The main program is in `src/vmult.cpp` which contains code with a number of `#pragma` statements that we will describe later.
~~~C
// Vector multiplication function
void vec_mult(int *a, int *b, int *c, int n) {

    // Buffering to optimize memory access
    int a_buf[VecMultConfig::MAX_SIZE], b_buf[VecMultConfig::MAX_SIZE];
    int c_buf[VecMultConfig::MAX_SIZE];

    // Load into local buffers
    input_loop:  for (int i = 0; i < n; i++) {
        a_buf[i] = a[i];
        b_buf[i] = b[i];
    }

    // Multiplcation loop
    mult_loop:  for (int i = 0; i < n; i++) {
        c_buf[i] = a_buf[i] * b_buf[i];
    }
    
    // Store results back to global memory
    output_loop:  for (int i = 0; i < n; i++) {
        c[i] = c_buf[i];
    }
}
~~~
So the code reads data into local buffers, `a_buf` and `b_buf`, multiplies them and stores the result `c_buf` back to external memory.  In this unit, we focus on the optimization of the multiplication loop, `mult_loop`.
We address the data transfer into and out of IP cores in a later unit.  All the data are 32-bit integers.  We will discuss other data types in subsequent units as well.

   

## Building the Vitis Project

The design files for this Vitis project are in the repo `fpgademos/vector_mult/vmult_vitis`.  Follow the instructions to [build the Vitis HLS project]]({{ site.baseurl }}/docs/vitis_build.md)) to build the project for these design files.



