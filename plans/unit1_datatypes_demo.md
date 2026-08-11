# Unit 1 Demo: `datatypes`

A plan for the Unit 1 SystemVerilog demo — integer arithmetic, bit growth,
truncation and saturation, and packing a real data structure. Written so each
step can be handed to Claude CLI (or done by hand) as a self-contained prompt.

**Status: built and verified, 2026-08-11.** Both parts run end to end. The
SystemVerilog agrees with the Python golden model on all 65,542 `int_prod` rows
and all 100 `samp_pack` samples; 67 tests pass in hwdesign, 30 in waveflow. The
three waveflow changes are on branch `svsim-and-step-tracebacks` (pushed); see
[What changed from this plan](#what-changed-from-this-plan) for the three places
reality differed.

**Scope:** the demo, plus three enabling changes in **waveflow** (`repos/pysilicon`)
that this plan makes upstream rather than stopgapping. The Unit 1 lab (PRNG) and
the Unit 1/Unit 2 demo reshuffle are recorded under [Context](#context) and
[Follow-on work](#follow-on-work) but are *not* part of this plan.

## Context

The course is being reworked. What was one large unit last semester is now two:

|       | Unit 1                                    | Unit 2                                              |
| ----- | ----------------------------------------- | --------------------------------------------------- |
| Topic | data types, integers, combinational logic | FSMs and sequential logic                           |
| Demos | **`datatypes` (this plan)**       | `lin_relu`, `poly_fun` (pipelined), an FSM demo |
| Lab   | PRNG / stream cipher                      | `subc`                                            |

Consequence that motivates this plan: all three existing Unit 1 demo modules
([`simp_fun.sv`](../demos/simp_fun/simp_fun.sv),
[`lin_relu.sv`](../demos/simp_fun/lin_relu.sv),
[`poly_fun.sv`](../demos/simp_fun/poly_fun.sv)) take `clk`/`rst` and register
their inputs with `always_ff`. Its doc page is already titled *"Basic Sequential
Logic and FSMs"*. All of it belongs to Unit 2. **Once it moves, Unit 1 has no
SystemVerilog demo at all** — only `setup`. Students would meet SystemVerilog
for the first time in a graded lab, in the same two weeks they are installing
Vivado and Python.

This demo fills that gap, and it must also prepare the bit-level machinery the
PRNG lab depends on — slicing, masking, and where the sign bit goes — none of
which appears in any current demo.

**Known gap:** Part 2 teaches sign extension via `$signed`, not via `>>>`, so
`>>` vs `>>>` is never shown in SystemVerilog code (the shifts live on the Python
side, where masking is what matters). These are the same question — what fills
the vacated high bits — so the `samp_pack.md` page should draw the parallel in a
sentence where `re_bad` is explained. If that proves too thin once the PRNG lab
is written, add a two-line shift example rather than a third demo part.

## Teaching content

Everything here maps onto the existing Unit 1 problem set
([`basic_logic.html`](../units/unit01_basic_logic/prob/basic_logic.html)):
bit packing (Q1), two's complement (Q2), truncation (Q4), addition overflow
(Q5), multiplication overflow (Q7), arithmetic shifts (Q8), bit growth (Q9).

### Part 1 — `int_prod`: the discarded half of a product

The current `simp_fun` assigns a 16x16 product into a 16-bit output and says
nothing about it. That silently discarded half is the lesson.

Signed throughout (two's complement is Q2), `W = 8`, and written with a single
`always_comb` block — the course teaches `always_comb` / `always_ff`, not
`assign`.

```systemverilog
module int_prod #(parameter int W = 8) (
    input  logic signed [W-1:0]   a,
    input  logic signed [W-1:0]   b,
    output logic signed [2*W-1:0] prod,        // full product — nothing lost
    output logic        [W-1:0]   hi,          // upper half, as bits
    output logic        [W-1:0]   lo,          // lower half, as bits
    output logic signed [W-1:0]   trunc,       // what "a*b" gives you in W bits
    output logic signed [W-1:0]   sat,         // clamped instead of wrapped
    output logic                  overflow,    // did trunc lose the value?
    output logic                  hi_nonzero   // the WRONG test — see -1 * 1
);
    localparam signed [W-1:0] SAT_MAX =  (1 <<< (W-1)) - 1;   //  127 at W=8
    localparam signed [W-1:0] SAT_MIN = -(1 <<< (W-1));       // -128 at W=8

    always_comb begin
        prod  = a * b;          // LHS is 2W -> operands widen -> exact
        trunc = a * b;          // LHS is W  -> evaluated in W bits -> wraps

        hi = prod[2*W-1:W];     // a part-select is always UNSIGNED — these are
        lo = prod[W-1:0];       // bit views, not numbers

        // Saturate: clamp to the W-bit signed range instead of wrapping.
        if (prod > SAT_MAX)
            sat = SAT_MAX;
        else if (prod < SAT_MIN)
            sat = SAT_MIN;
        else
            sat = prod;         // it fits, so this truncation is lossless

        overflow   = (prod != trunc);   // trunc is signed, so it sign-extends to 2W
        hi_nonzero = |hi;               // reduction OR
    end
endmodule
```

Four things this teaches, none decorative:

1. **The two `a * b` lines are the core.** Same expression, twice, different
   answers, because the left-hand side is a different width. That is
   SystemVerilog's context-determined width rule, and it is exactly the trap
   waiting in the PRNG lab.
2. **`sat` vs `trunc`** — two responses to the same overflow, side by side.
   The `else` branch is its own small lesson: truncation is safe only once you
   have proved the value fits.
3. **`hi`/`lo` introduce part-select**, and are deliberately left *unsigned* —
   a part-select in SystemVerilog is always unsigned regardless of the operand,
   because it yields bits rather than a value. Worth saying out loud on the doc
   page rather than leaving as a trap.
4. **`overflow` vs `hi_nonzero`** — the correct signed test against the naive
   unsigned one. `|hi` is what students reach for first and it cries wolf on
   every negative product. `prod != trunc` says exactly what overflow means:
   the truncated value is not the true value.

Vectors that make it land, at `W = 8`:

| `a` | `b` | true`a*b` | `trunc`      | `sat` | `overflow` | `hi_nonzero` | why it earns a row                    |
| ----- | ----- | ----------- | -------------- | ------- | ------------ | -------------- | ------------------------------------- |
| 3     | 5     | 15          | 15             | 15      | 0            | 0              | fits — the baseline                  |
| 100   | 100   | 10000       | 16             | 127     | 1            | 1              | wrapping says 16; saturation says 127 |
| -100  | 100   | -10000      | -16            | -128    | 1            | 1              | the same, on the negative side        |
| 16    | 16    | 256         | 0              | 127     | 1            | 1              | two nonzero inputs multiply to zero   |
| 20    | 20    | 400         | **-112** | 127     | 1            | 1              | two positives multiply to a negative  |
| -1    | 1     | -1          | -1             | -1      | 0            | **1**    | the naive test cries wolf             |

**Display in binary as well as decimal.** In decimal the lesson is invisible;
in binary it is obvious the bits merely moved.

```systemverilog
$display("a=%0d b=%0d | prod=%b hi=%b lo=%b | trunc=%0d sat=%0d ovf=%b",
         a, b, prod, hi, lo, trunc, sat, overflow);
```

### Part 2 — `samp_pack`: packing a real data structure

Not a tour of bitwise operators — a data structure students would actually meet.
A timestamped complex sample:

| field    | width | type     |
| -------- | ----- | -------- |
| `time` | 8     | unsigned |
| `real` | 12    | signed   |
| `imag` | 12    | signed   |

8 + 12 + 12 = **32 bits exactly**, one word. This is how an RF/ADC sample stream
is packed into an AXI-Stream beat, so it also sets up the stream and FIFO units
later in the course.

Layout, MSB-first:

```
bit  31..24 : time   (8b unsigned)
bit  23..12 : real  (12b signed)
bit  11..0  : imag  (12b signed)
```

```systemverilog
module samp_pack #(
    parameter int TW = 8,    // time width
    parameter int DW = 12    // real/imag width
) (
    // pack
    input  logic        [TW-1:0]      t_in,
    input  logic signed [DW-1:0]      re_in,
    input  logic signed [DW-1:0]      im_in,
    output logic [TW+2*DW-1:0]        word,

    // unpack — fed the word back
    output logic        [TW-1:0]      t_out,
    output logic signed [15:0]        re_out,   // correct: sign-extended
    output logic signed [15:0]        im_out,
    output logic signed [15:0]        re_bad    // the missing-$signed bug
);
    always_comb begin
        // Packing: concatenation. Signedness is LOST here — a concatenation
        // result is always unsigned, whatever went into it.
        word = {t_in, re_in, im_in};

        t_out  = word[TW+2*DW-1 : 2*DW];
        re_out = $signed(word[2*DW-1 : DW]);   // sign-extends to 16 bits
        im_out = $signed(word[DW-1   : 0]);
        re_bad =         word[2*DW-1 : DW];    // zero-extends — wrong
    end
endmodule
```

**The one trap, and why the destination is 16 bits.** A part-select is unsigned
regardless of what was packed into it, so widening it needs `$signed`. Unpacking
a 12-bit field into a 12-bit variable would hide this — same bits, reinterpreted
correctly — so the bug only shows when the destination is wider, which is also
what real code does (unpack into a 16-bit working register).

With `re_in = -1000`: the 12-bit field is `0xC18`, `re_out` is `-1000`, and
`re_bad` is `+3096`. Every negative sample folds into the top of the positive
range.

This is the same lesson as `hi`/`lo` in Part 1, which is deliberate: both parts
put the correct construct beside the one students reach for first.

### Part 2 exercise: 100 samples, two independent checks

Python generates 100 random samples — with `-2048`, `2047`, `0`, and `-1` forced
in among them — packs them with shifts and masks, and writes both the fields and
the packed words (hex, one per line: a realistic sample file). The SV testbench
reads them and checks:

1. **Cross-language:** SV's `word` equals Python's packed word, bit for bit.
2. **Round-trip:** `unpack(pack(x)) == x` for all 100 samples.

The second is a *property*, not a golden-value comparison — a different and
useful verification idea to plant early.

The Python side carries its own half of the lesson: packing there is
`(t << 24) | ((re & 0xFFF) << 12) | (im & 0xFFF)`, so the masks are mandatory
because Python integers are unbounded and negative values would otherwise
contaminate the neighbouring fields. SV needs no masks because the widths are
declared. Same operation, opposite defaults — which is exactly the Python-vs-SV
comparison worth drawing.

### Part 2 plots

Scatter the 100 samples on the I/Q plane coloured by timestamp — it looks like
real captured data. Then the same scatter using `re_bad`: the entire negative
half-plane folds up into a positive band. The bug becomes a picture rather than
a table row.

### Part 1 plot

Sweep `a` and `b` over the full signed 8-bit grid (-128..127, so 256x256 — small
enough to plot exactly, which is why `W = 8`). Three panels side by side: the
true product, `trunc`, and `sat`. The wraparound bands in `trunc` are
unmistakable, and `sat`'s flat plateaus at ±127/-128 show the tradeoff — it
stops lying about the sign, at the cost of no longer being right about the
magnitude. A fourth panel with the `overflow` mask shows how much of the input
space is broken. This turns "multiplication overflows" from a sentence into a
picture.

## Layout

One directory, not two. The docs already model a demo as one nav entry with
child pages ([`simp_fun`](../docs/demos/simp_fun/) has four,
[`fixp`](../docs/demos/fixp/) has three), the two parts share the entire build
scaffold, and the name leaves room for a third part later without a rename.

```
hwdesign/
├── demos/datatypes/
│   ├── int_prod.sv
│   ├── tb_int_prod.sv
│   ├── samp_pack.sv
│   ├── tb_samp_pack.sv
│   ├── datatypes_build.py     # the BuildDag + run_dag_cli entry point
│   ├── vectors/               # generated
│   ├── results/               # generated (plots, JSON)
│   └── sim/                   # xsim scratch
└── docs/demos/datatypes/
    ├── index.md
    ├── int_prod.md
    └── samp_pack.md
```

Nothing goes in the `hwdesign/` package. Everything shared — the xsim runner and
the SV simulation step — is a waveflow change instead; see
[Three waveflow changes](#three-waveflow-changes--made-upstream-not-stopgapped).

**Naming:** testbenches are `tb_<name>.sv`. All eight testbenches in the repo
already follow this (`tb_cubic.sv`, `tb_poly_fun.sv`, `tb_subc_divide.sv`, ...)
and none use the `_tb.sv` suffix.

## Build: use waveflow's `BuildDag`

Decision: **use `BuildDag` + `run_dag_cli`**, not a hand-rolled CLI.

The motivation is running components in isolation, and isolation is *implemented
by* the freshness machinery — `--through int_prod_sim` runs only the sim step
precisely because `int_prod_gen` reports UP-TO-DATE. You cannot have the second
without the first.

[`run_dag_cli`](../../pysilicon/waveflow/build/cli.py) also supplies two flags
that are genuinely good pedagogy here and tedious to reimplement worse:

- `--list-steps-verbose` prints each step with its description and its
  `consumes`/`produces`. For a demo whose point is "here are the stages of a
  verification flow," that listing *is* a teaching artifact, and it stays correct
  when the DAG is edited.
- `--status` answers "did I actually run the Python half yet?"

Cost is small: a `BuildStep` is a dataclass with `consumes`, `produces`, and
`run()` — see `GenStep` in
[`basic_vec_build.py`](../../pysilicon/examples/basic_vec/basic_vec_build.py),
about ten lines.

### DAG shape — two independent branches

```
int_prod_source  ─→ int_prod_gen  ─→ int_prod_sim  ─→ int_prod_check  ─→ int_prod_docs
samp_pack_source ─→ samp_pack_gen ─→ samp_pack_sim ─→ samp_pack_check ─→ samp_pack_docs
```

Eight steps plus `SourceStep`s. Two parallel branches rather than one line is
deliberate: `--through samp_pack_check` visibly skips the `int_prod` branch, which
shows students why it is a *graph* and not a list.

| step        | does                                                          |
| ----------- | ------------------------------------------------------------- |
| `*_gen`   | Python golden model; writes input vectors + expected outputs (seeded) |
| `*_sim`   | `run_sv_sim()` on the testbench; captures output             |
| `*_check` | compare SV vs Python; raise on mismatch; write JSON report    |
| `*_docs`  | render plots, write-if-different into `docs/demos/datatypes/images/` |

### Guardrail: keep step bodies to one call

Every step body is a single call into a plain function:

```python
class IntProdGenStep(BuildStep):
    def run(self, config, **_):
        return {"int_prod_vectors": gen_int_prod_vectors(config.root_dir, W=8)}
```

`gen_int_prod_vectors()`, `run_sv_sim()`, and `check_int_prod()` stay ordinary
functions rather than logic buried in step bodies. The DAG orchestrates; it must
not hide anything. Students get isolation from `--through`, the
`xvlog`/`xelab`/`xsim` invocation still lives in code they can open, and the
tests below can call the Python halves directly without a DAG or a toolchain.

**No notebooks.** `--through` already provides step-by-step execution, so a
notebook would be a second, drifting copy of the same flow.

### Three waveflow changes — made upstream, not stopgapped

waveflow **is editable** from this repo, and all three fixes below belong there.
Course-side workarounds would become debt every later unit inherits, and would
hide the problems from waveflow's other users. Make these first; the demo then
needs nothing course-specific and the `hwdesign/` package stays empty.

> **Path note:** `../../pysilicon/` below is the **waveflow repo** at
> `repos/pysilicon` (the clone whose package is `waveflow/`). Not to be confused
> with `hwdesign/pysilicon/`, the stale vendored snapshot being migrated away
> from — see [`migration.md`](./migration.md).

> **Coordination.** waveflow is installed *editable* into the course venv, so
> edits take effect in hwdesign immediately and land on whatever branch is
> checked out. Check `git -C ../pysilicon branch --show-current` first, and do
> not edit it from two sessions at once. (Verified 2026-08-10: `main`, clean.)

1. **`BuildDag.run` discards step tracebacks.**
   [`build.py:627-630`](../../pysilicon/waveflow/build/build.py#L627-L630)
   catches every step exception and keeps only `str(exc)`. A student whose
   testbench fails to elaborate sees `FAILED: <message>` with no file, no line,
   no stack — exactly the week-1 opacity that would make the DAG a liability.

   **Fix:** keep the traceback on `BuildResult` — add a `traceback: str | None`
   field populated from `traceback.format_exc()` in that handler, and have
   `run_dag_cli`'s `on_step_end` print it when a step fails. Every `BuildDag`
   user benefits; the alternative (a course base class wrapping `run()`) also
   forces a `run`/`run_impl` split on every step, because subclasses override
   `run()` and would bypass the wrapper.
2. **`sv_sim` has no importable core.**
   [`waveflow/scripts/sv_sim.py`](../../pysilicon/waveflow/scripts/sv_sim.py)
   is shaped purely as a CLI — argparse `main()`, `sys.exit()` on failure —
   so calling it from a step would kill the DAG process rather than raise.

   **Fix:** the standard split. A `run_sv_sim(sources, tb, top, sim_dir, ...)`
   library function that **raises** on failure with the tool's own stderr
   attached, plus a thin `main()` that catches and exits. It must **echo each
   command before running it** so a broken Vivado PATH is diagnosable by a TA in
   ten seconds. Do not add a second module — refactor the existing one.
3. **There is no `SvSimStep`.** Every build step waveflow ships is
   Vitis/HLS-centric, so anyone driving a plain xsim testbench from a `BuildDag`
   writes their own today. This is the most valuable of the three.

   **Fix:** add `SvSimStep` alongside the existing steps in
   [`waveflow/build/`](../../pysilicon/waveflow/build/), consuming SV sources
   plus a vector artifact and producing the simulation output, implemented on
   top of `run_sv_sim`.

## Steps

**In waveflow first** (`repos/pysilicon`, check the branch before starting):

1. **`BuildResult` keeps the traceback**, and `run_dag_cli` prints it on failure.
2. **Split `sv_sim`** into a raising `run_sv_sim()` plus a thin CLI `main()`.
3. **Add `SvSimStep`** to `waveflow/build/`, built on `run_sv_sim`.

**Then in hwdesign:**

4. **`demos/datatypes/int_prod.sv` + `tb_int_prod.sv`** — as above. Testbench
   reads vectors from `vectors/`, writes results, prints the binary display line.
5. **`demos/datatypes/samp_pack.sv` + `tb_samp_pack.sv`** — as above.
6. **`demos/datatypes/datatypes_build.py`** — plain functions, six `BuildStep`s
   (the `*_sim` pair being waveflow's new `SvSimStep`), `run_dag_cli` entry
   point. Verify `--list-steps-verbose`, `--status`, and `--through` on each
   branch actually behave as this plan claims.
7. **`docs/demos/datatypes/`** — `index.md`, `int_prod.md`, `samp_pack.md`, with
   `parent:`/`nav_order:` frontmatter matching the existing demo pages. Document
   `--through` and `--force-step`; note there is **no** `--only STEP` flag, so
   students don't hunt for one.
8. **Test infrastructure — none of this exists today.**
   - Create `hwdesign/tests/` with `__init__.py`, `conftest.py`, and
     `test_dag_wiring.py` / `test_int_prod.py` / `test_samp_pack.py` /
     `test_demo_e2e.py` (tiers 0, 1, 1, 2).
   - Add `pytest` (and `pytest-cov` if wanted) to
     [`requirements-dev.txt`](../requirements-dev.txt), which currently lists
     only the two editable installs.
   - Add a `[tool.pytest.ini_options]` section to
     [`pyproject.toml`](../pyproject.toml) with `testpaths = ["tests"]` and a
     `markers = ["vivado: requires Vivado on PATH"]` entry.
   - `conftest.py` holds the Vivado skip predicate and a fixture giving the demo
     root, so tier-2 tests stay three lines each.

   See [Testing](#testing) for what each tier asserts.

## Doc assets: plots tracked in the repo, regenerated on demand

The plots from both parts are committed under
`docs/demos/datatypes/images/`, matching the existing convention
(`docs/demos/simp_fun/images/*.png`, referenced as
`<img src="images/foo.png" width="800"/>`). The requirement is that re-running
the demo must **not** leave the repo dirty.

**Use the DAG, not `create_doc_assets`.** waveflow's
[`create_doc_assets.py`](../../pysilicon/waveflow/scripts/create_doc_assets.py)
implements exactly this idea — a `DocSet` of dependencies, outputs and a
generator, stale when an output is missing or a dep is newer, with
`--status`/`--force`/`--list`. But it is **not usable from hwdesign**: its
`_REPO_ROOT` is `Path(__file__).resolve().parents[2]`, i.e. the *waveflow*
clone, and `_build_registry()` is a hardcoded dict of waveflow's own doc sets
with no extension point. Rather than extend it, use the `BuildDag` — a step
whose `produces` are the tracked PNGs is skipped when fresh, which is the same
logic, already wired into `--status` and `--through`. One freshness mechanism,
not two.

Add a `*_docs` step to each branch, after `*_check`:

```
int_prod_gen  ─→ int_prod_sim  ─→ int_prod_check  ─→ int_prod_docs
samp_pack_gen ─→ samp_pack_sim ─→ samp_pack_check ─→ samp_pack_docs
```

Three things are needed for the repo to actually stay clean:

1. **Fixed RNG seed.** The 100 samples must be seeded, or every regeneration
   produces a genuinely different plot. This also makes the tests reproducible.
2. **Write-if-different.** Even with identical data, matplotlib writes
   byte-different PNGs on each render — the `Software` metadata tag carries the
   matplotlib version, and some backends add a date. So render to a temporary
   path, compare bytes against the tracked file, and copy only on a difference.
   Roughly five lines, and robust regardless of matplotlib's metadata behaviour.
3. **Suppress the metadata anyway** — `savefig(path, metadata={"Software": None})`
   removes the main source of spurious byte differences, so step 2 almost never
   has to copy.

Rebuild is then `--force-step int_prod_docs`, or just re-running after editing a
source; `--status` shows whether the committed figures are stale.

## Testing

Worth doing, and cheaper than it looks — the demo already computes exact
pass/fail results, so most of the work is making failures loud rather than
writing new assertions.

**Why it matters here specifically.** waveflow is installed *editable* from a
clone that is actively developed (see
[`requirements-dev.txt`](../requirements-dev.txt)), so **the demo can break
without anyone touching this repo**. A test run is the canary for that drift.
hwdesign currently has no `tests/`, no pytest config, and no CI.

**Prerequisite — check steps must raise.** Have `*_check` raise on any mismatch,
the way waveflow's own `basic_vec` `RunStep` does (`raise RuntimeError("STOP —
Vitis disagreed with the Python golden: ...")`). Then a student running the demo
and a test runner see the same loud failure, and the tests need no duplicated
comparison logic.

### Tier 0 — DAG wiring (milliseconds, no tools)

Build the DAG and assert it is well-formed: every `consumes` has a producer,
`step_names()` resolves, each documented `--through` target exists. Artifact-name
typos are the classic `BuildDag` error and would otherwise surface only at
runtime, on a student's machine. Nearly free to write.

### Tier 1 — Python golden models (seconds, no Vivado)

The high-value tier. Test the plain functions directly — no DAG, no toolchain:

- `int_prod`: `trunc == prod` exactly when `overflow` is false; `sat` clamps to
  ±(2^(W-1)) and is monotonic in the true product; the six table rows above as
  explicit cases.
- `samp_pack`: `unpack(pack(x)) == x` over random samples, plus the forced edge
  cases (`-2048`, `2047`, `0`, `-1`); packed words are exactly 32 bits; the
  buggy zero-extended unpack differs from the correct one precisely when the
  field is negative.

These are properties, so they can be run over many random inputs cheaply. This
tier is what catches waveflow API drift.

### Tier 2 — full DAG including xsim (minutes, needs Vivado)

`dag.run(config, through="int_prod_check")` and assert success — about three
lines each, given that the check steps raise. Guard with a skip when `xvlog` is
not on `PATH` so the suite still passes on a machine without Vivado:

```python
pytestmark = pytest.mark.skipif(shutil.which("xvlog") is None,
                                reason="Vivado not on PATH")
```

### Tier 3 — doc assets stay clean

One cheap test worth having: run the `*_docs` steps twice and assert the tracked
PNGs are byte-identical after the second run, and that `git status --porcelain`
on `docs/demos/datatypes/images/` is empty. That is the property the whole
write-if-different mechanism exists to guarantee, and it is easy to break by
accident (an unseeded RNG, a stray `savefig` timestamp).

### Where things live

Demo tests go in a new `hwdesign/tests/`. The three **waveflow** changes get
tests in waveflow's own suite, which already has a
[`tests/build/`](../../pysilicon/tests/build/) directory — that is where the
`BuildResult` traceback field and `SvSimStep` belong.

CI is optional and secondary: GitHub Actions could run tiers 0 and 1 (no Vivado
needed), but it would install waveflow from git rather than the local editable
clone, so it catches drift only after a waveflow push. The local `pytest` run is
the real canary.

## Decisions taken

- **No notebooks.** `--through` already gives step-by-step execution; a notebook
  would be a second copy of the same flow, free to drift out of sync.
- **`W = 8`**, not 16. The full signed sweep is 256x256 — plottable exactly —
  and 8-bit binary stays readable in `$display` output.
- **No polynomial-with-saturation demo.** Students see enough polynomial
  examples elsewhere in the course (`poly_fun` in Unit 2, `cubic` in Unit 3).
  Saturation is taught here instead, as the `sat` output of `int_prod`, where it
  costs three lines and sits directly beside the truncation it is contrasted
  with.
- **`always_comb` only, no `assign`.** The course teaches `always_comb` /
  `always_ff`; `assign` is not introduced. Both modules use a single
  `always_comb` block.
- **Signed throughout in `int_prod`**, except `hi`/`lo`, which stay unsigned
  because a part-select yields bits rather than a value — called out explicitly
  on the doc page rather than left as a trap.
- **Fix waveflow upstream, do not stopgap in hwdesign.** The three changes above
  are in scope for this plan. `hwdesign/` gains nothing.

## Follow-on work

Not in scope here, recorded so it is not lost:

- Move `lin_relu` / `poly_fun` / `simp_fun` to a Unit 2 demo directory; consider
  keeping *de-clocked* variants so Unit 2 can open with "the design you already
  know, now with registers."
- Unit 2 has no FSM demo. [`demos/fsm/`](../demos/fsm/) holds only `counter.sv`
  and `tb_counter.sv` and has no docs page, but [`subc`](../docs/labs/subc/)
  requires symbolic states and a handshake protocol. Same gap this plan closes
  for Unit 1.
- The Unit 1 lab (PRNG -> stream cipher), which replaces the earlier `intmath`
  saturation lab (dropped: too close to the Unit 3 `cubic` lab).

## What changed from this plan

Recorded because both were discovered by running the thing, not by reading it.

### 1. A fourth waveflow change: `SvSimStep.outputs`

The plan had `SvSimStep` producing only the simulation *directory*. That is not
enough to make freshness mean anything, and it fails in a way that looks like
success:

- xsim exits **0 even after `$fatal`**, so a testbench that could not open its
  input files still reported `PASSED`.
- `run_sv_sim` creates `sim_dir` before invoking anything, so the failed run left
  a directory behind that looked newer than its inputs — and the next build
  skipped the simulation as `UP-TO-DATE` while the file the check step needed
  was still missing.

`SvSimStep` therefore gained an `outputs` mapping for the files the testbench
itself writes. They join `produces`, so freshness tracks real data, and the step
raises if a declared output is absent after the run. That closes the
silent-success hole as well.

### 2. Path plusargs must be POSIX-form

`-testplusarg "vecdir=C:\Users\...\repos\..."` arrives at `$value$plusargs` with
its backslashes read as escapes — `\r` became a carriage return, and the
testbench tried to open `C:UserssdranDocuments/...`. `run_sv_sim` now emits
`Path` values via `as_posix()`; `$fopen` accepts forward slashes on Windows, so
this costs nothing.

### 3. `sim_tool()` — resolve the simulator, do not assume `PATH`

Not a correction so much as an opportunity: waveflow gained `find_vivado_path()`
upstream (commit `07661e1`) while this work was in progress. The xsim binaries
live in the same `bin/` as `vivado`, so `run_sv_sim` now derives them from it and
falls back to `PATH`. Students no longer need to source `settings64.bat`, and the
Linux binary names work.

### Confirmed as planned

Everything else landed as written. Worth noting that the teaching claims were
verified against generated data rather than asserted: `20 * 20` really does
truncate to `-112`, `-1 * 1` really does trip `hi_nonzero` while `overflow`
stays 0, and `-1000` really does read back as `+3096` without `$signed`. Those
values are now pinned by tests in `tests/test_datatypes_models.py`, so the docs
cannot drift away from the code.

The matplotlib STOPGAP in `pyproject.toml` is also resolved: waveflow declared it
upstream (`a95edfb`) on the same day. matplotlib stays as a dependency, but now
because the demo plots with it directly.
