---
title: Launching Vitis and Vivado
parent: NYU Remote Server
nav_order: 3
has_children: False
---
# Launching Vitis and Vivado within the Remote server

## NYU Server Version

At the time of writing, the NYU EDA servers have been upgraded to version 2026.1 of the Vitis and Vivado tools.  We will ensure that the labs and demos work for this version, even though some of the material was developed for a slightly earlier 2025.1 version.

## Environment Variable Problem

The NYU EDA servers are configured to set paths to software for different classes.  At the time of writing, there appears to be a mis-configuration of an environment variable for the Cadence software that is not needed for this class.  

The problem is in the file, `tcshrc_cadence_local`.  This file mis-sets an environment variable `LD_PRELOAD`.  `LD_PRELOAD` forces a shared library into *every* program you run, so a setting meant for Cadence also reaches Vitis, Vivado, and Python — where it can produce loader or missing-symbol errors that look nothing like a Cadence problem.

For this class, unset the variable:

```bash
unsetenv LD_PRELOAD
```

That fixes the current shell only.  To avoid retyping it at every login, add the
same line to the **end** of your own `~/.tcshrc`.  Your account ships with a
`~/.tcshrc` that sources the EDA setup files first and applies your own settings
afterwards, so anything you add at the bottom takes precedence:

```bash
# Sources of all application files  (installed by NYU IT)
source ~/tcshrc_cadence_local
source ~/tcshrc_mentor_local
source ~/tcshrc_synopsys_local
source ~/tcshrc_xilinx_local
echo 'EDA tools: environment files sourced'

# Your own settings
setenv PATH "$HOME/.local/bin:$PATH"
unsetenv PYTHONPATH
unsetenv LD_PRELOAD
```

The `PATH` and `PYTHONPATH` lines come from [setting up Python](./python.md); the
`LD_PRELOAD` line is the one to add here.  Because they sit below the `source`
commands, they override whatever the EDA files set.

Then open a fresh login and confirm it is gone:

```bash
echo $LD_PRELOAD
```

This should print nothing.

{: .warning }
> Do **not** delete the line from `~/tcshrc_cadence_local` itself.  NYU IT
> installs those files into your home directory and may replace them when
> accounts are re-provisioned — silently undoing your change and leaving you to
> rediscover the problem.  You may also need Cadence for another course.
> Unsetting the variable at the end of your own `~/.tcshrc` has exactly the same
> effect, survives IT updates, and is a single line to remove if you ever want
> the original behaviour back.


## Tool Version Problem

Your account automatically sources `~/tcshrc_xilinx_local` at login, and that file
puts the **old 2023.2** tools on your path:

```bash
setenv XILINX /eda/xilinx/
set path=( $path $XILINX/Vivado/2023.2/bin $XILINX/Vitis_HLS/2023.2/bin $XILINX/DocNav )
```

So if you log in and simply type `vivado`, you get version **2023.2**, not the
2026.1 version this class uses — and nothing warns you.  The same applies to
`vitis_hls`, which is the 2023.2 HLS tool; in 2026.1 the HLS flow is
`vitis-run --mode hls` instead.

This matters because Xilinx project files are generally **not** backward
compatible.  Using the old tools by accident usually does not fail immediately;
it fails later, with confusing errors about a project built by a newer version.

You must therefore run the settings command for 2026.1 in each session before
using the tools:

```bash
source /eda/xilinx/2026.1/Vivado/settings64.csh    # for Vivado
source /eda/xilinx/2026.1/Vitis/settings64.csh     # for Vitis
```

{: .important }
> Always confirm which version you actually have before starting work:
>
> ```bash
> vivado -version
> vitis --version
> ```
>
> If either reports 2023.2, you are on the old tools and have not sourced the
> settings file.  (Note the inconsistent flags: `vivado` takes one dash,
> `vitis` takes two.)

If you would rather not type this at every login, you can add the `source` lines
to the end of your own `~/.tcshrc`, below the other settings described above.
Only do this if you are not also taking a course that needs the 2023.2 tools,
since it changes the default for every session.

## Launching Vitis and Vivado

Once you have SSH-ed or connected via Fast-X into one of the NYU EDA servers, 
you can follow the [launching instructions](../amd/lauching.md) to start either the Vitis or Vivado tools.

---

Go to [running python remotely](./python.md)
