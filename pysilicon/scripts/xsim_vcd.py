"""
xsim_vcd.py — Run Vivado simulation with VCD output

This script re-runs a Vivado HLS RTL simulation using `xsim` and generates a VCD (Value Change Dump) file
for waveform analysis. It is intended for use on Windows systems where Vivado is installed.

Usage (CLI):
First, run RTL co-simulation in Vitis HLS to generate the necessary simulation files.
In that simulation, enable trace capture with a setting such as `trace_level all`
or `trace_level port`.
Then, run this script from the command line:
```bash
    python xsim_vcd.py --top <top_function> [--comp <component_name>] [--out <output_file>]
```

Arguments:
    --top    (required) Name of the top-level function to simulate
    --comp   (optional) Name of the HLS component directory (default: 'hls_component')
    --out    (optional) Output VCD filename (default: 'dump.vcd')
        --trace_level (optional) VCD trace level. Built-in values `*`, `all`, and
            `port` reuse the trace selection from the generated simulation Tcl. You
            can also specify a custom hierarchical target such as `/top_function/*`.

Example:
```bash
    python xsim_vcd.py --top add  --out wave.vcd
```

This will run the simulation for the top function `add` in the component directory `hls_component`
and output the VCD file as `vcd/wave.vcd`.

Python API:
    You can also call this module from Python directly::

        from pysilicon.scripts.xsim_vcd import run_xsim_vcd
        from pathlib import Path

        out_path = run_xsim_vcd(
            top="poly",
            comp="pysilicon_poly_proj",
            out="dump.vcd",
        )
        print(f"VCD written to: {out_path}")
"""

import os
import sys
import shutil
import subprocess
import re
import argparse
from pathlib import Path


def _get_log_vcd_command(lines, trace_level):
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('log_wave '):
            if trace_level in {'*', 'all', 'port'}:
                return f"{stripped.replace('log_wave', 'log_vcd', 1)}\n"
            return f'log_vcd {trace_level}\n'

    raise RuntimeError(
        'Could not find a log_wave command in the simulation TCL. '
        'Re-run co-simulation with trace capture enabled before generating a VCD.'
    )


def modify_tcl(tcl_path, tcl_vcd_path, trace_level):
    with open(tcl_path, 'r') as f:
        lines = f.readlines()

    log_vcd_command = _get_log_vcd_command(lines, trace_level)

    # Insert VCD commands before log_wave
    for i, line in enumerate(lines):
        if line.strip().startswith('log_wave '):
            lines = lines[:i] + ['open_vcd\n', log_vcd_command] + lines[i:]
            break

    # Replace final lines
    for i in range(len(lines)):
        if lines[i].strip() == 'run all' and i + 1 < len(lines) and lines[i + 1].strip() == 'quit':
            lines[i + 1] = 'close_vcd\nquit\n'
            break

    with open(tcl_vcd_path, 'w') as f:
        f.writelines(lines)

def create_vcd_batch(top_name, original_bat, new_bat):
    with open(original_bat, 'r') as f:
        for line in f:
            if 'xsim' in line:
                xsim_line = line.replace(f'{top_name}.tcl', f'{top_name}_vcd.tcl')
                break
        else:
            raise RuntimeError("No xsim line found in batch file.")

    with open(new_bat, 'w') as f:
        f.write('cd /d "%~dp0"\n')
        f.write(xsim_line)

def run_batch(batch_path):
    subprocess.run(batch_path, shell=True, check=True)

def copy_vcd(sim_dir, base_dir, component_path, output_vcd):
    src = os.path.join(sim_dir, 'dump.vcd')
    if not os.path.exists(src):
        print("⚠️ dump.vcd not found.")
        return

    vcd_dir = os.path.join(base_dir, 'vcd')
    os.makedirs(vcd_dir, exist_ok=True)

    dst = os.path.join(vcd_dir, output_vcd)
    shutil.copyfile(src, dst)
    print(f"✅ VCD copied to {dst}")

def parse_args():
    parser = argparse.ArgumentParser(description="Process VCD dump options.")

    parser.add_argument(
        "--comp",
        type=str,
        default="hls_component",
        help="Component name (default: hls_component)"
    )
    parser.add_argument(
        "--top",
        type=str,
        required=True,
        help="Top-level function name (required)"
    )
    parser.add_argument(
        "--out",
        type=str,
        default="dump.vcd",
        help="Output VCD filename (default: dump.vcd)"
    )
    parser.add_argument(
        "--soln",
        type=str,
            default="solution1",
        help="Solution name (default: solution1)"
    )
    parser.add_argument(
        "--trace_level",
        type=str,
        default="*",
        help="VCD trace level (default: *)"
    )
    return parser.parse_args()


