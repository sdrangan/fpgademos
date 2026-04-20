
from __future__ import annotations

from pathlib import Path
from typing import List

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from vcdvcd import VCDVCD

from pysilicon.hw.arrayutils import read_array
from pysilicon.utils.vcd import VcdParser
from pysilicon.utils.timing import TimingDiagram

# Import conv2d schemas (sibling module)
from conv2d_demo import Conv2DCmd, Conv2DResp, Conv2DDebug, Conv2DEvent

class Conv2DTimingResult:
    """
    Container for the decoded results of a conv2d VCD timing analysis.

    Attributes
    ----------
    clk_name : str
        Full VCD signal name of the clock.
    clk_period : float
        Estimated clock period in nanoseconds.
    in_signals : dict[str, str]
        AXI4-Stream signal name mapping for the input stream.
    out_signals : dict[str, str]
        AXI4-Stream signal name mapping for the output stream.
    bursts_in : list[dict]
        Raw burst dictionaries extracted from the input stream.
    bursts_out : list[dict]
        Raw burst dictionaries extracted from the output stream.
    cmd_hdr : PolyCmdHdr
        Decoded command header (tx_id, coeffs, nsamp).
    x : numpy.ndarray
        Input sample array decoded from the input data burst.
    resp_hdr : PolyRespHdr
        Decoded response header (tx_id echo).
    y : numpy.ndarray
        Output sample array decoded from the output data burst.
    resp_ftr : PolyRespFtr
        Decoded response footer (nsamp_read, error).
    vp : VcdParser
        The underlying VCD parser instance (for advanced use).
    """

    def __init__(self) -> None:
        self.clk_name: str | None = None
        self.clk_period: float | None = None
        self.in_signals: dict = {}
        self.out_signals: dict = {}
        self.dbg_signals: dict = {}
        self.cmd_time : float | None = None
        self.resp_time : float | None = None
        self.dbg_times : List[float] = []
        self.cmd: Conv2DCmd | None = None
        self.resp: Conv2DResp | None = None
        self.dbg: List[Conv2DDebug] = []
        self.vp: VcdParser | None = None    

def extract_bursts(vcd_path: str | Path) -> tuple[List[dict], float]:
    """
    Analyze a VCD file captured from the conv2d Vitis HLS kernel.

    Loads the VCD, extracts the AXI4-Stream input, output and debug signals,
    extracts bursts and returns a list of the bursts.

    Parameters
    ----------
    vcd_path : str | Path
        Path to the VCD file to analyze.

    Returns
    -------
    bursts : list[dict]
        List of the bursts each burst[i] has the elements:
        - 'tstart': the start time of the burst in nanoseconds
        - 'type': the type of the burst, one of 'Conv2DCmd', 
          'Conv2DDebug', 'Conv2DResp'
        - 'data': the decoded data of the burst, one of 
          Conv2DCmd, Conv2DDebug, Conv2DResp
    clk_period : float
        Estimated clock period in nanoseconds.

    Raises
    ------
    FileNotFoundError
        If *vcd_path* does not exist.
    ValueError
        If the expected signals or burst structure are not found in the VCD.
    """
    vcd_path = Path(vcd_path)
    if not vcd_path.exists():
        raise FileNotFoundError(f"VCD file not found: {vcd_path}")

    # Parse VCD
    vcd = VCDVCD(str(vcd_path), signals=None, store_tvs=True)

    # Set up VCD parser
    vp = VcdParser(vcd)

    # Discover clock signal
    clk_name = vp.add_clock_signal()

    # Discover AXI4-Stream signals
    in_stream_name = f"in_stream_"
    out_stream_name = f"out_stream_"
    dbg_stream_name = f"debug_stream_"

    in_signals, _in_bw = vp.add_axiss_signals(
        name=in_stream_name,
        short_name_prefix="in_stream",
        ignore_multiple=True,
    )
    out_signals, _out_bw = vp.add_axiss_signals(
        name=out_stream_name,
        short_name_prefix="out_stream",
        ignore_multiple=True,
    )
    dbg_signals, _dbg_bw = vp.add_axiss_signals(
        name=dbg_stream_name,
        short_name_prefix="debug_stream",
        ignore_multiple=True,
    )

    # Initialize the burst list
    bursts = []

    # Extract input bursts 
    bursts_in, clk_period = vp.extract_axis_bursts(
        clk_name, in_signals
    )
    for i, burst in enumerate(bursts_in):
        cmd = Conv2DCmd()
        words = burst['data']
        cmd.deserialize(words, word_bw=_in_bw)
        b = {'tstart': burst['tstart'], 'type' : 'Conv2DCmd', 'data' : cmd}
        bursts.append(b)

    
    # Extract the debug event bursts
    bursts_dbg, _ = vp.extract_axis_bursts(
        clk_name, dbg_signals
    ) 
    for i, burst in enumerate(bursts_dbg):
        dbg = Conv2DDebug()
        words = burst['data']
        dbg.deserialize(words, word_bw=_dbg_bw)
        b = {'tstart': burst['tstart'], 'type': 'Conv2DDebug', 'data' : dbg}
        bursts.append(b)

    # Extract the output burst
    bursts_out, _ = vp.extract_axis_bursts(
        clk_name, out_signals
    )
    for i, burst in enumerate(bursts_out):
        resp = Conv2DResp()
        words = burst['data']
        resp.deserialize(words, word_bw=_out_bw)
        b = {'tstart': burst['tstart'], 'type': 'Conv2DResp', 'data' : resp}
        bursts.append(b)
    return bursts, clk_period

