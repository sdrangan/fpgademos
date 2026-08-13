---
title: Creating and publishing labs
parent: Instructor Guide
nav_order: 2
has_children: false
---
# Creating and publishing labs

A lab exists twice. The full, working version lives in `hwdesign-soln`, annotated
to mark which parts students complete. The public version in `hwdesign` is
**generated** from it by `labkit`, never written by hand.

## The two trees

```
hwdesign-soln/labs/prng/          the source
    lab.toml                      which file goes where
    prng.sv                       annotated — students get a redacted copy
    prng_model.py                 annotated
    tb_prng.sv                    shipped whole
    prng_build.py                 shipped whole
    notes.md                      never shipped

hwdesign/labs/prng/               generated
    tb_prng.sv                    copied whole
    prng_build.py                 copied whole
    partial/
        prng.sv                   redacted
        prng_model.py             redacted
```

Redacted files land in `partial/` rather than at the top level, so that a
student's work in progress sits where `git pull` cannot overwrite it. They do not
have to copy the files up by hand — the lab's build DAG does it on the first run
(see [What the student does](#what-the-student-does)).

## Annotating a file

Wrap the code students should write in a marker pair. The comment prefix is the
one for that language — `//` for SystemVerilog and C++, `#` for Python.

```systemverilog
    always_comb begin

        // TODO:  Compute the following intermediate values
        // x2_s1_next = ...  x squared term
        // ax1_s1_next = ...  a1*x + a0 term
// BEGIN SOLUTION
        x2_s1_next  = sat( (x_s0 * x_s0) >>> FBITS );
        ax1_s1_next = sat( ((a1_s0 * x_s0) >>> FBITS) + a0_s0 );
// END SOLUTION
    end
```

Students get everything except the two lines between the markers.

**The `TODO` comment sits outside the block.** That is deliberate and it is why
the annotation is so light: a comment is harmless in the solution, so it needs no
directive at all, and keeping it adjacent to the code it stands for means the two
cannot drift apart when the solution changes.

{: .important }
> The annotated file **is** the solution. It compiles, simulates, and passes its
> own tests exactly as it stands — there is no build step between you and a
> working file. Only the student version is generated.

A marker must be the whole comment. `// BEGIN SOLUTION` is a marker;
`x = 1; // BEGIN SOLUTION` is an ordinary line, so prose that happens to mention
a marker cannot change what ships.

### The two optional sections

Most holes need nothing more than the pair above. Two extra sections exist for
content the *solution* must not contain:

| Section        | Effect                                                | Use it when                                                          |
| -------------- | ----------------------------------------------------- | -------------------------------------------------------------------- |
| `BEGIN TODO` | Lines emitted verbatim into the student file          | The text would be wrong in the solution — `// y is not driven yet` |
| `BEGIN STUB` | Lines written commented, emitted **un**commented | The student file will not parse without filler                       |

{: .warning }
> `BEGIN TODO` lines are emitted **verbatim** — write them exactly as they should
> appear in the student file: an ordinary comment, at the indentation you want.
> Do **not** add a second comment prefix. Writing `//     // TODO: ...` ships
> `//     // TODO: ...`, double-commented and flattened against the left margin.
> `BEGIN STUB` is the section that strips a prefix; `BEGIN TODO` is not.

`BEGIN STUB` is rare but not dispensable. A Python function whose entire body is
inside a solution block leaves `def f():` followed by nothing, which is a syntax
error — and a lab whose files do not import scores zero for reasons that have
nothing to do with the student:

```python
def subc_divide(a, b, nbits=16):
    # TODO: Implement the conditional subtraction division algorithm
# BEGIN SOLUTION
    z = np.uint32(0)
    for _ in range(nbits):
        z <<= 1
    return z
# BEGIN STUB
#     return np.uint32(0)
# END SOLUTION
```

Students get `    return np.uint32(0)`. The prefix and one following space are
stripped, so the indentation you write after `# ` is the indentation they get.

Sections must appear in the order `SOLUTION` → `TODO` → `STUB` → `END SOLUTION`,
and blocks do not nest. Anything malformed is a hard error, never a warning —
a marker the parser had to guess at is a marker that might not remove what it was
meant to.

## `lab.toml`

Every file in the solution lab directory must be accounted for:

```toml
[lab]
name   = "prng"
public = "../../../hwdesign/labs/prng"

full    = ["prng_build.py", "tb_prng.sv", "readme.md"]
partial = ["prng.sv", "prng_model.py"]
private = ["notes.md"]
ignore  = ["scratch/"]
```

`public` is relative to the lab directory, and must point outside the solution
repository.

**A file in none of the lists is an error, not a default.** Both possible
defaults are bugs you discover after students do: silently not shipping means
they cannot build, and silently shipping whole means the answer key is public.

`ignore` is what keeps that rule livable. Build residue is ignored already —
`sim/`, `eval/`, `vectors/`, `results/`, `submission/`, `test_outputs/`,
`__pycache__/`, `*.zip`, `*.log`, and friends — so `ignore` is only for anything
unusual a particular lab leaves behind.

## Publishing

Yes, the copy into the student repository is automated. That is what `publish`
does — it writes across repositories, using the `public` path from `lab.toml`.

Run these from the `hwdesign-soln` root:

```bash
# Check the markers parse. Writes nothing.
python -m hwdesign.labkit lint labs/prng

# Show exactly what would be written, and write nothing.
python -m hwdesign.labkit publish labs/prng --dry-run

# Write the student tree.
python -m hwdesign.labkit publish labs/prng

# Exit 1 if the published tree differs from what the solution would produce.
python -m hwdesign.labkit check labs/prng
```

`check` is the one to run before committing, and the one to put in CI. It has to
run from the private side, because that is the only side that can see both trees.

After a publish there are changes in **two** repositories. Commit them
separately, and read the `hwdesign` diff before pushing it — it is the last human
look at what becomes public.

## What the guards will stop you doing

A publish fails, writing nothing, on any of these:

1. A file in the lab directory listed nowhere and matching no ignore pattern.
2. Unbalanced, nested, or out-of-order markers.
3. A marker token that would survive into a published file — usually an annotated
   file listed as `full`.
4. A line from inside a solution block appearing anywhere in the published tree.
5. A `public` path that overlaps the solution directory.
6. A file listed as `partial` that contains no `BEGIN SOLUTION` block — you either
   meant `full`, or you forgot to annotate it.

Guard 4 is the one that matters. It is the only check that catches a leak you
cannot see by reading the diff — a block closed a line early, or a file
misclassified in `lab.toml`. Short and structural lines (`end`, `);`) are ignored,
as is anything that also appears outside a solution block — including everything
in your `TODO` and `STUB` sections, which are student-facing by construction. So
a failure here is worth taking seriously rather than working around.

### When guard 4 is wrong

It fires on one thing that is not a leak: library boilerplate identical inside a
solution block and in a file shipped whole. Writing `prng` produced two —
`fig, ax = plt.subplots(figsize=(7.5, 4))` and `plt.close(fig)` appear in the
plotting solution and, character for character, in a helper in the build script.

Say so explicitly rather than contorting the solution to dodge it:

```toml
allow_shared = [
    "fig, ax = plt.subplots(figsize=(7.5, 4))",
    "plt.close(fig)",
]
```

The entries are exact stripped lines and excuse nothing else in the block, so the
override is narrow and sits in the manifest where it gets reviewed. Reach for it
only when you have looked at the flagged line and are sure it reveals nothing —
which is the whole point of making it a decision rather than a default.

## What the student does

Students never copy files out of `partial/` by hand. The lab's build script
declares each completable file with a `StudentSourceStep`:

```python
dag.add(StudentSourceStep(artifact="prng_sv", path=Path("prng.sv")))
```

On the first build this copies `partial/prng.sv` up to `prng.sv` and says so. It
**never overwrites** — once the student's file exists, the step only confirms it
is still there, and that holds under `--force` too. From then on that file's
timestamp is what drives the rebuild of everything downstream.

### Tell each graded stage which files are its own

Pass the source steps to the stage that grades them:

```python
pysim = PySimStep(name="pysim", title="Python LFSR model", starts_from=[prng_model_src])
```

When *every* file in `starts_from` is still byte-identical to its template, that
stage reports `not started` and scores zero rather than listing failed checks.

Do this on every graded stage. Without it, a student's very first command is
answered with a page of ✗ marks for work they have not yet had a chance to do —
a failing grade as the opening move, when nothing has actually gone wrong. Worse,
it is usually a *partial* score: checks like "produced 1000 samples" are
satisfied by the untouched template, so an unstarted lab collects points it has
not earned. In `prng` that was 7 out of 30 before this existed.

`evaluate()` still runs, so the stage's declared outputs are still produced and
the stages downstream still have something to read. Only what the student is told
changes.

Their loop is the DAG's, one stage at a time:

```
python prng_build.py --through prng_py     # score, and why
python prng_build.py --through prng_sim    # the next stage
python prng_build.py                       # everything, then the submission zip
```

Each graded stage scores itself and writes the result to disk, so `--grades`
reports their standing without rebuilding anything. How the scoring works, and
how the results reach Gradescope, is covered in
[Autograders and Gradescope](./gradescope.md).

## Creating a new lab

This is the order `prng` was actually built in, including the two steps that
turned out to matter most.

1. Create `hwdesign-soln/labs/<name>/` and write the lab **complete and working**.
   Annotating as you go is fine — the markers are comments, so the file still
   runs — but do not trust anything until the solution scores full marks.
2. Write `lab.toml`, classifying every file.
3. Run the solution end to end. **It must score 100%.** If the rubric cannot be
   satisfied by the reference implementation, it is the rubric that is wrong.
4. `lint`, then `publish --dry-run`, and read the output.
5. **Publish to a scratch directory and run the result as a student would** —
   see below. Do not skip this.
6. `publish` for real, then review the `hwdesign` diff by hand before committing.
7. Write the student-facing lab page under `hwdesign/docs/labs/<name>/`.

### Step 5 is the one that finds the bugs

Copy the lab to a temporary directory, point `public` at another temporary
directory, publish, and run the published tree with nothing filled in:

```bash
cp -r labs/prng /tmp/soln/labs/prng
sed -i 's|public = .*|public = "/tmp/pub/labs/prng"|' /tmp/soln/labs/prng/lab.toml
python -m hwdesign.labkit publish /tmp/soln/labs/prng
cd /tmp/pub/labs/prng && python prng_build.py
```

An untouched submission should score close to zero, and it must not crash. When
this was first run for `prng` it scored **18 out of 20**, for three separate
reasons that were invisible from reading the code:

- Both placeholder implementations returned 0, so the two languages "agreed"
  perfectly while implementing nothing, and the cross-language check paid full
  marks.
- A stream of all zeros satisfied "values are in range".
- A constant stream has zero variance, so its correlation is `NaN` — which was
  being read as "uncorrelated" and passing.

None of those is visible from the solution side, because the solution never
produces a degenerate stream. Two rules came out of it, worth applying to any lab
that grades one artifact against another:

**Grading consistency between two things the student wrote needs a floor.** Two
identical stubs are perfectly consistent. Require the compared data to be
non-trivial before consistency earns anything.

**Check what your rubric does with an empty or constant input**, not just a wrong
one. Degenerate cases pass tests that were written with wrong-but-plausible input
in mind.

### Other things worth knowing

**Put the lab's spec constants in the build script, not the student's file.** The
sample count, the seed, and the data width belong to the lab. Reading them from
the submission means a file that fails to import takes the grader down with it,
and lets a student change what they are graded against.

**Let a graded step run the simulator itself** rather than depending on a
separate `SvSimStep`. As its own DAG node, a failed compile raises and halts the
build, so a student with a syntax error gets a traceback and no submission file
at all. Run it inside `evaluate()` and a compile error becomes a scored zero with
the tool output as feedback.

**Only bundle files that always exist.** `GradeReportStep` fails if a bundled
file is missing, so a lab that bundles the simulator's output cannot produce a
submission for a student whose simulation did not run.
