---
title: Installing the Python packages
parent: GitHub Repository
nav_order: 2
has_children: false
---

# Installing the Python packages

The course uses **two** Python packages. Knowing which is which will save you a
lot of confusion later:

| Package | Where it lives | What it is |
|---|---|---|
| `waveflow` | [separate repository](https://github.com/sdrangan/waveflow) | A general-purpose, Python-first hardware modeling and synthesis framework. It is not specific to this course, and is used for the simulation, timing analysis, code generation, and HLS/Vivado tooling throughout. [**Documentation**](https://sdrangan.github.io/waveflow/docs/) |
| `hwdesign` | this repository | A thin, course-specific layer *on top of* waveflow — autograder glue, lab scaffolding, and helpers that only make sense for this class. |

You install `waveflow` **from GitHub**; you install `hwdesign` **from your clone
of this repository**. You do not need to clone waveflow.

## 1. Clone the course repository

If you have not already, follow [Cloning the Repository](./repo.md). The rest of
this page assumes you are in the `hwdesign` directory that produced.

## 2. Create and activate a virtual environment

Create an environment named `env` (any name works). I usually run this in the
directory just outside `hwdesign`:

```bash
python -m venv env
```

This may take several minutes without showing progress. The resulting `env`
directory may be large.

Activate it:

```bash
.\env\Scripts\Activate.ps1   [Windows PowerShell]
.\env\Scripts\activate.bat   [Windows command prompt]
source env/bin/activate      [macOS / Linux]
```

On Windows PowerShell you may get *"...Activate.ps1 is not digitally signed. The
script will not execute on the system."* If so, run:

```bash
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Your prompt should now be prefixed with `(env)`. Everything below must be run
inside the activated environment.

## 3. Install waveflow

```bash
(env) pip install git+https://github.com/sdrangan/waveflow.git
```

This pulls waveflow and its dependencies (numpy, pandas, simpy, scikit-learn,
and others), so it will take a few minutes.

{: .warning }
> **Do not `pip install pywaveflow`.** There is a package by that name on PyPI,
> but it is a placeholder that only reserves the name — it contains a single
> file and none of the actual framework. Its own description tells you to
> install from GitHub, which is what the command above does. Installing it
> will not give you a working environment, and having both installed puts two
> packages in conflict over the same `waveflow` directory.

## 4. Install hwdesign

From inside your clone of this repository:

```bash
(env) pip install -e .
```

The `-e` ("editable") flag means Python reads the package straight from your
clone, so a `git pull` updates it with no reinstall.

> ⚠️ **Do steps 3 and 4 in that order.** `hwdesign` declares `waveflow` as a
> dependency, but waveflow is distributed from GitHub rather than PyPI. If you
> run `pip install -e .` in a fresh environment *before* installing waveflow,
> pip will search PyPI, fail to find it, and stop with
> `No matching distribution found for waveflow`. Installing waveflow first
> satisfies the dependency and everything resolves.

## 5. Verify the installation

```python
import importlib.metadata as md
import hwdesign, waveflow

print("hwdesign", md.version("hwdesign"))
print("waveflow", md.version("waveflow"))
print("waveflow loaded from", waveflow.__file__)
```

You should see a version number for each and a path for waveflow. If either
import raises `ModuleNotFoundError`, the most common cause is that the virtual
environment is not activated.

> If you get an error mentioning **`pysilicon`**, you have hit course material
> that has not yet been updated — see the note at the bottom of this page.

## Using the environment later

Activate the environment in every new terminal before running course material:

```bash
.\env\Scripts\Activate.ps1   [Windows PowerShell]
source env/bin/activate      [macOS / Linux]
```

Leave it with:

```bash
(env) deactivate
```

## Updating

To pick up new course material, pull this repository — the editable install
means there is nothing to reinstall:

```bash
git pull
```

To pick up a newer waveflow, reinstall it. The `--force-reinstall` is required
because waveflow's version number does not change on every update, so pip would
otherwise decide you are already up to date:

```bash
(env) pip install --force-reinstall --no-deps git+https://github.com/sdrangan/waveflow.git
```

## Note: material still being migrated

The course tooling is being moved onto waveflow one unit at a time. Material
that has not been converted yet will fail with a message beginning:

```
The vendored 'pysilicon' package has been removed - this course material has
not been migrated to waveflow yet.
```

That is expected, not a broken install — it means that particular demo or lab is
still queued for conversion. Your environment is fine.
