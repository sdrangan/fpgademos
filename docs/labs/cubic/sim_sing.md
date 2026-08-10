---
title: Single Test Case
parent: Cubic Fixed Point
nav_order: 3
has_children: false
---

# Simulating a Single Test Case

## Setting up the Testbench

Before you run through all the test cases, it is useful to
get a single test case working.  For this purpose, I have written a testbench file,
`tb_cubic_sing.sv`.  You can modify it to validate your code with a simple,
configurable test case as follows:

- The testbench instantiates an instance of the module `cubic` as the
**DUT**  (device under test).  You do not need to change this part of the code.
-  At the top of the file, the testbench sets sets a single set of input values
for `x` and `a`.  You can change these values to try different inputs.
But these values are good to start.  In particular, they are small enough
that nothing should saturate.

```
// Test value parameters (real)
localparam real xr_test  = 2.5;
localparam real a0r_test = 1.0;
localparam real a1r_test = -0.5;
localparam real a2r_test = 0.25;
```

- Next, **complete the `TODO` section**:  
This section converts the real values to integers and computes an *expected*
integer and real output from the .  Change the code in the section to match whatever
exact integer operation you used in `cubic`.  

- The testbench takes the the specified input values and drives the DUT with the values.
- In parallel, the testbench monitors the DUT output `y` and any internal signals over about 10 clock cycles.
- The test passes if the output `y` from the DUT matches the expected value.
- The testbench also capture various monitoring of internal signals that are useful to debugging.


## Running the Test

Once you have set up the testbench, you can run the test from the command line using `xilinxutils` function, `sv_sim`:

- Open a terminal in Unix or command window in Windows (On Windows, you cannot use Powershell)
- Activate the virtual environment with the `xilinxutils` package
- Follow the [instructions](../../support/amd/launching.md) to set the path for Vivado tools
- Navigate to the `hwdesign/labs/subc` directory
- Run

```bash
sv_sim --source cubic.sv --tb tb_cubic_sing.sv
```

You should get an output as follows.  
```bash
=== Cubic Fixed Point Testbench ===
Parameters: WID=16, FBITS=8

Test Inputs:
  x  = 0 (2.5000)
  a0 = 0 (1.0000)
  a1 = 0 (-0.5000)
  a2 = 0 (0.2500)

Expected output:
  y  = 4336 (16.9375)

=== Monitoring Internal Signals ===
Cycle | x_s0  | x2_s1  | ax1_s1 | x_s1  | y
------|-------|--------|--------|-------|-------
    0 |     0 |      0 |      0 |     0 |     0
    1 |     0 |      0 |      0 |     0 |     0
    2 |   640 |      0 |      0 |     0 |     0
    3 |   640 |   1600 |    -64 |   640 |  4336
    4 |   640 |   1600 |    -64 |   640 |  4336
    5 |   640 |   1600 |    -64 |   640 |  4336
    6 |   640 |   1600 |    -64 |   640 |  4336
    7 |   640 |   1600 |    -64 |   640 |  4336
    8 |   640 |   1600 |    -64 |   640 |  4336
    9 |   640 |   1600 |    -64 |   640 |  4336

TEST PASSED: Output y matches expected value 4336
```


## Running the Simulation on the NYU Server

If you are on the [NYU server](../../support/nyuremote/),
you should follow the specialized [python instructions](../../support/nyuremote/python.md).
In particular, follow those instructions to:
- log into the server
- clone the repository `hwdesign` to your home directory so it is at `~/hwdesign`
- install the `uv` utility
- create and activate a virtual environment
- install the python package with `uv` in that environment.

Once you have done these steps, you can run the script with

```bash
(hwdesign) uv run sv_sim --source cubic.sv --tb tb_cubic_sing.sv
```

---  

Go to [validate against the test vectors](./test.md).