---
title: Simulation with the Vitis GUI
parent: Root Solver
nav_order: 3
has_children: false
---

# Simulation with the Vitis GUI

## Creating the Vitis Project 

The GUI is a good option if you like a complete graphical
interface where you can easily see the options and manually step
through the process one step at a time.
If you wish to pursue this option, first [launch the Vitis GUI](../../support/amd/launching.md).
Note that if you are on the [NYU server](../../support/nyuremote/),
you will need to open a GUI terminal with [Fast-X connect](../../support/nyuremote/fastx.md).

Once the Vitis GUI is open, 
follow the [instructions](../../support/amd/vitis_build.md) to create a Vitis HLS project
with the following parameters:

Go to **File -> New Component -> HLS** and then select:
- **Project location**:  `hwdesign/labs/rootsolve`
- **Component Name**:  `hls_component`
- **Source Files**:
    * Design Files: Add `fsolve.cpp` 
    * Top Function: `fsolve`
    * Testbench files: Add `tb_solve.cpp`
- **Hardware Part number**:  Follow the [FPGA part number guide](../../support/amd/fpga_part.md).  Even though you do not have to deploy the design in this lab,
you need to select a part.  You can use the FPGA in the `Pynq-Z2` board `xc7z020clg400-1`.
* For **Settings**, set clock rate:  `100MHz` or `10ns`. 


## C Simulation

Once the project is created, our first task it to simualte the IP to ensure **functional correctness**.

* In the **FLOW** panel (left sidebar), select **C Simulation → Run**.   
    * A long simulation will begin.  
    * You will see a large number of outputs.  Within that stream of outputs, you should see
    some print out that the tests passed.  The precise print out will depend on
    how you configured the testbench.

Once the C simulation is complete, the testbench should create an ouptut file in

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

## C Synthesis

Following simulation, we can **synthesize** our design, which means we convert the C/C++ functions into synthesizable RTL (Verilog/VHDL), targeting the specified FPGA part.

Still in the **FLOW** panel, select **C Synthesis → Run**. 
If you are interested, you can see details about the synthesis results
in t **C Synthesis -> Reports -> Synthesis**.  This information describes
various synthesis results like how many FPGA resources are used for the design
along with the number of number of clock cycles per iteration.
We will discuss how to optimize these synthesis results later.

## RTL Co-Simulation

We finally re-simulate the RTL generated in synthsis.

* In the **Flow panel** (left sidebar), find the **C/RTL Simulation** section
* Select the settings (gear box) in the C/RTL Simulation:
    - Set **cosim.argv** to `rtl`.  This argument is passed to the `main()` function
    in the testbench.  For this particular testbench, it is used to create
    the 
* Next select the **C/RTL Simulation->Run**.  This command will execute a RTL-level simulation of the synthesized IP.  


Once the RTL co-simulation is complete, the testbench should create an ouptut file in

```bash
rootsolve/test_ouptus/tv_rtl.csv
```

Similar to the C simulation, you can check that the outputs are correct with


```bash
python run_tests.py --tests rtl
```

---

Once all tests are passed, you can go [submit](./submit.md)








