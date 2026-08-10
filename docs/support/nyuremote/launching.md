---
title: Launching Vitis and Vivado
parent: NYU Remote Server
nav_order: 3
has_children: False
---
# Launching Vitis and Vivado within the Remote Server

## Tool version

The NYU EDA servers run version **2026.1** of Vitis and Vivado. Some of the course
material was developed against the slightly earlier 2025.1, and we will keep the labs
and demos working on both.

## Loading the tools

The tools are not on your path when you log in. Load them with a single command:

```bash
module load /home/shared/modules/xilinx
```

Then launch either tool by name:

```bash
vitis      # Vitis IDE
vivado     # Vivado IDE
```

That is the whole procedure. The `module load` also sets the license server, so nothing
else needs configuring.

{: .note }
> Run `module load` once per login session — it affects only the terminal you type it
> in. If you open a second terminal, run it again there.

## Checking that it worked

```bash
vitis -version
vivado -version
```

Both should report **2026.1**. If instead you get `Command not found`, you have not run
the `module load` in that terminal.

## Loading the tools automatically

If you would rather not type the command at every login, add it to the end of your
`~/.tcshrc` (the default shell on these servers is `tcsh`):

```bash
module load /home/shared/modules/xilinx
```

New logins will then have the tools available immediately. This is safe unless you are
also taking a course that needs a different Xilinx version, in which case it is better
to load it per session.

## The GUIs need a graphical connection

`vitis` and `vivado` with no arguments open full graphical applications. Over a plain
SSH connection they have nowhere to draw and will fail or hang. Connect with
[Fast-X](./fastx.md) first, or use the command-line tools instead — see
[Launching Vitis and Vivado](../amd/lauching.md) for what each tool does and for the
batch-mode commands such as `vitis-run --mode hls` and `xsim`.

---

Go to [setting up Git and GitHub](./github.md)
