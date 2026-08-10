---
title: Building and Simulating Projects with System Verilog Files
parent: Vitis and Vivado
nav_order: 6
has_children: false
--- 

# Building a Vivado Project with the GUI

## Overview

In this course, we will use two types of Vivado projects:

- **Projects with SystemVerilog files**  
  These appear early in the course and are used to simulate simple circuits.  
  They are *simulation‑only* and will not be deployed to an FPGA.

- **Projects with processing systems integrated with Vitis IP**  
  These appear later in the course and involve building and simulating Vitis IP separately, then integrating everything inside a Vivado block design.  
  These projects *can* be deployed on a real FPGA board.

This note explains how to build simple SystemVerilog‑based projects using the **Vivado GUI**.  
If you prefer the command‑line workflow, you can skip this note entirely — all demos and labs include full command‑line instructions. The GUI is optional and provided only for students who prefer a visual workflow.

The [next note](./sv_build.md) describes building Vivado projects that include processing systems and Vitis IP.


## Example project

As an example system verilog project to build, consider building the demo for [simple scalar function](../../demos/simp_fun/).  The files for this demo are in the location:

```
hwdesign/demos/fsm
```

This directory has two files:

- `lin_relu.sv`:  Defines a simple linear + ReLU function in SV.
- `tb_lin_relu.sv`:  Defines the testbench in SV.

You can follow the steps to simulate the counter in the [demo](../../demos/simp_fun/simulation.md)
entirely with command line utilities.  This note will provide you the steps for simulating the SV files with the Vivado GUI, if you prefer.

## Building the SystemVerilog Files with Vivado

The steps for the simulating a project with source and testbench
SystemVerilog files with the Vivado GUI is as follows:

* [Launch the Vivado GUI](./launching.md)
   * Note that if you are on the [NYU server](../nyuremote/), you will need to
   follow slightly [different instructions](../nyuremote/launching.md). 
* Select the menu option **File->Project->New...**.  
   * For the project name, you can leave it as the default value, say `project_1`.  
   * In location, use the directory of the SV files.  In this example, the files are in `hwdesign/demos/simp_fun`.  The Vivado project will then be stored in this directory
* Select **RTL project**.  
   * Leave *Do not specify sources at this time* checked.
* For **Default part**, select the `Boards` tab and then select:
   * For the RFSoC 4x2, select `Zynq UltraScale+ RFSoC 4x2 Development Board`.
   * For the PYNQ-Z2 board, select `pynq-z2` or something similar
* The Vivado window should now open with a blank project.
* You will see a number of files including the project directory.
* Add project files:  In the left panel select **Add sources** and add the two files,
`lin_relu.sv` and `tb_lin_relu.sv`.  These files could have been added earlier.

Vivado will automatically detect the module hierarchy. In this example,
it will place the testbench, `tb_lin_relu.sv` at the top, and the `dut` below that.

You can edit or view either of the files with **File->Text Editor->Open Source**.
The files will appear in a panel on the right.

## Simulating the Project

To simulate the project, we simply select from the **Simulation panel**,
the option **Run simulation**.  The top level SystemVerilog file should now
be simulated.  You will see print outs in the **Tcl console** window,
tha is usually at the bottom.  Any CSV files that are created in the
simulation will also be created.

You can also select the **Window->Waveform** menu option and see a timing diagram.
Unfortunately, there is no way to download this waveform trace.
Later, we will discuss how to create VCD traces that can be downloaded
and analyzed in python.


