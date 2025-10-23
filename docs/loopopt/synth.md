---
title: Initial synthesis 
parent: Loop optimization
nav_order: 2
has_children: false
---

# Initial Synthesis

## Understanding the loop
We focus on our simple loop that, without the compiler directives (`#pragma` statements) is simply:
~~~C
for (i=0; i < n; i++) {
    c_buf[i] = a_buf[i] * b_buf[i]
}
~~~
In hardware, each iteration would be implemented as a set of steps like:
* Load `a_buf[i]` into some register, say `A`
* Load `b_buf[i]` into some register, say `B`
* Multiply `A*B` and store in some register, say `C`
* Store `C` in `c_buf[i]`
* Increment `i`

Synthesis balances trying to perform these operations
quickly vs. using a lot of hardware resources.


## Performing the initial synthesis

Let's perform an initial synthesis with no optimization
to see the results.

* In `include/vmult.h` set the parameters:
~~~C
#define PIPELINE_EN 0  // Enables pipelining
#define UNROLL_FACTOR 1  // Unrolls loops when > 1
#define MAX_SIZE 1024  // Array size to test
#define DATA_FLOAT 1   // Data type:  1= float, 0=int
~~~
which are the default parameters.  These parameters will perform no optimization.
* In the `Flow` panel (left sidebar), select `C Synthesis->Run`.
The synthesis will map the C design to logic elements and build a state machine for the overall execution flow.

The synthesis for a simple design like this takes under a minute and will generate a number of files.

## Analyzing the performance
The synthesis provides an estimate of how long the loop takes to execute in hardware.  In general, the number of cycles to execute a loop with `n` iterations (sometimes called *trip count*) is given by:
~~~
  num cycles = L0 + n*II
~~~
where `L0` is the *iteration latency*, which is the number of cycles for the first iteration to complete, and `II` is the *iteration interval*, which is the number of cycles for each additional iteration.  The total time in seconds is
~~~
   total latency = (num cycles)*Tclk
~~~
where `Tclk` is the clock period.   For this design, I have somewhat aggressively set `fclk = 1/Tclk=300 Mhz`.

We can find out the parameters for our initial synthesis:

* In the `Flow` panel, select `C Synthesis->Reports->Synthesis`.  This will open a Summary Synthesis Report.  
* Scroll to the `Modules & Loop` section.
* In the table, there will be one entry for each loop.  The data for multiplication loop is `vec_mult_Pipeline_mult_loop`.

You will likely see parameters:
   * `Interval = 1` meaning `II=1` which is the optimal.  This means that all the steps in the interval could be completed in one clock cycle.
   * `Iteration latency = 10`, referring to the initial latency.

With the above clock rate and trip count of `n=1024`, the total latency was `1034` clock cycles or about `3.44 us`.  
These metrics help us understand how efficiently the loop maps to hardware — whether operations are serialized or overlapped, and how well the design meets timing constraints.
---

Go to [Optimizing the loop](./synthopt.md).