class Conv2DTimingInfo(object):
    def __init__(self):
        self.bursts: List[dict] = []
        self.clk_period: float | None = None
        self.nrows: int | None = None
        self.ncols: int | None = None
        self.tcmd : float | None = None
        self.tresp : float | None = None
        self.times : dict[str, np.ndarray] = {}
        self.stage_df : pd.DataFrame | None = None

def analyze_timing(
        bursts: List[dict], 
        clk_period: float):
    
    # Create the empty timing info object
    timing_info = Conv2DTimingInfo()
    timing_info.bursts = bursts
    timing_info.clk_period = clk_period
    
    # Get the command and response burst
    cmd_burst = None
    resp_burst = None
    for b in bursts:
        if b["type"] == "Conv2DCmd":
            cmd_burst = b
            tcmd = b['tstart']
            cmd = cmd_burst['data']
            nrows = cmd.val['nrows']
            ncols = cmd.val['ncols']
        elif b["type"] == "Conv2DResp":
            resp_burst = b
            tresp = b['tstart']

    if cmd_burst is None:
        raise ValueError("No Conv2DCmd burst found in the VCD data")
    if resp_burst is None:
        raise ValueError("No Conv2DResp burst found in the VCD data")
    
    # Save command and response times
    timing_info.tcmd = tcmd
    timing_info.tresp = tresp

    # Get the debug bursts
    times = dict()
    for k in ['load', 'compute', 'store']:
        times[k] = np.zeros((nrows+1,2))
    for b in bursts:
        if b["type"] == "Conv2DDebug":
            tdebug = b['tstart']
            debug = b['data']
            row_ind = debug.val['row_ind']
            event = debug.val['event']
            if event == Conv2DEvent.LOAD_START:
                times['load'][row_ind][0] = tdebug
            elif event == Conv2DEvent.LOAD_END:
                times['load'][row_ind][1] = tdebug
            elif event == Conv2DEvent.COMPUTE_START:
                times['compute'][row_ind][0] = tdebug
            elif event == Conv2DEvent.COMPUTE_END:
                times['compute'][row_ind][1] = tdebug   
            elif event == Conv2DEvent.STORE_START:
                times['store'][row_ind][0] = tdebug 
            elif event == Conv2DEvent.STORE_END:
                times['store'][row_ind][1] = tdebug

    timing_info.times = times

    # Compute a dataframe with mean and median times for each stage
    stage_rows = []
    for stage, stage_times in times.items():
        stage_durations = stage_times[:, 1] - stage_times[:, 0]
        stage_rows.append(
            {
                "stage": stage,
                "nrows": stage_times.shape[0],
                "median_time": np.median(stage_durations),
                "mean_time": np.mean(stage_durations),
            }
        )
    stage_df = pd.DataFrame(stage_rows)
    timing_info.stage_df = stage_df

    # Save the timing results to a markdown file
    latency_ns = tresp - tcmd
    latency_cycles = latency_ns / clk_period
    summary_df = pd.DataFrame(
        [
            {"metric": "shape", "value": f"{nrows} x {ncols}"},
            {"metric": "clock period", "value": f"{clk_period:g} ns"},
            {"metric": "latency", "value": f"{latency_ns:g} ns"},
            {"metric": "cycles", "value": f"{latency_cycles:g}"},
        ]
    )
    output_dir = Path.cwd() / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "timing_results.md"
    markdown = (
        summary_df.to_markdown(index=False)
        + "\n\n"
        + stage_df.to_markdown(index=False)
        + "\n"
    )
    output_path.write_text(markdown, encoding="utf-8")
    print(f"Timing info in {output_path}")

def plot_timing(timing_info: Conv2DTimingInfo):
    # Create a timing diagram
    td = TimingDiagram()
    for stage, stage_times in timing_info.times.items():
        for i in range(stage_times.shape[0]):
            tstart = stage_times[i][0]
            tend = stage_times[i][1]
            td.add_event(stage, tstart, tend)
    ax = td.plot_signals(text_mode='never')
    ax.set_xlabel("Time (ns)")
    output_dir = Path.cwd() / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "timing.png"
    ax.figure.savefig(output_path, bbox_inches="tight")
    print(f"Timing plot in {output_path}")

def write_loop_info():
    input_path = Path.cwd() / "data" / "csynth_loop_info.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"csynth loop info file not found: {input_path}")

    loop_df = pd.read_csv(input_path)
    loop_name_col = loop_df.columns[0]
    matches = loop_df[loop_df[loop_name_col].fillna("").str.contains("convolve_row")]
    if matches.empty:
        raise ValueError(f"No row containing 'convolve_row' found in {input_path}")

    loop_row = matches.iloc[0]
    summary_df = pd.DataFrame(
        [
            {"metric": "PipelineII", "value": loop_row["PipelineII"]},
            {"metric": "PipelineDepth", "value": loop_row["PipelineDepth"]},
            {"metric": "TripCountMin", "value": loop_row["TripCountMin"]},
            {"metric": "TripCountMax", "value": loop_row["TripCountMax"]},
            {"metric": "LatencyMin", "value": loop_row["LatencyMin"]},
            {"metric": "LatencyMax", "value": loop_row["LatencyMax"]},
        ]
    )

    output_path = Path.cwd() / "data" / "convolve_loop_info.md"
    output_path.write_text(summary_df.to_markdown(index=False) + "\n", encoding="utf-8")
    print(f"Loop info in {output_path}")


if __name__ == "__main__":
    vcd_path = Path(__file__).parent / "vcd" / "dump.vcd"
    bursts, clk_period = extract_bursts(vcd_path)
    analyze_timing(bursts, clk_period)
    write_loop_info()