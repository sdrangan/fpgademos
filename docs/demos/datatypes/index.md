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

In going through this demo, you will learn to:

* Read and write **SystemVerilog** combinational logic with `always_comb`
* Reason about **bit growth**: how wide the result of a multiply really is
* Tell **truncation** from **saturation**, and see what each costs
* Detect **overflow** correctly for signed values — and see why the obvious test
  is wrong
* **Pack and unpack** a data structure with concatenation and part-selects
* Build a **Python golden model**, generate test vectors from it, and confirm
  that the SystemVerilog agrees with it exactly

## Running it

The demo is driven by one script, `datatypes_build.py`, which is organised as a
graph of stages.  You can run it a stage at a time, which is the point:

~~~bash
    cd hwdesign/demos/datatypes

    # what the stages are, and what each one reads and writes
    python datatypes_build.py --list-steps-verbose

    # what has already been built, and what is now out of date
    python datatypes_build.py --status

    # just the Python model — no Vivado needed
    python datatypes_build.py --through int_prod_gen

    # ...then the SystemVerilog simulation
    python datatypes_build.py --through int_prod_sim

    # ...then compare the two
    python datatypes_build.py --through int_prod_check

    # everything, both parts
    python datatypes_build.py
~~~

A stage is skipped when its outputs are already newer than its inputs — you will
see `UP-TO-DATE` instead of `RUNNING`.  To make one run again anyway:

~~~bash
    python datatypes_build.py --force-step int_prod_sim
~~~

Note there is no `--only` flag.  `--through NAME` runs everything *up to* `NAME`,
and stages that are already up to date are skipped, which amounts to the same
thing.

The two parts are separate branches of the graph, so
`--through samp_pack_check` does not touch `int_prod` at all.  That is why this
is a graph and not a list.

## Why there is a Python model at all

Each part is written twice: once in Python and once in SystemVerilog.  The
Python version is the **golden model** — the answer we agree is correct — and
the build compares the two, value for value, over every test vector.

This is how hardware is actually verified, and it is worth getting used to now,
while the thing being verified is a multiply.  In [`int_prod`](./int_prod.md)
the comparison covers all 65,536 input combinations, so "it works" means
something precise.

The two languages also disagree by default in instructive ways, and the demo
points those out as they come up.

---

Go to [the integer product](./int_prod.md).
