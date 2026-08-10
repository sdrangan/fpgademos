---
title: System Verilog Implementation
parent: Conditional Subtraction Division
nav_order: 3
has_children: false
---

# System Verilog Implementation

## Handshaking protocol

We now move to implementing the module in SystemVerilog.
A skeleton for the conditional subtraction divider module is in the file `subc_divide.sv`.  Since the operation can take a variable number of clock cycles, it is useful
to implement the transfer of inputs and outputs with a **handshaking protocol** with the following signals:  For the inputs to the module, we use the two signals:

* `output inready`:  Indicates that the module is ready for the next set of inputs, `a`, `b` and `nbits`
* `input invalid`:  Set to indicate that there are valid data values for `a`, `b`, and `nbits`.   The module will start the processing of the data when `inready=invalid=1`.

For the outputs from the module, we use the two signals:

* `output outvalid`:  Indicates that the module processing is complete and a valid output `z` is available.
* `input outready`:  Indicates to the module, that the data is ready to be accepted.  The module will consider the data as transferred when  `outready=outvalid=1`.

## State machine

We can manage the handshaking protocol in the module by using three states:

* `IDLE`:  Waiting for inputs.  
    - In this state, the module outputs `inready=1` and `outvalid=0`.  
    - The module waits until the signal `invalid=1`.  
    - When `invalid=1`, the inputs `a`, `b`, and `nbits` should be registered to the internal registers and the module should move to the state `RUN`.
* `RUN`:  The module is performing the division over multiple iterations.
    - You can use the variable `count` for the iteration number and stop after the correct number of iterations.
    - While running, `inready=0` and `outvalid=0`
    - After completing the `nbits` iterations, the module should move to `DONE`.
* `DONE`:  The results are ready.  
    - The module asserts `outvalid=1` and `inready=0` to indicate the resutls are ready, and `inready=0` to indicate that it is not ready yet for new inputs.
    - When the signal `outready=1` the module assumes the outputs have been read,
    and moves to the `IDLE` state in the next iteration.


## Completing and testing the code
Use the states to complete the section marked `TODO` in `subc_divide.sv`.
Then, when you are complete, I have created a testbench in `tb_subc_divide.sv`.
The testbench:

- Reads the `test_vectors/tv_python.csv` files with the test inputs `a`, `b`, `nbits` and outputs `z` from the Golden python model
- Runs each input to the SV module and gets the output `z`
- Compares the `z` from the python golden model with the implementation
- Writes the results to a file `test_vectors/tv_sv.csv`

The testbench can be run by using the `xilinxutils` function (if you are running the
code on the NYU server, go to the next section):
- Open a terminal in Unix or command window in Windows (On Windows, you cannot use Powershell)
- Activate the virtual environment with the `xilinxutils` package
- Follow the [instructions](../../support/amd/launching.md) to set the path for Vivado tools
- Navigate to the `hwdesign/labs/subc` directory
- Run

```bash
sv_sim --source subc_divide.sv --tb tb_subc_divide.sv
```

This will run the three steps in synthesizing and simulating the SV mdule.  The outputs will be stored in a CSV file, `test_outputs/tv_sv.csv`.

You should see how many tests passed, and you can keep modifying the SV code until all test passed.
I suggest that you modify the testbench to get more visibility until you pass the tests.

## Running the Simulation on the NYU Server

Note that if you are on the [NYU server](../../support/nyuremote/),
you should follow the specialized [python instructions](../../support/nyuremote/python.md).
In particular, follow those instructions to:
- log into the server
- clone the repository `hwdesign` to your home directory so it is at `~/hwdesign`
- install the `uv` utility
- create and activate a virtual environment
- install the python package with `uv` in that environment.

Once you have done these steps, you can run the script with

```bash
(hwdesign) uv run sv_sim --source subc_divide.sv --tb tb_subc_divide.sv
```

## Running the Simulation with the Vivado GUI

The above flow uses command line only.  If you prefer,
you can follow the [instructions for using the Vivado GUI](../../support/amd/sv_build.md).
Running the GUI will create the same files.  You can also edit your
SystemVerilog files in the Vivado editor.

---

Go to [submission](./submit.md)