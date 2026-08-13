---
title: The Python model
parent: Pseudorandom Number Generator
nav_order: 2
has_children: false
---

# Stage 1: the Python model

```bash
python prng_build.py --through pysim
```

Open `prng_model.py`. The constants are already there:

```python
WIDTH = 16                  # bits of LFSR state
MASK = (1 << WIDTH) - 1     # 0xFFFF — what "keeping 16 bits" means
TAPS = 0xD008               # bits 15, 14, 12 and 3
BITS = 8                    # bits per output sample
```

`TAPS` is a bit mask with a 1 in each tapped position. `0xD008` is
`1101 0000 0000 1000` — bits 15, 14, 12 and 3, exactly the taps shaded in the
diagram on [the theory page](./theory.md).

## Your job

Two functions, both with a placeholder `return` to delete.

### `prng_next(state)`

Takes the current 16-bit state, returns the next one — one step, one new bit.

**Getting the XOR of the tapped bits.** `state & TAPS` keeps only the bits you
care about and zeroes the rest. You then need the XOR of all the bits that
survived. The XOR of every bit in a number is the same as the low bit of how many
1s it has, and `bin(w).count("1")` gives you that count.

**Masking.** In SystemVerilog a 16-bit variable is 16 bits and that is that. In
Python an integer has no width, so `state << 1` really is one bit longer than
`state`, and nothing truncates it for you. Without `& MASK` your state grows
forever, drifts away from what the hardware does, and the two will never agree.

### `prng_sample(state)`

Runs `prng_next` `BITS` times and takes the sample from the resulting state.
Returns **both** the new state and the sample — the caller has to carry the state
into the next call, or every sample would start from the same place.

The sample is the low `BITS` bits of the state. `(1 << BITS) - 1` is a mask of
`BITS` ones, which is how you keep just those.

This is the loop you will write again in SystemVerilog, where it looks completely
different and does exactly the same thing.

## What is given

`lfsr_stream(seed, nsamp)` calls `prng_sample` `nsamp` times, carrying the state
along, and returns a NumPy array. The build script calls it and writes the result
to `vectors/prng_py.csv`.

You can also run the file directly while you work, to see the first ten samples
without going through the build:

```bash
python prng_model.py
```

## What is checked

This stage asks only whether your stream is **well formed**: that you produced
enough samples, that they fit in `BITS` bits, and that the generator is actually
moving rather than stuck on one value.

Whether the stream is any *good* is a different question, and it is the next
stage that asks it — with measuring code you write yourself. See
[Evaluating before you build](./evaluate.md).

Nothing here compares you against a reference sequence. Any correct PRNG passes.
The lab pins one algorithm so nobody has to guess, but the grading asks whether
your numbers are right, not whether they came from a particular recurrence.

Run `python prng_build.py --grades` to see your score and the reason for it.

## If something is not working

**Every sample is 0.** Either you have not removed the `return 0` placeholder, or
your feedback is always coming out 0. Remember zero is a fixed point.

**Values above 255.** `prng_sample` takes the low `BITS` bits, so this almost
always means your state is growing — the missing `& MASK`.

**The histogram has a hard staircase.** Your sequence is probably a counter, not
an LFSR. Check that the feedback actually depends on `state`.

**A short repeating pattern.** Your taps are not the ones above, or the shift is
going the wrong way. A primitive polynomial gives you 65535 states before
repeating; a bad tap set can cycle in a handful.

----

Go to [evaluating your generator](./evaluate.md)
