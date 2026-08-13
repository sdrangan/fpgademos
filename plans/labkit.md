# `labkit` — publishing student labs from annotated solutions

A plan for replacing the manual redaction step between `hwdesign-soln` (private)
and `hwdesign` (public). Written so each stage can be handed to Claude CLI as a
self-contained prompt.

**Status: planned, 2026-08-12.** Not started.

**Scope:** the tool and its tests, sized for exactly one consumer — the Unit 1
PRNG lab, which is the first lab authored this way and is planned separately.

Two things are deliberately *out* of scope, both decided 2026-08-12:

* **Retrofitting `cubic` and `subc`.** Those labs are likely to change, and
  converting them now would be work done against a moving target. The grammar is
  still designed around what their solutions already look like — that evidence is
  what made it small — but nothing is migrated.
* **Notebooks.** `prng` does not need one: incremental execution was the reason
  labs used notebooks, and `--through <step>` on the build DAG now does that job
  better. This removes the only file type needing more than a line pass. See
  [Notebooks, deferred](#notebooks-deferred) for what it will cost when a lab
  does want one.

## The finding that shapes this

The existing solution files are already 90% annotated. Both labs put the TODO
comments *in the solution*, immediately above the code they stand in for:

```systemverilog
// hwdesign-soln/labs/cubic/cubic.sv:69
        // TODO:  Compute the following intermediate values
        // x2_s1_next = ...  x squared term
        // ax1_s1_next = ...  a1*x + a0 term
        // x^2 term
        x2_s1_next = sat( (x_s0 * x_s0) >>> FBITS );

        // a1*x + a0 term
        ax1_s1_next = sat( ((a1_s0 * x_s0) >>> FBITS) + a0_s0 );
```

```python
# hwdesign-soln/labs/subc/subc_divide.py:40
    # TODO: Implement the conditional subtraction division algorithm

    z = np.uint32(0)
    for _ in range(nbits):
        ...
```

The manual step is literally *delete the lines after the TODO comment*. So the
grammar needs one thing, not three: **a marker pair around the code to drop.**
The TODO text is a comment, and a comment is harmless in both versions — it needs
no directive at all, and it stays where it is, next to the code it describes, so
the two cannot drift.

This is what makes the tool small. Every richer design considered (paired
SOLUTION/STUDENT blocks, generating both trees from a neutral source, cell tags)
adds machinery to express something the files already express.

Consequences worth stating:

* **The annotated file *is* the solution.** It compiles, simulates, and passes
  its own tests with no build step. There is one generated direction, not two,
  and an instructor debugging the solution never has a tool between them and the
  file.
* **The retrofit is mechanical.** Adding markers to `cubic` and `subc` is
  inserting two lines per hole. Neither lab needs `TODO` or `STUB` (below).

## Marker grammar

```
<prefix> BEGIN SOLUTION
    ...dropped from the student file...
<prefix> BEGIN TODO          (optional)
    ...emitted verbatim...
<prefix> BEGIN STUB          (optional)
    ...emitted with the comment prefix removed...
<prefix> END SOLUTION
```

Only the outer pair is required, and in the common case it is all you write.
The two optional sections exist for what the *solution* must not contain:

* **`TODO`** — student-only text. Not needed when the TODO comment can simply
  live outside the block, which is the normal case. Needed when the text would
  be actively wrong in the solution (`// y is not driven yet`).
* **`STUB`** — student-only *live code*. The rare one, but not optional in
  general: a Python function whose entire body is inside a SOLUTION block leaves
  `def f():` followed by nothing, which is a syntax error. `subc_divide.py` only
  escapes this because two `if` guards precede the block. Written commented in
  the solution and uncommented on the way out.

Matching: strip leading whitespace and the comment prefix, then require an exact
token match. Markers may sit at any indentation. Nesting is an error.

STUB de-commenting: `<ws><prefix><one optional space><rest>` → `<ws><rest>`.
Leading whitespace is preserved, so `    # return 0` becomes `    return 0`.
Anything beyond the single consumed space is kept, and is the author's business.

Comment prefixes by extension:

| Extension | Prefix |
| --- | --- |
| `.sv .svh .v .vh .c .h .cpp .hpp .cc .tpp` | `//` |
| `.py .tcl .sh .toml .cfg` | `#` |
| `.md` | `<!--` … `-->` |
| `.ipynb` | `#` in code cells, `<!--` … `-->` in markdown cells |

## Notebooks, deferred

`.ipynb` is the only file type needing more than a line pass, and no lab in scope
has one. Recorded so the shape is known when one does: walk `cells[].source` (a
list of strings, newlines included), apply the same line pass per cell, and on
the way out

* drop `outputs` and set `execution_count` to `null` on every code cell — a
  solution notebook's outputs *are* the solution;
* drop `metadata.widgets`, which is large, machine-written, and pure churn;
* delete a cell that becomes empty, so a redacted-away cell leaves no blank.

Roughly 30 lines in a `notebooks.py`, plus the markdown-cell prefix. Nothing in
the line engine needs to change to accommodate it later.

## The manifest

`lab.toml`, in the solution lab directory:

```toml
[lab]
name   = "prng"
public = "../../../hwdesign/labs/prng"

full    = ["prng_build.py", "tb_prng.sv", "readme.md"]
partial = ["prng.sv", "prng_model.py"]
private = ["notes.md", "autograder_config.xml"]
ignore  = ["sim/", "test_outputs/", "submission/", "*.zip"]
```

**An unlisted file is an error, not a default.** Either default is a bug found
late: silently-not-shipped means students cannot build, silently-shipped-whole
means the answer key is public. Forcing a decision is the only safe rule.

`ignore` is what makes that rule usable. `hwdesign-soln/labs/cubic/` currently
holds fourteen entries, most of them build residue (`sim/`, `autograder.zip`,
`submitted_results.json`, `test_outputs/`, `submission/`). Ship sensible defaults
— `sim/`, `__pycache__/`, `.pytest_cache/`, `*.zip`, `*.pyc`, `test_outputs/`,
`submission/`, `autograder_build/` — and let `ignore` extend them.

`tomllib` is 3.11+; hwdesign declares `requires-python = ">=3.10"`. Add
`tomli; python_version < "3.11"` rather than lowering the floor or inventing a
format.

## Layout

```
hwdesign/labkit/
    markers.py     the line/block engine and the prefix table
    publish.py     manifest, tree walk, guards
    __main__.py    the CLI
```

Instructor-side only. The student-side counterpart —

```python
StudentSourceStep(artifact="prng_sv", path="prng.sv", partial="partial/prng.sv")
```

— belongs in [`hwdesign/grading.py`](../hwdesign/grading.py) beside `GradedStep`,
because a lab's DAG should import its nodes from one place. It behaves as
`SourceStep` does, except that when the top-level file is absent and the
`partial/` one exists it copies it up and says so. **It never overwrites.** That
removes "copy the files from `partial/` first" from the student's manual steps
and from the support queue, while keeping `partial/` as the shipped location so
`git pull` cannot clobber work in progress.

## CLI

```
python -m hwdesign.labkit publish labs/prng [--dry-run]
python -m hwdesign.labkit check   labs/prng     # exit 1 if publishing would change anything
python -m hwdesign.labkit lint    labs/prng     # markers well-formed, nothing written
```

`check` is the CI gate, and it runs in the **private** repo — it is the only side
that can see both trees.

## Guards

Each of these fails the publish rather than warning:

1. A file in the lab directory that is in no manifest list and matches no `ignore`.
2. Unbalanced, nested, or out-of-order markers.
3. Any marker token surviving into an output file.
4. Any non-blank line from inside a SOLUTION block appearing anywhere in the
   output tree. Cheap, and a real leak check.
5. `public` resolving to a path inside the solution repo.
6. A `partial` file containing no markers — you meant `full`, or you forgot them.

Guard 4 is the one that matters most, and the reason to write it early: it is the
only check that catches a leak the author cannot see by reading the diff.

## Verification

Two tiers, in two repos.

**In `hwdesign`** (unit, tier 0) — synthetic fixtures under `tests/labkit/`, one
per language plus a notebook. Assert the redaction, the STUB de-commenting, the
notebook output stripping, and that every guard fires. Synthetic rather than the
real labs, because the real solutions live in the private repo and must not be
copied here even as test data.

**In `hwdesign-soln`** (end to end) — the test that justifies the whole exercise:

```
publish the lab into a temp dir
run the lab DAG there      → it runs at all, and scores the expected baseline
run the lab DAG on soln    → full marks
```

This is only expressible because [`GradedStep`](../hwdesign/grading.py) made the
score machine-readable. The two pieces are halves of one thing: one turns "what
does a fresh student see?" into a number, the other makes the student tree
reproducible enough to ask the question. Neither is worth much alone.

## Retrofit, deferred

`cubic` and `subc` stay hand-redacted for now; both are likely to change. When
they are converted: add markers to the solution, publish, then diff against the
committed partial **once, by hand**. Expect whitespace-only differences — the
current partials carry leftover blank lines and stray indentation where code was
cut out (`cubic.sv:73` is a line of spaces). Byte-exact reproduction is not the
goal and chasing it would distort the grammar; a reviewed one-time diff is.

## Sequencing

1. `markers.py` + fixtures — the engine, no I/O.
2. `publish.py` + manifest + guards; `--dry-run` lands before anything writes.
3. `StudentSourceStep` in `grading.py`.
4. Author the `prng` solution in `hwdesign-soln/labs/prng`, annotated from the
   start, with its docs in `hwdesign/docs/labs/prng`.
5. Publish into `hwdesign/labs/prng` only once the solution is good — the public
   tree is a build output and should not be hand-touched before then.
6. The end-to-end test in `hwdesign-soln`: publish to a temp dir, run the DAG,
   assert the baseline; run it on the solution, assert full marks.

Stages 1–3 are entirely inside `hwdesign` and need no access to the solution
repo.
