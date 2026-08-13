---
title: Line Intersection
parent: Labs
nav_order: 5
has_children: true
---

# Vitis HLS Implementation of a Line Intersection

A basic problem in many physical simulations is to determine how close points in 3D are to simple shapes.  This problem arises, for example, in robotics for collision detection.  In this lab, we consider a simple version of this problem where we build a Vitis HLS IP to compute the distance of 3D points to a line segment.

In going through this lab, you will learn to:

- Describe command and response jobs to an IP with Data Schemas
- Build a python Golden model for a loop
- Implement a **pipelined loop** of the same computation in Vitis HLS
- Design memory layouts and nested loops for optimal pipelining
- **Synthesize** the design
- Compare expected results with the Golden model for **functional validation**
- Parse C synthesis reports to determine the **latency** and **initiation interval (II)** of the design

## Files

All files for the lab can be found in this repo in:

```bash
hwdesign/labs/intersect
```

In this directory, you will find:

```text
intersect/
|-- run_hls.tcl          // TCL script for simulation and C synthesis
|-- run_tests.py         // Submission program
|-- line_inter_tb.cpp    // Vitis HLS testbench
`-- partial/
	|-- line_inter.ipynb   // main jupyter notebook
	`-- line_inter.cpp    // Vitis kernel
```

Copy all the files in the `intersect/partial` directory to `intersect`.  

---

Go to [building the python model](./python.md)




