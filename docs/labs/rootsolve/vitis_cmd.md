---
title: Simulation from the Command Line
parent: Root Solver
nav_order: 4
has_children: false
---

# Simulation using the Command Line

## TCL File

Instead of running Vitis from the GUI, you can run all the
functions from the command line.  This method does not require
a GUI interface and is easier to automate.  When running from the command
line, it is useful to include a **TCL file** that provides configurations
and the instruction sequence to run.  For this lab, I have included the TCL file `run_hls.tcl`.   The file commands are:

```tcl
# Create or reset the project
open_project hls_component -reset

# Set the top-level function
set_top fsolve

# Add design and testbench filess
add_files src/fsolve.cpp
add_files -tb tb/tb_solve.cpp

# Create solution
open_solution "solution1" -reset

# FPGA part (Pynq-Z2)
set_part {xc7z020clg400-1}

# Clock: 100 MHz = 10 ns
create_clock -period 10 -name default

# ------------------------------------------------------------
# C Simulation
# ------------------------------------------------------------
csim_design

# ------------------------------------------------------------
# C Synthesis
# ------------------------------------------------------------
csynth_design

# ------------------------------------------------------------
# RTL Co-Simulation
# Pass argument "rtl" to testbench via cosim.argv
# ------------------------------------------------------------
cosim_design -argv "rtl"
```

You can adjust the file as you need.  I would suggest:

- Intially comment out the last two steps `csynth_design` and `cosim_design`.
That way you can first make sure the C-simulation works.
- Once that is working, uncomment the two steps so all the steps are run.


## Running the Vitis Command Line

We are now ready to run the C simulation and/or RTL simulation from
the command line.  You should follow the [instructions](../../support/amd/launching.md).

* Open a terminal:
    - In Windows, open a Command Shell, not a Powershell.  
    - In Linux, open any terminal.
* Next, set the paths to enable the Vitis command line tools: If you are on the [NYU remote server](../../support/nyuremote/), you can skip this step since the server accounts
have been configured to have the correct paths by default.
    - Find the path the Vitis for the version you want to use:
        * On Linux, it is likely in `/tools/Xilinx/Vitis/2025.1`  
        * On Windows, is is likely in `c:\Xilinx\2025.1\Vitis`
    - Run the settings command:
        * On Linux: `source <vitis_path>/settings64.sh`
        * On Windows: `<vitis_path>/settings64.bat` 
*  Now run the Vitis command.  The command will depend on the version that you are using:

    - If you are using Vitis 2025.1 or later (the recommended version if you installed Vitis HLS on your local machine), the command is:

    ```bash
    vitis-run --mode hls --tcl run_hls.tcl
    ```

    - If you are running on the [NYU remote server](../../support/nyuremote/),
    the server has an older 2023.2 version.  In this case, the command syntax is:

    ```bash
    vitis_hls -f run_hls.tcl
    ```

## Checking the Test Outputs 

When you run the C simulation, you should see that the three tests passed.

As in the [Vitis GUI version](./vitis_gui.md), running the C simulation
will create a CSV file:

```bash
rootsolve/test_ouptus/tv_csim.csv
```

This CSV file has the inputs for each test case, the expected values from the Python model,
and the outputs from the simulated device under test or DUT.  In our case, the DUT
is the Vitis HLS IP.  The results will not exactly match since the floating point
computations are not exactly the same in Python vs. Vitis HLS.  But they should be close.

If you run 

```bash
python run_tests.py --tests csim
```

it will verify that your test outputs are corrrect.

Similarly, the RTL Co-Simulation will generate an output file:

```bash
rootsolve/test_ouptus/tv_rtl.csv
```

and you can verify that the results are correct with:

```bash
python run_tests.py --tests rtl
```

---

Once all tests are passed, you can go [submit](./submit.md)








