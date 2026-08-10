---
title: Launching Vitis and Vivado
parent: Vitis and Vivado
nav_order: 3
has_children: false
---
# Launching Vitis and Vivado

## Vitis and Vivado Tools

Both Vitis and Vivado have various tools.  For Vitis, the tools we will use in the classs are:

- `vitis` — Launches the Vitis IDE or runs Vitis workflows from the command line.
- `vitis-run` — Builds and runs Vitis applications, including host code and hardware kernels.  We typically use a format of the form:

```bash
    vitis-run --mode hls --tcl <tclfile.tcl>
```

For Vivado, the tools are:

- `vivado` — Starts the Vivado IDE or runs synthesis/implementation scripts in batch mode.
- `xvlog` — Compiles Verilog/SystemVerilog source files for simulation.
- `xelab` — Elaborates the compiled design and creates a simulation snapshot.
- `xsim` — Runs the simulation using the snapshot, with optional GUI or batch execution.

## Launching the Vitis or Vivado GUI in Windows

In Windows, you can run both the Vitis IDE and Vivado IDE from the **Start menu** by clicking the Windows button  and typing "Vivado" or "vitis" into the search bar.  Either operation is equivalent to running `vitis` or `vivado` from the command line.

## Setting the Path for Command Line Tools

To use any command line tool, you will need to set the path.  In the instructions below, I have assumed that users working locally on Linux and Windows are on version 2025.1, while users on the NYU remote machine are on the newer 2026.1.  I will test the demos and labs to make sure everything works on both versions as the semester progresses.

{: .important }
> **On the NYU servers, do not use the `settings64` commands below.**  There you load
> the tools with a single `module load` instead — see
> [Launching Vitis and Vivado on the NYU server](../nyuremote/launching.md).

For a Vivado command line tool:

* In Windows, open a Command Shell, not a Powershell.  In Linux, open any terminal.
* Find the path the Vivado for the version you want to use:
  * On Linux, it is likely in `/tools/Xilinx/Vivado/2025.1`
  * On the [NYU remote server](../nyuremote/), the latest version is currently in `/eda/xilinx/2026.1/Vivado/`
  * On Windows, is is likely in `c:\Xilinx\2025.1\Vivado`
* Run the settings command:
  * On Linux: `source <vivado_path>/settings64.sh`
  * On the [NYU remote server](../nyuremote/), `source <vivado_path>/settings64.csh`  (Note that you need the `.csh` since the default shell is `tcsh`)
  * On Windows: `<vivado_path>/settings64.bat`
* You can now run a command like `vivado -version`.
  * Note:  It is not `vivado --version` (two dashes)

The steps are similar for Vitis tools:

* Determine where the vitis tool is located:
  * In Linux: `vitis` and `vitis-run` are typically located in a directory like `/tools/Xilinx/Vitis/2025.1`
  * On the [NYU remote server](../nyuremote/), the latest version is currently in `/eda/xilinx/2026.1/Vitis/`
  * In Windows: `vitis` and `vitis-run` are typically located in a directory like `c:\Xilinx\2025.1\Vitis`
* In that directory:
  * In Linux, run `source settings64.sh`
  * In Windows Command Shell (not Powershell), run: `settings64.bat`
* Then, in the terminal run:
  * `vitis --version` to get the version (Note:  This command has two dashes!)
  * `vitis` for the Vitis GUI
  * `vitis-run --mode hls --tcl <tclfile.tcl>`
