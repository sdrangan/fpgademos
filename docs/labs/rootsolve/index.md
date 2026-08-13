---
title: Root Solver
parent: Labs
nav_order: 4
has_children: true
---

# Vitis HLS Implementation of a Root Solver

In this lab, we will build a simple hardware accelerator
to find roots for a nonlinear function.  The problem we consider
is to the **roots** of a function `f(x)`, meaning we want to find
an `x_root` such that `f(x_root) ~= 0`.  We will use a simple Euler
iteration: 

```
   x[k+1] = x[k] - step*f(x[k])
```

When `f(x) > 0` and `step` is sufficiently small, it can be shown that
`x[k] -> x_root`, some root of the `f(x)` assuming one exists.
In this lab, we will build a simple Vitis IP that:

- take parameters of the function `f(x)` along with parameters for the Euler descent via an AXI4-Lite interface
- runs the Euler iteration and provides the ouptut `x_root` and `f(x_root)`.

In going through the lab, you will learn to:

- Create a floating point python, **golden model** for an iterative algorithm 
- Create a **Vitis HLS IP** for the iterative algorithm with an **AXI4-Lite interface** 
- Implement logic with a **loop** within the accelerator
- Run **C simulation** and **RTL co-simulation** on the Vitis HLS IP
- Compare the outputs to the python Golden model


