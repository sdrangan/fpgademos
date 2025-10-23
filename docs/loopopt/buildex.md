---
title: Vector multiplier example
parent: Loop optimization
nav_order: 1
has_children: false
---

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

   

## Building and Simulating the the Vector Multiplier

The design files for this Vitis project are in the repo `fpgademos/vector_mult/vmult_vitis`.  Follow the instructions to [build the Vitis HLS project]]({{ site.baseurl }}/docs/vitis_build.md)) to build the project for these design files.  
The top of the file `include/vmult.h` provides a number of parameters that we can vary to see the effect of the optimization:
~~~C
#define PIPELINE_EN 0  // Enables pipelining
#define UNROLL_FACTOR 1  // Unrolls loops when > 1
#define MAX_SIZE 1024  // Array size to test
#define DATA_FLOAT 1   // Data type:  1= float, 0=int
~~~
To try different optimizations, we will simply changes the values and re-run synthesis.

But, before we synthesize the Vitis IP, let's make sure that the model is functionally correct by running it against the testbench.  In the Vitis IDE GUI, go the `Flow` Panel (left sidebar) and select `C Simulation->Run`.  This will run the testbench that generates two vectors `a` and `b` and confirms that the output is expected.  Among many outputs you see in the `Output` window is `Test passed!`.

---

Go to the [initial synthesis](./synth.md).