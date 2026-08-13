---
title: Autograders and Gradescope
parent: Instructor Guide
nav_order: 3
has_children: false
---

# Autograders and Gradescope

{: .note }
> This page is a placeholder. It will be written once `prng` has been through a
> real Gradescope submission, so that it documents what the flow actually does
> rather than what it was designed to do.

## What already exists

The machinery is built and tested; only the write-up is pending.

**Grading is part of the build.** A lab's DAG is made of `GradedStep` nodes
(`hwdesign/grading.py`). Each one does its stage's work *and* scores it, writing
a JSON record to `eval/<step>.json`. A low score never halts the build — students
always reach the later stages with partial credit — while a genuine failure, one
that leaves the next step with nothing to read, does halt it.

**The submission is the terminal node.** `GradeReportStep` consumes every step's
eval record and writes `submission/submitted_results.json` plus the
`submission.zip` the student uploads. Because the records are its consumed
artifacts, it cannot bundle a stale score.

**Gradescope needs no changes.** The results file is written in the shape
`gradescope/autograde.py` already copies verbatim to
`/autograder/results/results.json`:

```json
{
  "score": 23.0,
  "tests": [
    {"name": "Python PRNG model", "score": 5.0, "max_score": 10.0, "output": "..."}
  ]
}
```

## What this page will cover

- Writing an `evaluate()` method, and the `Checks` accumulator that builds the
  feedback students see.
- Choosing what each step is worth, and why `points` is declared on the step
  rather than returned from `evaluate()`.
- `autograder_config.xml` and the required-files list.
- Building and uploading the autograder zip.
- The limits of the current model: scores are computed on the student's machine
  and uploaded, so the required-files list is the only check. This predates the
  build-DAG work and is unchanged by it.
