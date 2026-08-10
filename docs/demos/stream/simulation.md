---
title: Simulating and Viewing the Timing
parent: AXI4-Streaming
nav_order: 3
has_children: false
---

# Simulation and Viewing the Timing Diagram

## Simulating the Averaging Kernel  

To simulate the kernel and testbench:

- Open a command terminal (not Powershell) in Windows, or Unix terminal in IoS/Unix
- [Set the paths for the Vitis HLS tools](../../support/amd/launching.md)
- Run the TCL script

```bash
vitis-run --mode hls --tcl run_avg_hls.tcl
```

This script will run:

- C simulation
- C synthesis
- RTL simualtion

## Creating and Viewing the VCD File

We then re-run the simulation to create a VCD file:

```bash
xsim_vcd --top avgfilt --comp hls_component --out dump_avg.vcd
```

You can then use the jupyter notebook, `view_timing.ipynb` to view the timing diagrams.