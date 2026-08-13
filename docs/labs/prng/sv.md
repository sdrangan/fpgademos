---
title: The SystemVerilog
parent: Pseudorandom Number Generator
nav_order: 4
has_children: false
---

# Stage 3: the SystemVerilog

```bash
python prng_build.py --through svsim
```

You write two things here: the state update in `prng_next.sv`, and the loop in
`tb_prng.sv` that turns single-bit steps into whole samples. The stage then runs
the simulation and compares its output with **your own** Python model, sample for
sample — the two languages have to agree.

## The state update, in `prng_next.sv`

`prng_next.sv` is a module with two ports and no clock:

```systemverilog
module prng_next #(
    parameter int WIDTH = 16,
    parameter logic [15:0] TAPS = 16'hD008
)(
    input  logic [WIDTH-1:0] state_in,
    output logic [WIDTH-1:0] state_out
);

    always_comb begin
        // your one line here
    end

endmodule
```

Purely combinational — no `always_ff`, no clock, no reset, no state of its own.
It is a function written in hardware: give it a state, it gives you the next one.
The sequencing lives in the testbench.

### Two operators you need

**Reduction XOR.** Applied to a vector, unary `^` XORs together *every bit* of
its operand and gives back a single bit:

```systemverilog
logic [7:0] w;
logic       parity;
assign parity = ^w;      // w[7] ^ w[6] ^ w[5] ^ ... ^ w[0]
```

This is not the same as the binary `^` you use between two values. It is the
reason the feedback needs no explicit chain of XORs: `^(state_in & TAPS)` masks
off everything but the taps and then XORs what is left.

**Concatenation.** `{a, b}` builds a wider vector by gluing pieces together, most
significant first. That is how you write a shift:

```systemverilog
{state_in[WIDTH-2:0], new_bit}    // drop the top bit, append new_bit at the bottom
```

Count the width: `WIDTH-1` bits plus 1 bit is `WIDTH` bits, so this fits
`state_out` exactly. Getting that count wrong is the usual way to lose a bit
silently — the same trap as the truncated product in the
[datatypes demo](../../demos/datatypes/).

## The sample loop, in `tb_prng.sv`

The second thing you write. `prng_next` advances the state by one bit; something
has to run it `BITS` times to build a whole sample, and that something is the
testbench. It is the same loop you wrote as `prng_sample` in Python.

```systemverilog
for (k = 0; k < BITS; k++) begin
    state_in = state;
    #1;                 // let the combinational logic settle
    state = state_out;
end
sample = ...
```

**The `#1` is not optional.** `prng_next` is combinational, so `state_out` only
reflects a new `state_in` after the simulator has advanced time. Leave it out and
you read the previous value on every pass, and the generator never moves. This is
the difference between a function call and a piece of hardware: the hardware does
not compute the moment you assign to its input, it computes *shortly after*, and
in a testbench you have to say how long to wait.

`sample` is `BITS` wide and `state` is `WIDTH` wide, so taking the low bits is a
part-select: `state[BITS-1:0]`.

## What is given

Everything else in `tb_prng.sv`: it reads the seed, sample count and output
directory as plusargs, instantiates your `prng_next`, runs the outer loop over
samples, and writes `vectors/prng_sv.csv`.

There is also a watchdog, which is worth stealing for your own testbenches:

```systemverilog
initial begin
    #10_000_000;
    $display("FATAL: still running after 10 ms of simulated time.");
    $fatal(1);
end
```

A loop with the wrong bound runs forever, and a simulator that never returns
looks exactly like a simulator that is working hard. This turns a hang into an
error message.

## What is checked

Your SystemVerilog against **your** Python model, sample for sample, with partial
credit for a partial match.

When they disagree, the feedback names the first sample that differs and what
each side said. That is usually enough — if sample 0 already differs, your update
is wrong; if the streams run together for a while and then split, suspect a width
or a wrap.

Two things score zero regardless of matching:

- **The simulation did not run.** A syntax error or an elaboration failure is a
  zero with the tool output attached, not a crashed build. You can still submit.
- **Your Python model produced a constant stream.** Every file starts with a
  placeholder that returns 0, and two placeholders agree with each other
  perfectly while implementing nothing. Matching a constant proves nothing, so it
  earns nothing. Fix `prng_model.py` first.

Note what this stage does *not* check: whether the thing you built is any good.
Two implementations can agree perfectly and both be wrong — which is exactly why
[the evaluation stage](./evaluate.md) comes before this one.

----

Go to [grading and submission](./submit.md)
