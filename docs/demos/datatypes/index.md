---
title: Integers, Overflow and Bit Packing
parent: Demos
nav_order: 1
has_children: true
---

# Integers, Overflow and Bit Packing

This is the first demo of the class, and the first SystemVerilog you will see.
Everything in it is **combinational** — no clock, no reset, no registers.  Those
arrive in the next unit; here the only question is what a circuit computes, not
when it computes it.

All the code is in

~~~bash
    hwdesign/demos/datatypes
~~~

There are two parts, and they are independent:

* [**`int_prod`**](./int_prod.md) — multiply two signed 8-bit numbers and look at
  what happens to the answer when you only keep 8 bits of it.
* [**`samp_pack`**](./samp_pack.md) — pack a timestamped complex sample into a
  single 32-bit word and take it apart again, the way a real sample stream is
  carried over a bus.

Two ideas run through both, and each has a page of its own:

* [**Running the demo in steps**](./steps.md) — real designs are built in stages,
  and this class drives those stages with Waveflow's `BuildDag`.
* [**The Python golden model**](./python.md) — every part is written twice, and
  the Python version is the definition of the right answer.

In going through this demo, you will learn to:

* Read and write **SystemVerilog** combinational logic with `always_comb`
* Reason about **bit growth**: how wide the result of a multiply really is
* Tell **truncation** from **saturation**, and see what each costs
* Detect **overflow** correctly for signed values — and see why the obvious test
  is wrong
* **Pack and unpack** a data structure with concatenation and part-selects
* Build a **Python golden model**, generate test vectors from it, and confirm
  that the SystemVerilog agrees with it exactly

## Getting started

Everything is driven by one script:

~~~bash
    cd hwdesign/demos/datatypes
    python datatypes_build.py --list-steps-verbose
~~~

That prints the stages the demo is built from.  [Running the demo in
steps](./steps.md) explains what those stages are and how to walk through them
one at a time — including how to run the Python half on a machine with no Vivado
installed.

---

Go to [running the demo in steps](./steps.md).
