---
title: The two repositories
parent: Instructor Guide
nav_order: 1
has_children: false
---

# The two repositories

Course material lives in two repositories, and which one a file belongs in is
decided by a single question: *would a student seeing this spoil the work?*

| Repository | Visibility | Holds |
| --- | --- | --- |
| [`hwdesign`](https://github.com/sdrangan/hwdesign) | **public** | Everything students see — units, demos, docs, and the incomplete lab files they complete. |
| [`hwdesign-soln`](https://github.com/sdrangan/hwdesign-soln) | **private** | Full working solutions, exams, and autograder configuration. |

There is a third repository, [`waveflow`](https://github.com/sdrangan/pysilicon)
(cloned as `pysilicon`), which holds the general-purpose hardware design library
this course is built on. It is not course material — see the design rule at the
top of `hwdesign/__init__.py` for what belongs there rather than here.

## Why two, and why it cannot be one

A private branch, a `.gitignore` entry, or a filtered push would all be simpler.
None of them is safe, because they all fail the same way: **a solution that
reaches the public repository's history is public permanently.** Deleting the
file in a later commit does not help — the object is still in the history, and on
GitHub it stays reachable through the API even after a force-push.

So the direction is fixed and one-way:

```
hwdesign-soln/labs/prng/     the source — full, working, annotated
        │
        │   python -m hwdesign.labkit publish
        ▼
hwdesign/labs/prng/          a build output — never edited by hand
```

{: .warning }
> Nothing under `hwdesign/labs/<lab>/` should ever be hand-edited once a lab is
> published. It is generated, and the next publish will silently overwrite your
> change. Edit the annotated solution instead. See
> [Creating and publishing labs](./labs.md).

## Setting up VS Code

Both repositories are checked out as siblings:

```
repos/
    hwdesign/
    hwdesign-soln/
    pysilicon/          (waveflow)
```

Open them together as one VS Code *workspace* rather than as separate windows —
searching across both at once is most of the value, and the relative paths in
`lab.toml` assume the sibling layout above.

**File → Add Folder to Workspace**, then **File → Save Workspace As**. The result
is `hwdesign.code-workspace` at the repository root:

```json
{
    "folders": [
        { "path": "." },
        { "path": "../pysilicon" },
        { "path": "../hwdesign-soln" }
    ]
}
```

Open that file (**File → Open Workspace from File**) and all three appear in the
Explorer as separate top-level folders, each with its own source control.

{: .note }
> Because the folders are separate repositories, VS Code's Source Control panel
> shows three independent sets of changes. A commit in one does not touch the
> others, which is the point — but it does mean publishing a lab produces changes
> in *two* repositories that need committing separately.

## Setting up Claude Code

If you use Claude Code in this workspace, adding a folder to the VS Code
workspace does **not** give Claude access to it. Those are separate lists.

For one session:

```
/add-dir ../hwdesign-soln
```

To make it persistent, add it to `.claude/settings.json` in `hwdesign`:

```json
{
    "permissions": {
        "additionalDirectories": ["../hwdesign-soln", "../pysilicon"]
    }
}
```

## Python environment

`hwdesign` depends on `waveflow`, which during development is installed editable
from the local `pysilicon` clone. From the `hwdesign` root:

```
pip install -e ../pysilicon
pip install -e .
```

The second line is what makes `python -m hwdesign.labkit` work from inside
`hwdesign-soln`, which is where you will run it.

Run the test suite from the `hwdesign` root with `pytest`. It is tiered: most of
it is pure Python and takes seconds, and the tests that drive Vivado are marked
`vivado` and skip automatically when the simulator is not installed.
