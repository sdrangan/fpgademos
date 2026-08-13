---
title: Grading and submission
parent: Pseudorandom Number Generator
nav_order: 5
has_children: false
---

# Grading and submission

## Seeing where you stand

Each stage scores itself as it runs and writes the result to disk, so you can ask
for your standing at any time without rebuilding anything:

```bash
python prng_build.py --grades
```

Every check names itself, says what it is worth, and — when it fails — says why:

```
Python LFSR model: 10/10
  ✓ (4/4) Generated at least 1000 samples
  ✓ (3/3) Values are in range 0 to 255
  ✓ (3/3) The generator does not get stuck
Evaluating the generator: 7/10
  ✓ (2/2) Your lag-1 correlation is correct
  ✗ (0/3) Successive samples are uncorrelated — lag-1 correlation = +0.5042,
          which is 15.9 standard errors from zero — each sample predicts the
          next far too well
  ✓ (3/3) Your histogram is correct
  ✓ (2/2) The histogram is flat
```

This output is the authority on the marking scheme, which is why these pages do
not repeat it — a page can go stale, the build cannot.

A stage you have not run yet shows as `not yet run` and scores zero.

## The build only redoes what changed

The build tracks file timestamps. Edit `prng_model.py` and the Python stage
re-runs — and so do evaluation and simulation, because both work from its output.
Edit only `prng_next.sv` and just the simulation re-runs. Change nothing and every
stage reports `UP-TO-DATE` and does no work.

If you ever want to force everything to run again:

```bash
python prng_build.py --force
```

## Building the submission

`submit` is a build step like any other, and it is the last one in the graph:

```bash
python prng_build.py --through submit
python prng_build.py                     # the same thing — submit is the default
```

Because it is a step, it depends on the three graded stages, so running it runs
whatever is out of date first. There is no separate script to remember and no way
to bundle results without regenerating them.

It writes:

```
submission/submitted_results.json    your scores and feedback
submission/submission.zip            what you upload
```

The zip contains that results file, your four source files,
`vectors/prng_py.csv`, and the histogram you drew in
[stage 2](./evaluate.md). Upload **`submission.zip`** to Gradescope.

Your figure is in there so it can be looked at. Nothing checks what it shows —
only that you produced one — but it is the part of this lab whose quality a
person can judge at a glance and a script cannot judge at all.

{: .warning }
> Gradescope reports the score in the zip you upload. Run the full build after
> your last edit — if you fix something and upload without re-running, you submit
> the old score.

You can submit an unfinished lab. A stage you never ran scores zero and the zip
is still built, so partial work is always submittable.

## What is graded, and what is not

| | |
| --- | --- |
| **Graded** | The numbers your code produces, whether your measurements of them are right, and whether your two implementations agree |
| **Not graded** | Which algorithm you used, your variable names, your style |

Nothing is compared against a stored reference sequence. Any correct PRNG passes
the Python stage, and the SystemVerilog stage checks it against *your* Python
rather than against ours. The write-up pins one algorithm so that nobody has to
guess what to build — not because the grader insists on it.

The one thing this does not let you do is leave both sides unimplemented. Two
untouched placeholders agree with each other perfectly, so a constant stream
scores zero on the comparison no matter how well it matches. See
[the SystemVerilog stage](./sv.md).
