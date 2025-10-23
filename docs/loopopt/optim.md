---
title: Pipelining and unrolling 
parent: Loop optimization
nav_order: 3
has_children: false
---

# Pipelining and Unrolling

In the previous section, we synthesized a simple loop without any optimization. Now we’ll explore two powerful techniques that can dramatically improve performance: **loop pipelining** and **loop unrolling**.

## What is pipelining?

Pipelining allows the hardware to start a new loop iteration before the previous one finishes — much like an assembly line. Instead of waiting for each multiply-store operation to complete before starting the next, pipelining overlaps them across clock cycles.  

This is controlled using the directive:
~~~C
#pragma HLS PIPELINE II=1
~~~
Here, `II` stands for initiation interval — the number of cycles between starting consecutive iterations. An `II=1` means the loop starts a new iteration every cycle, which is ideal for throughput.

## Synthesis with pipelining
To enable pipelining:
In `include/vmult.h`, set:
~~~C
#define PIPELINE_EN 1
~~~
Then re-run synthesis and examine the loop report. You should see:
- `Interval = 1` meaning `II=1`

In our simple example, even without pipelining, `II=1`, so the pipelining doesn't help.  The number of steps were sufficiently small that all the operations could complete in one clock cycle. But for more complex operations within each loop iteration, pipelining can be significant.

## What is unrolling?
Unrolling duplicates the loop body to perform multiple iterations in parallel.  For example, an unroll factor of 4 is like:
~~~C
for (i=0; i < n; i += 4) {
    c_buf[i] = a_buf[i] * b_buf[i];
    c_buf[i+1] = a_buf[i+1] * b_buf[i+1];
    c_buf[i+2] = a_buf[i+2] * b_buf[i+2];
    c_buf[i+3] = a_buf[i+3] * b_buf[i+3];
}
~~~ 
which means that there are four multiplies in each clock cycle.
This unrolling is realized in hardware by instantiating up to four physical multiply units that run in parallel.  Ideally, this parallelism will reduce the latency by 4.

In the above example, suppose `n=1024` and we unroll by a factor of 4.  We say `n=1024` is the *number of iterations* and the loop has 256 *trips* — each trip performs 4 multiplications in parallel due to unrolling."


In Vitis HLS, you do not need to manually unroll the loop.  You can simply add the pragma: 
~~~C
#pragma HLS UNROLL factor=2
~~~

## Array partitioning
Unforunately, unrolling may not get the full gain.  In addition to multiplications, each iteration must read from buffers `a_buf` and `b_buf` and store to `c_buf`.  Generally each of these buffers can only support one or two accesses per cycle.
Hence, they will be a bottleneck.  To avoid this bottleneck, we
partition the buffers into discrete blocks, each with its own addressing logic to parallelize access.
This is done with the compiler directive:
~~~C
#pragma HLS ARRAY_PARTITION variable=a_buf type=cyclic factor=4  dim=1
~~~
Note:
* The parameter `dim=1` refers to partitioning along the first dimension — the index used in `a_buf[i]`.
* We used `type=cyclic` to partion so that it puts `0,4,8,...` in the first partition, `1,5,9,...` in the second partition and so on.


## Synthesis with unrolling
To enable unrolling, say by a factor of 4:
In `include/vmult.h`, set:
~~~C
#define UNROLL_FACTOR 4
~~~
Then re-run synthesis and examine the loop report. You should see:
- `Interval = 1` meaning `II=1`
- `Trip count = 256` meaning that loop with `n=1024` iterations only required 256 *trips*.  





