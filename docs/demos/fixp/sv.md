---
title: System Verilog Implementation
parent: Fixed Point Design
nav_order: 2
has_children: false
---

# SystemVerilog Implementation and Verification

## SV Implementation

The SystemVerilog implementation can be found in 

```
hwdesign/demos/fixp/piecewise.sv
```

## Verification against the Python Golden model

You can see that there is a natural mapping from the
python model to the SystemVerilog code.

The testbench is in:

```
hwdesign/demos/fixp/tb_piecewise.sv
```

The function reads the testbench vectors generated
from the python code and compares the results with the SV model.

You can run the testbench with:

- Open a command terminal on Windows or Linux
   - On Windows, do not use a power shell
- [Activate](../../support/repo/package.md) the hwdesign virtual environment
- [Set the path for the Vivado command line tools](../../support/amd/lauching.md)
- Navigate to `hwdesign/demos/fixp`
- In the command terminal run

```bash
sv_sim --source piecewise.sv --tb piecewise_tb.sv
``` 

You should see that all the results pass