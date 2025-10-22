---
title: Building the FPGA accelerator
parent: Getting started
nav_order: 3
has_children: false
---

# Building the FPGA accelerator

These instructions show how to:

* Create the Vitis IP for the simple scalar adder function.
* Build a barebones Vivado project with the Zynq UltraScale+ MPSOC
* Integrate the Vitis IP into the project
* Generate a bitstream for the FPGA
* Create a PYNQ overlay to access the Vitis IP running on the FPGA from python

The final overlay will then be used by the (notebooks)[{{ site.baseurl }}/scalar_adder/notebooks/scalar_add.ipynb].

The instructions below show how to build the entire project from scratch.  But, at the end, I have provided instructions to generate the Vitis and Vivado projects from TCL files and the files in the github repo.

## Creating the Vivado project

We first create an Vivado project with the MPSOC:

* Launch Vivado (see the [installation instructions]({{ site.baseurl }}/docs/installation.md#launching-vivado)):
* Select the menu option `File->Project->New...`.  
   * For the project name, use `scalar_adder_vivado`.  
   * In location, use the directory `fpgademos/scalar_adder`.  The Vivado project will then be stored in `scalar_adder/scalar_adder_vivado`.
* Select `RTL project`.  
   * Leave `Do not specify sources at this time` checked.
* For `Default part`, select the `Boards` tab and then select `Zynq UltraScale+ RFSoC 4x2 Development Board`.
* The Vivado window should now open with a blank project.
* You will see a number of files including the project directory, `scalar_adder\scalar_add_vivado`.
* Before the next step, we need to to find the precise target part number of the FPGA that the IP will run on.  This target part number will be used for Vitis in the next step:
   * Select the menu option `Report->Report IP Status`.  This will open a panel `IP status` at the bottom.
   * In this panel, you can see the part number for something like `/zynq_ultra_ps_e_0`.  That part number will be something like `xczu48dr-ffvg1517-2-e`

## Creating the Vitis HLS Project

* Launch Vitis (see the [installation instructions]({{ site.baseurl }}/docs/installation.md#launching-vitis))
* Select `Open Workspace`.  Go to the directory `fpgademos\scalar_adder`.  This is where we will put the workspace.  `Vitis_HLS` will reopen.
* Select `Create component->Create empty HLS component`.  You will walk through the following six steps:
    * For `Name and location`, select component name as `scalar_add_vitis`
    * Set the `Configuration file` select `Empty File` which is the default
    * In `Source Files`, select top function to `add`
    * In the `Hardware` tab, you will need to select the hardware you are targetting.  Select `Part`.  Then for family, select `zynquplusRFSoC`.  You can use the part numbers to select the remaining options.  In my case, the packages is `ffvg1517`.  The speed grade is `-2` and the Temp grade is `E`.  You should see your part.
    * In the `Settings` tab, I kept all defaults, but later will change the clock speed
* Now you should have an empty project.
* Sometimes the part number was not correct.  To verify the selection of the part, on the `Flow` panel (left sidebar), go to the `C Synthesis` section and select the settings (gear box).
    * In the `General` tab, there is `part` number.  Set the part number to `xczu48dr-ffvg1517-2-e` or whatever the correct part number is 

## Creating the Vitis IP and Testbench Source files
* In the directory `scalar_add_vitis/src/`, create the source C file, `scalar_add.cpp` describing the functionality for our "IP":
~~~c
    void add(int a, int b, int& c) {
        #pragma HLS INTERFACE s_axilite port=a
        #pragma HLS INTERFACE s_axilite port=b
        #pragma HLS INTERFACE s_axilite port=c
        #pragma HLS INTERFACE s_axilite port=return
        c = a + b;
        }
~~~
This file is already in the git repo, so you can skip this step if you are using the repo.
* In the SCALAR_ADD_VITIS explorer pane (left sidebar), right click `Sources` and select `Add Source File` and open `scalar_add.cpp`.   We have now added the file to our project.
Alternatively, you could have selected `New Source File` and created the file here.
* Next create a testbench. Generally, we place the testbenches in a separate directory, which in our case will be: `scalar_add_vitis/testbench`.   Tehe must follow the same name as the component with `tb_` as a prefix.  So, for this case the file will be  `tb_scalar_add.cpp` and located in the `scalar_add_vitis/testbench` directory:
~~~c
    #include <iostream>
    void add(int a, int b, int& c);

    int main() {
      int result;
      add(7, 5, result);
      std::cout << "Result: " << result << std::endl;
      return 0;
    }
~~~
* In the `FLOW` panel (left sidebar), select `C Simulation->Run`.  It should run with a result of 12
* Still in the `FLOW` panel,  select `C synthesis->Run` 
* Next in the `FLOW` panel, `Package->Run`.
* The packaging will have created a directory of files containing the *IP* for the adder.  It will be located in `scalar_adder_vitis/scalar_add/add/hls/impl/ip`. 

## Adding the scalar adder IP to Vivado
* Go to `Tools->Settings->IP`.  Select the `+` sign in `IP Repositories`.  Navigate to the directory with the adder component.  In our case, this was at:  `scalar_adder_vitis/scalar_add/add/hls/impl/ip`.  
* Select the `Add IP` button (`+`) again.  Add this IP.  Now the `Add` block should show up as an option.  If it doesn't it is possible that you synthesized for the wrong FPGA part number.  
* You should see an Vitis IP block with ports `s_axi_control`, `interrupt` and some clocks.  Select the "run block automation".  This will add a PS_AXI interface block to interface between the PS and AXI slave interface for the adder.
* We will leave the `interrupt` unconnected for now.  In future demos, you will see how to connect the interrupts to the processor. 
* Select the `Add` block.  In the `Block Properties` panel, select the `General` tab, and rename the block to `add`.  This is the name that we will use when calling the function from `PYNQ`.

## Creating the FPGA Bitstream in Vivado

We are now ready to create the bitstream to program the FPGA with the design.

* Generate output products:
   - In the `Block Design` window, open the `Sources` panel (left).
   - Right-click `design_1.bd` and select `Generate Output Products...`.
   - This step converts the Block Design (BD) into HDL netlists, making it usable for synthesis.
* Create HDL wrapper:
   - The first time you generate output products, you need to generate the BD in a top-level module that Vivado can synthesize.  You only need to do this once.  If you later make chnages, you do not need to re-run this step.
   - Right-click `design_1.bd` again and select `Create HDL Wrapper...`.
   - Choose "Let Vivado manage wrapper and auto-update" (recommended).
* Run Synthesis
   - In the **Flow Navigator** panel (left), click **Run Synthesis**.
   - This converts your HDL design into a *netlist*—a set of logic elements and their interconnections.
   - You’ll see a pinwheel and the message `Running synthesis...` in the top right.
   - For simple designs, this finishes in under a minute. For larger ones, synthesis (and later steps) can take hours—so enjoy the speed while it lasts!
* Run Implementation:
   - Still in the `Flow Navigator`, click `Run Implementation`.
   - This step physically maps the synthesized logic onto the FPGA fabric.
   - Expect a few minutes of processing time.
* Generate Bitstream
   - Finally, click `Generate Bitstream` in the `Flow Navigator`.
   - This creates the `.bit` file that programs the FPGA with your design.


## Creating a PYNQ Overlay

A **PYNQ overlay** is a packaged hardware design (bitstream + metadata) that can be loaded and controlled from Python on a PYNQ-enabled board (like ZCU111, ZCU104 or RFSoC). It abstracts the FPGA logic into a Python-friendly interface.
Follow the following steps to create the PYNQ overlay.

* Locate your bitstream and metadata file.  Vivado can place the files in crazy locations.  So, I suggest you go to the top directory and run the following command from the Vivado project directory for this demo:
~~~bash
    find . -name *.bit
    find . -name *.hwh
~~~
You will locate files with names like:
    *  `scalar_adder_wrapper.bit` — the FPGA configuration file
    * `scalar_adder.hwh` — the hardware handoff file with IP metadata
They are generally in two different directories.  
*  In the same directory as the `.bit` file, find the TCL file, like `scalar_adder_wrapper.tcl`. This file is useful for scripting.  For some reason, there may be multiple `tcl` files in the Vivado project directory.  Take the one in the same directory as the `.bit` file.
* Copy all the files to the `overlay` directory and rename them as:  `scalar_adder.bit`, `scalar_adder.hwh`, `scalar_adder.tcl`.

## Connecting to the RFSoC

* Now follow the instructions on the [RFSoC-PYNQ getting started page](https://www.rfsoc-pynq.io/rfsoc_4x2_getting_started.html).
You should be able to connect to the browser from the host PC at `http://192.168.3.1/lab`. 
* Enter the password `xilinx`.
* Create a directory `scalar_add_demo` with a subdirectory `overlay`.  In the future, I will make this so you can clone the git repo here and have the files on the FPGA board.
* Upload the files in the `overlay` directory to the `overlay` directory on the FPGA board



