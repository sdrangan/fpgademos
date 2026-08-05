---
title: RTL Simulation
parent: Bus Basics and Memory‑Mapped Interfaces
nav_order: 3
has_children: false
---

# RIL Simulation of the Synthesized Vitis IP

Before adding the Vitis IP to the FPGA project, it is useful to simulate the synthesized RTL.
This step can be done after C Synthesis and C simulation, but before Packaging.

* If Vitis is not already open from the previous step:
    * [Launch Vitis](../../setup/sw_installation/)
    * Open the workspace for the for the Vitis IP that you were using, which should be in `hwdesign/scalar_fun/scalar_fun_vitis`
* In the **Flow panel** (left sidebar), find the **C/RTL Simulation** section
* Select the settings (gear box) in the C/RTL Simulation:
    * Select **cosim.trace.all** to **all** or **port**  This setting will trace all the outputs or the signals at the port level.
* Next select the **C/RTL Simulation->Run**.  This command will execute a RTL-level simulation of the synthesized IP.

## Extracting VCD Files

The C/RTL simulation that is run from the Vitis GUI creates a `.wdb` (waveform database)  file with traces of all the signals.
This format is an AMD proprietary format and cannot be read by other programs,
although you can see it in the Vivado viewer.  So, we will modify the simulation to export 
an alternative open-source **VCD** or [**Value Change Dump**](https://en.wikipedia.org/wiki/Value_change_dump) format.  VCD files can be read by many programs including python.

The `xilinxutils` package has a simple python file that modifies the simulation files to capture the VCD output and re-runs the simulation.  You can execute it as follows:

* [Activate the virtual environment](../../support/repo/package.md) with `waveflow` and `hwdesign`
* Navigate (i.e., `cd`) to the directory of the Vitis IP project.  In the scalar function project, this Vitis project is in `hwdesign\scalar_fun\scalar_fun_vitis`
* Identify the `component_name` and `top_name`. 
    * When the IP was synthesized, Vitis created a directory of the form `<component_name>/<top_name>` based on the names of the component and top-level function.  Based on the settings we used in this project, this directory is: 

    ```bash
    scalar_fun_vitis\hls_component\simp_fun
    ```
    * Hence, in this example `component_name=hls_component` and `top_name=scalar_fun`
* Re-run the simulation with VCD with the command from PowerShell or Linux terminal:

```bash
(env) xsim_vcd --top <top_name> [--comp <component_name>] [--out <vcd_file>]
```

where `vcdfile` is the name of the VCD file with the signal traces.  By default, `<vcd_file>` is `dump.vcd`.  In our example, you will run:

```bash
(env) xsim_vcd --top sim_fun --comp hls_component --out dump.vcd
```

    * Note:  We have not yet created a version of the script `xsim_vcd` for Linux.
    * After running the script, there will be a VCD file with the simulation:

    ```bash
    scalar_fun_vitis\vcd\<vcd_file>
    ```

## Viewing the Timing Diagram
After you have created VCD file, you can see the timing diagram from the [jupyter notebook](https://github.com/sdrangan/hwdesign/tree/main/scalar_fun/notebooks/view_timing.ipynb).

## Understanding the `xsim_vcd.py` function. 

I wrote the function  `xsim_vcd.py` to automate the process of adding a VCD trace.
But you may want to know how this function works, in case you need to modify later.
Basically, the `xsim_vcd.py` does these steps automatically.

* After running the initial simulation, locate the directory where the simulation files are.
For the scalar adder simulation, it will be in something like:

```bash
scalar_fun_vitis\hls_component\scalar_fun\hls\sim\verilog
```

This large directory contains automatically generated RTL files for the testbench along with simuation files.
We will modify these files to output a VCD file and re-run the simulation. 
* In this directory, there will be a file `scalar_fun.tcl` which sets the configuration for the simulation.  Copy the file to a new file `scalar_fun.tcl` and modify as follows:
   *  Add initial lines at the top of the file (before the `log_wave -r /`) line:

    ```tcl
    open_vcd
    log_vcd * 
    ```

    * At the eend of the file there is:
    ```tcl
    run all
    quit
    ```
    
    Modify these lines to:
    ```
    run all
    close_vcd
    quit
    ```

* In the same directory, there is a file, `run_xsim.bat`.  
   * There should be a line like:

    ```bash
    call C:/Xilinx/2025.1/Vivado/bin/xsim  ... -tclbatch scalar_fun.tcl -view add_dataflow_ana.wcfg -protoinst add.protoinst
    ```
   
   * Copy just this line to a new file `run_xsim_vcd.bat` and modify that line to:

    ```bash
    cd /d "%~dp0"
    call C:/Xilinx/2025.1/Vivado/bin/xsim  ... -tclbatch scalar_fun_vcd.tcl -view add_dataflow_ana.wcfg -protoinst add.protoinst
    ```

    That is, we add a `cd /d` command to make the file callable from a different directory, and we change the `tclbatch` file from `scalar_fun.tcl` to `scalar_fun_vcd.tcl`
* Go back to the directory `scalar_fun_vitis` Re-run the simulation with 

```bash
./run_xsim_vcd.bat
```

This will re-run the simulation and create a `dump.vcd` file of the simulation data.



