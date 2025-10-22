---
title: Building a Vitis HLS project
parent: Installation and Set-Up
nav_order: 2
has_children: false
---

# Building a Vitis HLS Project

[Vitis HLS (High-Level Synthesis)](https://www.amd.com/en/products/software/adaptive-socs-and-fpgas/vitis/vitis-hls.html) is a tool from AMD that lets you design hardware accelerators using C, C++, or OpenCL, automatically converting your code into optimized RTL for FPGA implementation. It bridges the gap between software and hardware design, making it easier to prototype, analyze, and refine custom logic without writing Verilog or VHDL.
In most of the demos in this class, we first build a Vitis IP core (IP = intellectual property) to perform some task, like matrix multiplication. We then integrate that IP into a larger FPGA design using a second tool, Vivado, also from AMD.

In this note, we describe how we organize Vitis projects and show how to build them using Vitis HLS.

## Directory structure

Most Vitis projects in the repository follow the directory structure that we use for the vector multiplier.  The overall directory is `/fpgademos/vector_mult` and the Vitis files are in a sub-folder, `vmult_vitis`.  The Vitis folder has an internal structure:
~~~
   vmult_vitis
   ├── include
   │   └── vmult.h
   ├── src
   │   └── vmult.cpp
   ├── testbench
   │   └── tb_vmult.cpp
~~~
The structure has separate source, include, and testbench files.

As the project is designed and synthesized many new files will be created.  But, these are the only necessary source design files.

## Selecting the FPGA target
To synthesize the Vitis IP,  we need to to find the precise target part number of the FPGA that the IP will run on.  We can get this part number from any Vivado project with the SOC as one of the parts.  Once you have such a Vivado project:

   * Select the menu option `Report->Report IP Status`.  This will open a panel `IP status` at the bottom.
   * For the RFSoC 4x2, you can see the part number for something like `/zynq_ultra_ps_e_0`.  That part number will be something like `xczu48dr-ffvg1517-2-e`.  This is the part number you will need.

## Building the project manually
Once you have written the design files for the Vitis IP, you can create the project either manually or via a script.  
For the manual method using the example `vmult_vitis` as before:

* Launch Vitis HLS (see the [installation instructions]({{ site.baseurl }}/docs/installation.md#launching-vitis))
* Go to `File → New Component → HLS`.  You will set a sequence of items:
   * For `Component name` select `vmult_hls`
   * For `Component location` select `fpgademos/vector_mult/vmult_vitis`
   * For `Configuration File` select `Empty File`
   * For `Source Files` set:
       * Top Function: `vec_mult`
       * Design Files: Add `src/vmult.cpp` and `include/vmult.h`
       * Testbench: Add `testbench/tb_vmult.cpp`
   * For `Hardware` part select `xczu48dr-ffvg1517-2-e` as above
   * For `Settings` keep as default, including clock period of `10ns`
* Vitis will reopen withthe project.

If you do not have the source files like `vmult.cpp` of `vmult.h`, you can still create the project, and build them after the project is created.  In fact, the Vitis Unified IDE has an excellent editor.  

## Building the project with a TCL script
Instead of manually creating the project through the GUI, you can automate the process using a TCL script. This is especially useful for reproducibility and version control.

An example TCL file  `build_vmult.tcl`, for the above project is:
~~~tcl
    open_project vmult_hls -reset
    set_top vec_mult

    add_files -cflags "-Iinclude" src/vmult.cpp
    add_files -tb testbench/vmult_tb.cpp

    open_solution "solution1" -reset
    set_part {xczu48dr-ffvg1517-2-e}
    create_clock -period 10 -name default

    csim_design
    csynth_design
    cosim_design
    export_design -format ip_catalog
~~~
We place the file right in `vmult_vitis` directory to avoid to many indirect references.  You can now run the TCL script either in the Vitis HLS IDE or from a command line.


## Running the TCL script in Vitis HLS

- Launch Vitis HLS (see the [installation instructions]({{ site.baseurl }}/docs/installation.md#launching-vitis))
- Open the TCL Console
    - In the bottom panel of the IDE, locate the TCL Console tab.
    - If it’s not visible, go to `Window → Show View → TCL` Console.
- Navigate to the project folder
    - Use the `cd` command to change into the folder where your script lives:
    ~~~
    cd fpgademos/vector_mult/vmult_vitis
    ~~~
- Run the script
-    Use the source command to execute the script:
~~~bash
    source build_vmult.tcl
~~~
- Watch the output
    - The console will show progress as it runs simulation, synthesis, and co-simulation.
    - If there are errors (e.g., missing files), they’ll appear here.



## Running a Vitis HLS TCL script from the command line
* Open a terminal (e.g., PowerShell, Command Prompt, or bash)
* Navigate to the project folder
~~~bash
    cd fpgademos/vector_mult/vmult_vitis
~~~
* Run the script using vitis_hls
~~~bash
    vitis_hls -f build_vmult.tcl
~~~
This launches Vitis HLS in batch mode and executes the commands in your script.  This method is useful since you can run 

