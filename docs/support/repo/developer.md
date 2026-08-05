---
title: Developer Setup
parent: GitHub Repository
nav_order: 3
has_children: false
---

# Developer Setup

{: .note }
> This page is for **instructors and course assistants** who are developing
> course material — and especially for anyone who needs to change `waveflow`
> itself. If you are taking the course, you want
> [Installing the Python packages](./package.md) instead; nothing here is
> required to run the labs.

The student setup installs `waveflow` from GitHub as a fixed snapshot. That is
the right thing for a student and the wrong thing for a developer: to change
waveflow you would have to commit, push, and reinstall to see every edit. The
developer setup instead installs waveflow **editable from a local clone**, so
your edits take effect immediately.

## Setup

Clone both repositories side by side:

```bash
git clone https://github.com/sdrangan/hwdesign.git
git clone https://github.com/sdrangan/waveflow.git
```

Create and activate a virtual environment as described in
[Installing the Python packages](./package.md#2-create-and-activate-a-virtual-environment),
then install both packages editable from inside your `hwdesign` clone:

```bash
(env) pip install -e ../waveflow
(env) pip install -e .
```

The repository ships [`requirements-dev.txt`](https://github.com/sdrangan/hwdesign/blob/main/requirements-dev.txt)
which does both in one step:

```bash
(env) pip install -r requirements-dev.txt
```

{: .warning }
> **Check the path in that file first.** For historical reasons it currently
> reads `-e ../pysilicon`, because the original author's clone predates the
> rename from `pysilicon` to `waveflow` and the folder kept its old name. The
> package inside is `waveflow` either way — the folder name is cosmetic — but
> if you cloned into `../waveflow` as above, edit that line to match your
> layout (or use the two explicit `pip install -e` commands instead).

Verify with the same snippet as the student page — `waveflow.__file__` should
now point into your waveflow clone rather than into `site-packages`:

```python
import waveflow
print(waveflow.__file__)
```

## Three things that will eventually confuse you

**1. An editable install goes stale in one specific way.** Python *source* is
read live from the clone, so code edits need no reinstall. But the recorded
dependency list and the console-script shims (`sv_sim`, `waveflow_calib`, …) are
a snapshot taken at install time. If waveflow adds an entry point or a
dependency, your environment silently lacks it. Re-run the install:

```bash
(env) pip install -r requirements-dev.txt
```

**2. The install follows whichever branch is checked out.** An editable install
points at a *directory*, not a commit, so `git checkout` in your waveflow clone
silently changes what `import waveflow` returns. When course material breaks for
no apparent reason, check this before debugging anything else:

```bash
git -C ../waveflow branch --show-current
```

**3. Your environment is more capable than a student's.** It resolves waveflow
from your working clone, which may be on a feature branch containing work you
have not pushed. Course material written against that work will pass for you and
fail for every student. To catch this, verify against a student-like install
before publishing material — either in a second virtual environment built from
the [student instructions](./package.md), or by temporarily reinstalling
waveflow from GitHub:

```bash
(env) pip install --force-reinstall --no-deps git+https://github.com/sdrangan/waveflow.git
```

and switching back with `pip install -e ../waveflow` afterwards. The
`--force-reinstall` is needed because waveflow's version number does not change
on every commit.

## Where new code belongs

waveflow was created by splitting general-purpose tooling out of this repository,
and it is worth keeping that split clean — a previous version of this course
carried a vendored copy of the package, which drifted badly out of sync.

- **Would another waveflow user want this?** → it belongs **upstream in
  waveflow**.
- **Does it only make sense for *this course's* labs and units?** → it belongs
  in the `hwdesign` package here.

`hwdesign` depends on waveflow; waveflow must never depend on `hwdesign`. When
course-specific code matures into something generally useful, move it up into
waveflow rather than letting `hwdesign` grow into a second general-purpose
package.

## Regenerating the requirements files

`requirements.txt` pins exact versions; `requirements-loose.txt` is the same list
without version constraints. Regenerate them with:

```bash
python -m pip freeze > requirements.txt
```

Then strip the version pins — in Windows PowerShell:

```bash
(Get-Content requirements.txt) -replace "[<>=~!].*","" | Set-Content requirements-loose.txt
```

or on macOS / Linux:

```bash
sed 's/[<>=~!].*//' requirements.txt > requirements-loose.txt
```

Afterwards, edit `requirements.txt` by hand to remove lines that should not be
pinned for everyone:

- `pywin32==...` — Windows only.
- Any `-e git+https://github.com/...#egg=...` line — an artifact of the editable
  installs, not a dependency others should inherit.

{: .warning }
> The committed `requirements.txt` and `requirements-loose.txt` are stale: they
> are full environment freezes from before the waveflow migration and mention
> neither `waveflow` nor `hwdesign`. Use `requirements-dev.txt` for a developer
> setup and the [student instructions](./package.md) for a course setup until
> these two files are regenerated.
