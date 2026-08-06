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
same line to the end of your own `~/.tcshrc` — the file you already edited when
[setting up Python](./python.md):

```bash
unsetenv LD_PRELOAD
```

Then open a fresh login and confirm it is gone:

```bash
echo $LD_PRELOAD
```

This should print nothing.  If it still shows a value, your `~/.tcshrc` is being
read *before* the Cadence settings; in that case keep using the one-off
`unsetenv LD_PRELOAD` after logging in, and let the instructor know.

{: .warning }
> Do **not** edit `tcshrc_cadence_local` itself.  It belongs to the NYU IT
> department's setup and is shared with other classes that *do* use Cadence, so
> changing it could break a different course you are taking.  It may also be
> restored without warning when accounts are re-provisioned, silently undoing
> your change.  Unsetting the variable in your own `~/.tcshrc` has the same
> effect, is reversible, and affects nobody else.


## Launching Vitis and Vivado

Once you have SSH-ed or connected via Fast-X into one of the NYU EDA servers, 
you can follow the [launching instructions](../amd/lauching.md) to start either the Vitis or Vivado tools.

---

Go to [running python remotely](./python.md)
