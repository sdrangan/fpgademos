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

## The two files, and why there are two

Hardware is almost always written as a pair: the thing you are building, and a
separate program that exercises it.

**`prng_next.sv` is the design under test — the DUT.** It is the hardware. Every
line in it has to be something that could become real logic on a chip: gates,
wires, registers. Nothing in it reads files, prints, or waits for a while.

**`tb_prng.sv` is the testbench.** It is not hardware and is never synthesised.
Its whole job is to *drive* the DUT — make up inputs, apply them, look at what
comes out, and write the results somewhere you can check them. Because it never
becomes a circuit, it can do things hardware cannot: open files, print, and take
an arbitrary number of steps in an `initial` block.

The relationship is the same one you already have in Python. `prng_next()` is the
algorithm; `lfsr_stream()` is the harness that calls it repeatedly and collects
the answers. Here `prng_next` is the module and the testbench is the harness.

In this lab the DUT is *one step* of the LFSR and the testbench does the
iterating — it calls the DUT `BITS` times per sample, feeding each output back in
as the next input. That split is deliberate. Iterating inside the hardware needs
a clock and registers, which is **sequential logic**, and that is Unit 2. Once
you have it, the same generator becomes a module that advances itself once per
clock edge and the testbench shrinks to almost nothing.

So for now: everything that repeats lives in the testbench, and the DUT is pure
combinational logic that computes one answer from one input.

## The state update, in `prng_next.sv`

You get the module's shell. The ports and the body are yours:

```systemverilog
module prng_next #(
    parameter int WIDTH = 16,
    parameter logic [15:0] TAPS = 16'hD008
)(
    // your port declarations here
);

    always_comb begin
        // your one line here
    end

endmodule
```

Purely combinational — no `always_ff`, no clock, no reset, no state of its own.
It is a function written in hardware: give it a state, it gives you the next one.
The sequencing lives in the testbench.

### Declaring the ports

A module's port list is its interface: the wires that cross the boundary between
this block and whatever instantiates it. Each one needs three things — a
**direction**, a **type**, and a **width**:

```systemverilog
    direction  type  [range]  name
```

You need two ports. The testbench drives one and reads the other, so one is an
`input` and one is an `output`. Both carry a whole LFSR state, so both are
`WIDTH` bits wide — write the range in terms of `WIDTH` rather than as `[15:0]`,
so that changing the parameter changes the ports with it.

Ports are separated by commas, with no comma after the last one. The names have
to be the ones the testbench already uses; look at how it instantiates the module
and you will find them.

{: .note }
> Getting a width wrong here does not usually produce an error. SystemVerilog
> will happily connect a 16-bit signal to an 8-bit port and quietly discard the
> top half. It is the same silent truncation as the discarded product in the
> [datatypes demo](../../demos/datatypes/), and it is why widths are worth
> checking by hand rather than trusting.

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

## Running the simulator yourself

`prng_build.py` calls the simulator for you through a Waveflow helper,
`run_sv_sim`. That helper does nothing magic — it shells out to three Vivado
command-line tools in a scratch directory and raises an error if any of them
exits non-zero.

It is worth doing by hand at least once. Waveflow is this course's convenience,
not an industry standard; nobody at your next job will have heard of it. The
tools underneath are the ones everybody uses, and being able to drive them
directly is what lets you debug when a script does something you did not expect.

### The three commands

From the lab directory:

```powershell
# Put the Vivado tools on PATH for this shell (adjust for your install)
$env:PATH = "C:\Xilinx\2025.1\Vivado\bin;$env:PATH"

mkdir sim\manual\logs -Force
cd sim\manual

# 1. Compile: parse the SystemVerilog into a library called `work`
xvlog -sv ..\..\prng_next.sv ..\..\tb_prng.sv

# 2. Elaborate: link the modules into a runnable snapshot named tb_prng_sim
xelab tb_prng -s tb_prng_sim -debug typical -log logs/xelab.log

# 3. Run it, passing the values the testbench reads with $value$plusargs
xsim --% tb_prng_sim --runall -log logs/xsim.log -testplusarg "vecdir=." -testplusarg "nsamp=1000" -testplusarg "seed=45242"
```

You should see the first eight samples printed and `prng_sv.csv` written into the
directory you ran from.

The three steps map onto compiling a C program: `xvlog` is the compiler,
`xelab` is the linker, and `xsim` runs the resulting binary. `tb_prng` is named
in step 2 because the *testbench* is the top of the hierarchy — it instantiates
the DUT, not the other way round.

{: .note }
> The `--%` in the `xsim` line is PowerShell's stop-parsing token, and without it
> the `-testplusarg "name=value"` pairs are mangled before the tool ever sees
> them. On Linux, macOS, or in `cmd`, drop it. `45242` is `0xB0BA`, the seed —
> `$value$plusargs("seed=%d", ...)` reads decimal.

### What Waveflow adds

Nothing you could not type. It resolves where the Vivado binaries live so you do
not have to source `settings64`, makes and cleans the scratch directory, converts
path plusargs to forward slashes (a Windows backslash arrives at
`$value$plusargs` with `\r` read as a carriage return), checks that the testbench
actually wrote the files it promised, and raises with the log path when a step
fails.

That last one matters more than it sounds: **xsim exits 0 even after `$fatal`**.
A testbench that could not open its input file will report success to the shell.
Anything driving these tools from a script has to check the outputs rather than
the exit code — which is a thing worth knowing whatever tooling you end up using.

Once a design gets past a few files, everyone automates this. The wrapper is a
Makefile, a TCL script, or a Python harness depending on the shop, but the three
commands underneath are the same ones above.

---

Go to [grading and submission](./submit.md)
