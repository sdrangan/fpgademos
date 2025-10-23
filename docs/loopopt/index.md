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

---

Go to [Building the vector multiplier example](./buildex.md).


