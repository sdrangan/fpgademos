---
title: Pseudorandom Number Generator
parent: Labs
nav_order: 1
has_children: true
---

# Unit 1 Lab: A pseudorandom number generator

## Overview

Random number generators appear in myriad applications in hardware including statistical sampling, simulations, cryptography, built-in self-test -- anywhere where randomness is needed.  
In this lab, you will build a  [**linear-feedback shift register**](https://en.wikipedia.org/wiki/Linear-feedback_shift_register) — an LFSR — one of the most common circuits for generating a pseudo-random sequence of random bits.  The benefit of the LFSR is that it is extremely hardware efficient - it can be built from simple bitwise operations avoid more costly multiplications or other complex mathematical operations.

## Learning Objectives

In going through this lab, you will learn to:

- Model a simple iterative algorithm with **bitwise operations** in python
- **Evaluate** the performance of the algorithm in python prior to starting the hardware implementation
- Implement the update step of the algorithm via **combinational logic** in SystemVerilog
- Create a SystemVerilog **testbench** that includes the hardware module as a **device under test** (DUT) and iteratively calls the update steps
- **Functionally verify** the behavior of the DUT against test vectors from the python **Golden model**

Note that in a real hardware system, the iterations can also be performed in the synthesized hardware via what is called *sequential logic* that uses a *clock* and *registers*.  We will cover sequential logic in Unit 2.  In this lab, the iterations will be performed in the testbench.

## Files

The files for the lab can be found in the hwdesign github repo

```
hwdesign/
└── labs/
    └── prng/
        ├── prng_build.py         # Runs the build steps and scores them
        ├── partial/
        │   ├── prng_model.py     # Python model of the generator
        │   ├── prng_eval.py      # Python measurements of the generated stream
        │   ├── prng_next.sv      # SystemVerilog module: one step of the LFSR
        │   └── tb_prng.sv        # Testbench that drives the module
        ├── vectors/              # These directories are created by the build
        ├── results/              #   generated data, figures, scores and
        ├── eval/                 #   simulator output -- none of it is edited
        ├── sim/                  #   by hand, and none of it is submitted
        └── submission/           #   except the zip
```

The four files in the `partial` directory are not complete. You will finish
them as part of the lab, and each has `TODO` comments marking what to write:

| File | What you write |
| --- | --- |
| `prng_model.py` | `prng_next()` — one step of the LFSR, and `prng_sample()` — the loop that turns `BITS` steps into one sample |
| `prng_eval.py` | `lag1_correlation()` and `histogram()` — the measurements you use to judge your own design |
| `prng_next.sv` | One `always_comb` block: the same step, in hardware |
| `tb_prng.sv` | The loop that drives that module `BITS` times per sample |

**You do not need to copy anything by hand.** The first time you run the build it
copies each file out of `partial/` into the lab directory and tells you it has
done so:

```
prng_model.py:
    STARTED prng_model.py from partial\prng_model.py — edit prng_model.py,
    not the copy in partial/.
pysim:
    Python LFSR model: 0/10
      · (0/10) not started — prng_model.py is still unchanged from the template.
          Open it, look for the TODO comments, and run this again.
```

A stage whose files you have not touched yet says **not started** rather than
listing failed checks. That is not the same as getting it wrong, and the build
does not pretend otherwise — you will see real check-by-check feedback as soon as
there is real work to check.

Edit the copies at the top level, *not* the ones in `partial/`. The build never
overwrites your work once the top-level files exist — not even with `--force` —
which is what keeps a `git pull`, or a stray rebuild, from destroying an
afternoon.

`prng_build.py` is given and should not be modified. It is worth reading: it is
the script that decides your score, so nothing about the marking is hidden from
you.

## Build steps

In order that the lab can be executed incrementally in parts, we will use the Waveflow package's [Build DAG](https://sdrangan.github.io/waveflow/docs/guide/build/).  For this lab, the lab is executed in three *build steps*.  In each step, you will modify one of the files, and then run one of the following build steps.  The build steps will provide a score and feedback.  You can modify your code as many times as you like until you get a perfect score.  In the final step, you will create a submission for Gradescope.


| Stage | Command | What it asks |
| --- | --- | --- |
| `pysim` | `python prng_build.py --through pysim` | Does your Python generate a well-formed stream? |
| `pyeval` | `python prng_build.py --through pyeval` | Is that stream actually random — and can you show it? |
| `svsim` | `python prng_build.py --through svsim` | Does your SystemVerilog agree with your Python? |
| `submit` | `python prng_build.py --through submit` | Collects the three scores and builds the Gradescope zip |


Importantly, observe that you evaluate the design in Python **before** you build it in hardware. That is
not busywork and it is not the order most people reach for; see
[Evaluating before you build](./evaluate.md).

The full set of commands:

```bash
python prng_build.py --list-steps-verbose   # what the stages are
python prng_build.py --through pysim        # generate the stream, scored
python prng_build.py --through pyeval       # measure it, scored
python prng_build.py --through svsim        # the SystemVerilog, scored
python prng_build.py                        # everything, then the submission zip
python prng_build.py --grades               # your scores, without rebuilding
```

Each stage prints its score and the reason for it as soon as it runs. A low score
does not stop the build — you can keep going to the next stage and come back, and
you can re-run a stage as many times as you like.

The build only redoes what changed. Edit `prng_model.py` and every stage re-runs,
because they all work from its output; edit only `prng_next.sv` and just the
simulation does. Change nothing and each stage reports `UP-TO-DATE` and does no
work at all.

## Pages

* [Theory: how an LFSR works](./theory.md)
* [The Python model](./python.md)
* [Evaluating before you build](./evaluate.md)
* [The SystemVerilog](./sv.md)
* [Grading and submission](./submit.md)

----

Go to [the theory](./theory.md)
