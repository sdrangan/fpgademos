---
title: Cubic Fixed Point
parent: Labs
nav_order: 3
has_children: true
---

# Fixed Point Cubic Polynomial

In this lab, you’ll build a simple fixed point implementation of a monic cubic polynomial

```python
    y = a0 + a1*x + a2*(x**2) + x**3
```

We will build the function first in floating point and then compare to fixed point.
The lab follows closely the [demo](../../demos/fixp/) on implementing a fixed point 
linear function.  In particular, you will learn to:

In going through the lab, you will learn how to:

* Implement and simulate a **fixed‑point** version of a nonlinear function in Python  
* Measure the **approximation error** introduced by fixed‑point quantization 
* Generate **test vectors** from a Python **golden model** of the fixed‑point function  
* Implement the same fixed‑point function in SystemVerilog and **validate** the RTL against the golden test vectors  


## Getting started

The files in the lab can be found in the hwdesign github repo   

```
hwdesign/
└── labs/
    └── cubic/
        ├── run_tests.py         # Runs unit tests and creates the submission
        ├── tb_cubic.sv          # Test bench for the SV implementation 
        ├── partial/
        │   ├── cubic.ipynb      # Notebook for the python implementation
        │   ├── cubic.sv         # SystemVerilog implementation
        │   └── tb_cubic_sing.sv      # SystemVerilog testbench for a single test case
        └── test_outputs/        # This directory will be created
``` 

The files in the `partial` directory are not complete.  You will complete these as part of the lab.
No other files should be modified.  

Before starting, copy the files in the `cubic\partial` directory into the `cubic` directory.

----

Go to [python implementation](python.md)

