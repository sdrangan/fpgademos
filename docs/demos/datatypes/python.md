---
title: The Python Golden Model
parent: Integers, Overflow and Bit Packing
nav_order: 3
has_children: false
---

# The Python Golden Model

Every part of this demo is written **twice**: once in Python, once in
SystemVerilog.  That sounds like duplicated effort, and it is the single most
important habit in this class.

The Python version is the **golden model**.  It is not a sketch, or a prototype
you throw away once the RTL works — it is the definition of the right answer, and
it stays for the life of the design.  When the hardware and the model disagree,
the model is what says which one is wrong.

## Why write it at all

The obvious objection is that you now have two things to keep correct instead of
one.  Three reasons it is worth it anyway.

**You can be sure the hardware is right.**  Not "it looked right on the cases I
tried" — actually right.  In [`int_prod`](./int_prod.md) the model and the RTL
are compared on all 65,536 possible inputs.  There is no untested corner because
there is no corner left.

**You can design before you build.**  Choosing between truncation and saturation
is a real decision with real cost, and you want to make it by looking at the
distortion each one causes — not after a day of writing RTL for whichever you
guessed.  A Python model answers that question in seconds.  Unit 3 leans on this
heavily, when the question becomes how many fractional bits a filter needs.

**It survives the design.**  RTL gets rewritten — pipelined, retimed, split
across clock domains, ported to a different device.  Each rewrite has to produce
the same numbers, and the golden model is what proves it did.  A model written
for a Unit 1 demo would still be checking the design three redesigns later.

## What a golden model looks like

Here is the whole of the `int_prod` model:

~~~python
def wrap(value, width):
    """Reduce value to width bits, two's complement — what truncation does."""
    mask = (1 << width) - 1
    out = np.asarray(value) & mask
    return np.where(out >= 1 << (width - 1), out - (1 << width), out)


def saturate(value, width):
    """Clamp value into the signed width-bit range — the other response to overflow."""
    lo, hi = -(1 << (width - 1)), (1 << (width - 1)) - 1
    return np.clip(value, lo, hi)


def int_prod_model(a, b, width=8):
    """Every output of int_prod.sv, computed in Python at full precision first."""
    prod = np.asarray(a, dtype=np.int64) * np.asarray(b, dtype=np.int64)
    trunc = wrap(prod, width)
    return {
        "prod": prod,
        "hi": (prod >> width) & ((1 << width) - 1),
        "lo": prod & ((1 << width) - 1),
        "trunc": trunc,
        "sat": saturate(prod, width),
        "overflow": (prod != trunc).astype(np.int64),
        "hi_nonzero": (((prod >> width) & ((1 << width) - 1)) != 0).astype(np.int64),
    }
~~~

Three things about how this is written are worth copying.

**Compute at full precision first, then reduce.**  `prod` is a full-width product
with nothing thrown away, and `trunc` and `sat` are both derived *from it*.  The
model never loses information by accident — every loss is an explicit step you
can point at.  This is the opposite of what SystemVerilog does, and that is the
point: the model spells out what the hardware does silently.

**The finite-precision behaviour is a named function.**  `wrap` and `saturate` are
the two policies, sitting side by side, each three lines long.  Because they are
separate and named, you can compare them, test them, and reuse them — every later
unit in this class needs some version of both.

**It is vectorised.**  `a` and `b` are whole arrays, so all 65,536 cases are
computed in one call with no loop.  A model you can run over the entire input
space is a different kind of tool from one you run on six cases.

## How the model reaches the hardware

The model does not talk to the simulator directly.  It writes **test vectors** as
CSV, using a pandas `DataFrame`:

~~~python
def gen_int_prod_vectors(vec_dir, width=8):
    a, b = int_prod_inputs(width)
    model = int_prod_model(a, b, width)

    # every column the testbench will report, and what it should contain
    golden = pd.DataFrame({c: np.asarray(model[c], dtype=np.int64) for c in INT_PROD_COLS})
    golden.to_csv(vec_dir / "int_prod_golden.csv", index=False)

    # the stimulus is just the input columns of the same table
    golden[["a", "b"]].to_csv(vec_dir / "int_prod_in.csv", index=False)
~~~

Two files: the inputs, and the expected outputs — and notice the second is a
slice of the first table rather than a separately-built thing, so they cannot
disagree about what was asked.

The testbench reads the stimulus, drives the module, and writes what it got as a
CSV of its own.  A separate step reads both back and compares them:

~~~
    int_prod_gen  ──> int_prod_in.csv      ──> [SystemVerilog] ──> int_prod_sv.csv
         └──────────> int_prod_golden.csv  ─────────────────────────────┐
                                                                        v
                                                              int_prod_check
~~~

~~~python
diff = golden.compare(actual, result_names=("python", "systemverilog"))
~~~

`DataFrame.compare` returns only the cells that differ, which is more useful than
the first mismatch alone: if a width is wrong somewhere, you see an entire column
light up rather than one row.

CSV is worth a word.  It is what the rest of the course uses, so the pattern you
learn here is the one the labs expect.  pandas reads and writes it in a line at
each end.  SystemVerilog reads it with `$fscanf` — the format string just needs
commas in it — and the header row means the columns are matched **by name**, so
the testbench and the model cannot quietly drift into different orders.  And you
can open the file in a spreadsheet, or read it over someone's shoulder at 2am,
which is not nothing.

The one wrinkle on the SystemVerilog side is that the header is not data:

~~~systemverilog
    // The first line of a CSV is the column names.  Read it and throw it away.
    code = $fgets(header, fin);
~~~

## Two ways to check an answer

The two parts of this demo check themselves differently, and the difference is
worth naming.

`int_prod` uses a **golden value** comparison: for these inputs, the answer must
be exactly this.  It is the most common kind of check, and it is only as good as
the model that produced the values.

[`samp_pack`](./samp_pack.md) adds a **property**: `unpack(pack(x)) == x`, for
every `x`.  Nothing is stored; the claim is about the relationship between two
operations.  Properties are often easier to trust than golden values, because you
do not have to first convince yourself the stored answers were right.  They also
tend to survive redesign — that one stays true no matter how the packing is
implemented.

Good verification uses both.  Reach for a property whenever you can state one.

## Where Python will trip you

Python and SystemVerilog disagree by default, and the disagreement is systematic:

* **Python** keeps every bit unless you explicitly remove them.  Integers are
  unbounded, so `x << 13` just gets bigger, and a negative number has infinitely
  many leading ones.
* **SystemVerilog** removes every bit that does not fit, and does not mention it.

So a Python model of finite-precision hardware has to put the limits *back in* by
hand — that is exactly what `wrap` is for, and why `pack_sample` masks each field
with `& 0xFFF` before shifting it into place.  Forget a mask and the Python side
quietly computes something the hardware never could.

The failure has a signature worth recognising: the model and the RTL agree on
small values and diverge on large or negative ones.  That is almost always a
missing mask or a missing `wrap` in the model, not a bug in the RTL.

NumPy has the mirror-image trap.  Its fixed-width integer types overflow silently
like hardware does, so `np.int32` arithmetic can wrap where you meant it not to.
This model uses `np.int64` throughout and reduces precision only in `wrap` and
`saturate`, so every loss is deliberate.

---

Go to [packing a data structure](./samp_pack.md).
