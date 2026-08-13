---
title: Conditional Subtraction Division
parent: Labs
nav_order: 2
has_children: true
---

# Division by Conditional Subtraction

In this lab, you’ll build a small hardware block that performs division using only shifting and subtraction—exactly the kind of logic real processors fall back on when a native floating‑point divider isn’t available. Many microcontrollers, DSP engines, and custom accelerators avoid full floating‑point hardware because it’s large, slow, and power‑hungry, so they rely instead on compact integer circuits that construct the quotient bit‑by‑bit. By implementing this approach yourself, you’ll see how a division operation can be realized with simple, synthesizable building blocks and gain a clearer sense of what actually happens underneath the “/” operator that software makes look effortless.

In going through the lab, you will learn how to:

* Build a python **golden model** for a simple mathematical hardware IP
* Generate and store **test vectors** from the golden model
* Implement a hardware module in SystemVerilog with that performs algorithms over multiple **iterations**
* Implement a **handshaking** protocol between a testbench module and the device under test.
* **Verify** results of the hardware module with the test vectors.

## Getting started

The files in the lab can be found in the hwdesign github repo   

```
hwdesign/
└── labs/
    └── subc/
        ├── tb_subc_divide.sv        # Testbench for SystemVerilog implementation
        ├── test_subc_divide.py      # Unit tests for Python implementation
        ├── submit.py                # Creates the final submission
        ├── partial/
        │   ├── subc_divide.py       # Python implementation
        │   └── subc_divide.sv       # SystemVerilog implementation
        └── test_outputs/            # This directory will be created
``` 

The files in the `partial` directory are not complete.  You will complete these as part of the lab.
No other files should be modified.  In particular, I have provided the testbenches completely so
you can test if you are getting the correct results.  But, do study these files to understand
how to write testbenches yourself.

Before starting, copy the files in the `subc\partial` directory into the `subc` directory.

----

Go to [algorithm theory](theory.md)