def run_xsim_vcd(
    top: str,
    comp: str = "hls_component",
    out: str = "dump.vcd",
    soln: str | None = "solution1",
    trace_level: str = "*",
    workdir: str | Path | None = None,
) -> Path:
    """
    Generate a VCD file by re-running a Vivado HLS RTL simulation.

    This function performs the same steps as the CLI entry point but is
    callable from Python.  It modifies the simulation TCL and batch files
    to enable VCD logging, runs the simulation, and copies the resulting
    ``dump.vcd`` to the output location.

    Parameters
    ----------
    top : str
        Name of the top-level function to simulate (required).
    comp : str
        Name of the HLS component directory.  Default: ``'hls_component'``.
    out : str
        Output VCD filename (written inside a ``vcd/`` subdirectory of
        *workdir*).  Default: ``'dump.vcd'``.
    soln : str | None
        Solution name inside the component directory.  When ``None`` the
        single sub-directory of *comp* is used automatically.  Default:
        ``'solution1'``.
    trace_level : str
        VCD trace level.  Built-in values ``'*'``, ``'all'``, and ``'port'``
        reuse the trace selection recorded in the generated simulation TCL.
        You can also pass a specific hierarchical path for a custom
        ``log_vcd`` target.
    workdir : str | Path | None
        Working directory that contains the *comp* component folder.
        Defaults to the current working directory.

    Returns
    -------
    Path
        Absolute path to the written VCD file.

    Raises
    ------
    RuntimeError
        If the platform is not Windows, if required simulation files are
        missing, or if the simulation process fails.
    FileNotFoundError
        If the expected simulation directory does not exist.
    """
    if os.name != 'nt':
        raise RuntimeError(
            "run_xsim_vcd only works on Windows (Vivado xsim is Windows-only)."
        )

    base_dir = str(Path(workdir).resolve()) if workdir is not None else os.getcwd()
    component_name = comp
    top_name = top
    output_vcd = out
    solution_name = soln
    component_path = os.path.join(base_dir, component_name)

    if solution_name is None:
        subdirs = [d for d in os.listdir(component_path) if os.path.isdir(os.path.join(component_path, d))]
        if len(subdirs) == 0:
            raise RuntimeError(
                f"No subdirectories found in {component_path}. Please specify a solution name."
            )
        elif len(subdirs) > 1:
            raise RuntimeError(
                f"Multiple subdirectories found in {component_path}: {subdirs}. "
                "Please specify a solution name via 'soln'."
            )
        else:
            solution_name = subdirs[0]
    soln_path = os.path.join(component_path, solution_name)

    sim_dir_candidates = [
        os.path.join(soln_path, 'hls', 'sim', 'verilog'),
        os.path.join(soln_path, 'sim', 'verilog')
    ]
    sim_dir = None
    for candidate in sim_dir_candidates:
        if os.path.exists(candidate):
            sim_dir = candidate
            break
    if sim_dir is None:
        raise FileNotFoundError(
            f"No valid simulation directory found. Checked: {sim_dir_candidates}"
        )

    tcl_path = os.path.join(sim_dir, f'{top_name}.tcl')
    tcl_vcd_path = os.path.join(sim_dir, f'{top_name}_vcd.tcl')
    bat_path = os.path.join(sim_dir, 'run_xsim.bat')
    bat_vcd_path = os.path.join(sim_dir, 'run_xsim_vcd.bat')

    modify_tcl(tcl_path, tcl_vcd_path, trace_level)
    create_vcd_batch(top_name, bat_path, bat_vcd_path)
    run_batch(bat_vcd_path)
    copy_vcd(sim_dir, base_dir, component_path, output_vcd)

    vcd_dir = os.path.join(base_dir, 'vcd')
    return Path(os.path.join(vcd_dir, output_vcd)).resolve()


def main():

    # Check if OS is Windows.  If not declare error and exit.
    if os.name != 'nt':
        print("❌ This script only works on Windows.  I will try to add a linux version later.")
        sys.exit(1)

    # Get arguments
    args = parse_args()
    component_name = args.comp
    top_name = args.top
    output_vcd = args.out
    solution_name = args.soln
    trace_level = args.trace_level

    # Get directory paths
    base_dir = os.getcwd()
    component_path = os.path.join(base_dir, component_name)

    # Set soln_path to either the provided component_path/solution or name
    # or the first directory below component_path.  If there are multiple directories,
    # print an error and list the sub-directories.
    if solution_name is None:
        subdirs = [d for d in os.listdir(component_path) if os.path.isdir(os.path.join(component_path, d))]
        if len(subdirs) == 0:
            print(f"❌ No subdirectories found in {component_path}. Please specify a solution name with --soln.")
            sys.exit(1)
        elif len(subdirs) > 1:
            print(f"❌ Multiple subdirectories found in {component_path}. Please specify a solution name with --soln.")
            print("Subdirectories:")
            for d in subdirs:
                print(f"  - {d}")
            sys.exit(1)
        else:
            solution_name = subdirs[0]
    soln_path = os.path.join(component_path, solution_name)

    # Get candidate sim directories
    sim_dir_candidates = [
        os.path.join(soln_path, 'hls', 'sim', 'verilog'),
        os.path.join(soln_path, 'sim', 'verilog')
    ]
    # Test if any of the candidate directories exist.  If not, print an error and exit.
    found_sim_dir = False
    for sim_dir in sim_dir_candidates:
        if os.path.exists(sim_dir):
            found_sim_dir = True
            break
    if not found_sim_dir:
        print("❌ No valid simulation directory found. Please check your solution structure.")
        print("Checked the following directories: ")
        for d in sim_dir_candidates:
            print(f"  - {d}")
        sys.exit(1)

    tcl_path = os.path.join(sim_dir, f'{top_name}.tcl')
    tcl_vcd_path = os.path.join(sim_dir, f'{top_name}_vcd.tcl')
    bat_path = os.path.join(sim_dir, 'run_xsim.bat')
    bat_vcd_path = os.path.join(sim_dir, 'run_xsim_vcd.bat')

    if not os.path.exists(sim_dir):
        raise FileNotFoundError(f"Simulation directory not found: {sim_dir}")

    modify_tcl(tcl_path, tcl_vcd_path, trace_level)
    create_vcd_batch(top_name, bat_path, bat_vcd_path)
    run_batch(bat_vcd_path)
    copy_vcd(sim_dir, base_dir, component_path, output_vcd)

if __name__ == "__main__":
    main()
