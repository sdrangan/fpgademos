---
title: Multiple Test Cases
parent: Cubic Fixed Point
nav_order: 4
has_children: false
---

# Testing Against the Python Model

Once you have the module passing a single test,
we can run the test the module against the test vectors generated from the python
golden module.  We will use the testbench in `tb_cubic.sv`. 
This file will read the test vector inputs, instantiate your module as a DUT, run the inputs through your DUT module and compare the DUT outputs with the outputs from the python golden model.

At the beginning of the testbench file you will see:

```
module tb_cubic;

    // Parameters
    localparam int WID = 16;
    localparam int FBITS = 8;
    ...
```


Change `FBITS=8` or `FBITS=12` as needed.  I would first test `FBITS=8` since this test case is easier to match.  Once you have selected the correct parameters,  the testbench can be run by using the `xilinxutils` function:

- Open a terminal in Unix or command window in Windows (On Windows, you cannot use Powershell)
- Activate the virtual environment with the `xilinxutils` package
- Follow the [instructions](../../support/amd/launching.md) to set the path for Vivado tools
- Navigate to the `hwdesign/labs/subc` directory
- Run

```bash
sv_sim --source cubic.sv --tb tb_cubic.sv
```

This will run the three steps in synthesizing and simulating the SV mdule.  The outputs will be stored in a CSV file, `test_outputs/tv_w16_f8_sv.csv`
or `test_outputs/tv_w16_f12_sv.csv` depending on the choice of `FBITS`.
You should see how many tests passed, and you can keep modifying the SV code until all test passed.

You can also follow the specialized [python instructions](../../support/nyuremote/python.md)
for running the the tests on the [NYU server](../../support/nyuremote/).

## Verify the test outputs

Once you have the tests passing, you can run the program:

```bash
python run_tests --tests sv_f8 
python run_tests --tests sv_f12 
```

These commands will tests that the test vectors match.

If you are running Vitis and Vivado on the [NYU machine](../../support/nyuremote/),
you will need to follow the instructions for [setting up uv](../../support/nyuremote/python.md).
Then, activate the `hwdesign` virtual environment and run:

```bash
uv run python run_tests --tests sv_f8 
un run python run_tests --tests sv_f12 
```


Go to [submission](./submit.md)