---
title: Building a Vitis HLS project
parent: Vitis and Vivado
nav_order: 8
has_children: false
---

# Building a Vitis HLS Project

In this note, we describe how we organize Vitis projects and show how to build them using Vitis HLS.

## Directory structure

Most Vitis projects in the repository follow the directory structure that we use for the vector multiplier.  For the vector multiplier project, the overall directory is `/hwdesign/vector_mult` and the Vitis files are in a sub-folder, `vmult_vitis`.  The Vitis folder has an internal structure:
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


## Building the project manually
Once you have written the design files for the Vitis IP, you can create the project either manually or via a script.  
For the manual method, the steps for the example `vmult_vitis` are as follows.  You can modify them for any other project.

* [Launch Vitis HLS](./launching.md)
* Go to **File → New Component → HLS**.  You will set a sequence of items:
   * For **Component name** select `hls_component`
   * For **Component location** select `hwdesign/vector_mult/vmult_vitis`
   * For **Configuration File** select `Empty File`
   * For **Source Files** set:
       * Top Function: `vec_mult`
       * Design Files: Add `src/vmult.cpp` and `include/vmult.h`
       * Testbench: Add `testbench/tb_vmult.cpp`
   * For **Hardware** part select the part number such as `xczu48dr-ffvg1517-2-e` as in [building the Vivado project](./vivado_build.md)
   * For **Settings** keep as default, except increase the clock frequency to `250MHz`
* Vitis will reopen with the project.

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
    create_clock -period 2.5 -name default

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
    cd hwdesign/vector_mult/vmult_vitis
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
    cd hwdesign/vector_mult/vmult_vitis
~~~
* Run the script using vitis_hls
~~~bash
    vitis_hls -f build_vmult.tcl
~~~
This launches Vitis HLS in batch mode and executes the commands in your script.  This method is useful since you can run 

