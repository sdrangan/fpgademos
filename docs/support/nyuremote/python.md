---
title: Using Python
parent: NYU Remote Server
nav_order: 4
has_children: False
---
# Using Python 

The NYU EDA servers provide a system Python installation, but **`pip` is not available** and you do **not** have permission to install system‑wide packages.  
To work around this, students should use **`uv`**, a modern, fast, user‑level Python package manager that installs entirely in your home directory.
This suggestion was provided by the student Ashesh Kaji, so please thank him next time.

**'`uv`** is a drop‑in replacement for:
- `pip`
- `virtualenv`
- `pipx`
- `pip-tools`
- `poetry` (for basic workflows)

It requires **no sudo access** and works perfectly on the NYU servers.

---

## 1. Install `uv`

Log into the EDA server:

```bash
ssh <netid>@ecs02.poly.edu
```

Then install `uv` into your home directory:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

This command installs `uv` as a local binary in the directory `~/.local/bin`.
We need to add that directory to your path.  Linux has different *shells*, and
the commands differ depending on which one you use.  Check your shell with:

```bash
echo $SHELL
```

The output ends in either `tcsh` or `bash`.  Follow the matching section below —
**the commands are not interchangeable.**  You can edit the file with any Linux
editor, such as `vi`.

### If your shell is `tcsh`

Add these lines to the end of `~/.tcshrc`, which adds `uv` to your path and
disables the system Python:

```bash
setenv PATH "$HOME/.local/bin:$PATH"
unsetenv PYTHONPATH
```

Then reload the shell configuration:

```bash
source ~/.tcshrc
```

### If your shell is `bash`

Add these lines to the end of `~/.bashrc` instead:

```bash
export PATH="$HOME/.local/bin:$PATH"
unset PYTHONPATH
```

Then reload the shell configuration:

```bash
source ~/.bashrc
```

### Both shells

You only need to do this once.  Subsequent logins will run the configuration
automatically.

You can verify installation with:

```bash
uv --version
```

---

## 2. Create a Virtual Environment

Navigate to the directory where you [cloned the `hwdesign` repo](../repo/repo.md).
Generally, this is `~/hwdesign`.
Inside that project directory:

```bash
uv venv
```

This creates a `.venv/` folder containing a private Python environment.

Activate it:  

```bash
source .venv/bin/activate.csh  # for tcsh
source .venv/bin/activate      # for bash
```

Your prompt should now show something like:

```
(.venv) <netid>@ecs02:~/hwdesign$
```

You can deactivate with:

```
deactivate
```

## 3. Install the course packages

The course uses two packages: **`waveflow`** (a general-purpose hardware
modeling framework, kept in a [separate repository](https://github.com/sdrangan/waveflow))
and **`hwdesign`** (this course's own helpers, in this repo).  See
[Installing the Python packages](../repo/package.md) for what each one does —
this page covers only the `uv` commands you need on the NYU servers.

From the `hwdesign` directory, with the virtual environment activated, install
waveflow first:

```bash
uv pip install git+https://github.com/sdrangan/waveflow.git
```

Then install `hwdesign` itself as editable:

```bash
uv pip install -e .
```

> ⚠️ **Run these two commands in this order.** `hwdesign` depends on
> `waveflow`, but waveflow is distributed from GitHub rather than PyPI.  If you
> run `uv pip install -e .` first, the install fails because it cannot find
> `waveflow` on PyPI.  Installing waveflow first satisfies the dependency.

{: .note }
> Do **not** use `requirements.txt` here.  That file is a pre-migration snapshot
> of a different environment and does not list either package; the two commands
> above are the complete install.

{: .warning }
> Do **not** `uv pip install pywaveflow`.  The PyPI package of that name is a
> placeholder that only reserves the name — it contains none of the actual
> framework.  Install waveflow from GitHub as shown above.

Verify that both packages are importable:

```bash
python -c "import hwdesign, waveflow; print('OK')"
```

If this raises `ModuleNotFoundError`, the usual cause is that the virtual
environment is not activated.  If it raises an error mentioning `pysilicon`,
that is unmigrated course material rather than a broken install — see the note
at the end of [Installing the Python packages](../repo/package.md).

## 4. Running Python

With the environment activated, run scripts with plain `python`:

```bash
python your_script.py
```

Console scripts such as `sv_sim` are on your path once the environment is
activated:

```bash
sv_sim --source [source files] --tb [tb_files]
```

Everything runs inside your private environment, not the system Python.

{: .warning }
> Prefer the activated environment over `uv run`.  Because this directory
> contains a `pyproject.toml`, `uv run` treats it as a project and may try to
> re-resolve its dependencies before running — which fails, since `waveflow` is
> not on PyPI.  If you see a resolution error mentioning `waveflow`, activate
> the environment and run `python` directly as shown above.

---

## 5. Why We Use `uv` Instead of `pip`

The NYU EDA servers:

- Do **not** include `pip`
- Do **not** allow system‑wide package installation
- Use a system Python that students cannot modify

`uv` solves all of these problems:

- Installs into your **home directory**
- Requires **no sudo**
- Manages virtual environments automatically
- Works on macOS, Windows, and Linux
- Is significantly faster and more reliable than pip

    