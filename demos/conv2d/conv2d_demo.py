from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import subprocess
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

import numpy as np
from scipy.signal import correlate2d

from pysilicon.build.build import CodeGenConfig
from pysilicon.build.streamutils import copy_streamutils
from pysilicon.hw.arrayutils import (
    gen_array_utils,
    get_nwords,
    read_array,
    read_uint32_file,
    write_array,
    write_uint32_file,
)
from pysilicon.hw.dataschema import DataList, EnumField, IntField, MemAddr
from pysilicon.hw.memory import AddrUnit, Memory
from pysilicon.toolchain import toolchain
from pysilicon.toolchain.stagetest import StageTest
from pysilicon.utils.csynthparse import CsynthParser


"""
Parameters
"""
EXAMPLE_DIR = Path(__file__).resolve().parent
INCLUDE_DIR = "include"
WORD_BW_SUPPORTED = [32, 64]
TRACE_LEVELS = ("none", "port", "all")
STAGES = ("csim", "csynth", "cosim", "generate_vcd")
VITIS_STAGES = ("csim", "csynth", "cosim")
STAGE_FLOW = StageTest.from_names(STAGES)
VITIS_STAGE_FLOW = StageTest.from_names(VITIS_STAGES)

MAX_NROW = 512         # Max number of rows in the input image
MAX_NCOL = 512         # Max number of columns in the input image
MAX_KERNEL_SIZE = 4    # Max size of the convolution kernel (assumed to be square)
PIXEL_BITWIDTH = 8     # Bit width of each input pixel
KERNEL_BITWIDTH = 8    # Total number of bits in the kernel including sign bits and fractional bits 
KERNEL_FBITS = 7       # Number of fractional bits in the fixed-point representation of kernel elements
MEM_DWIDTH = 32        # Memory data width in bits
MEM_AWIDTH = 64        # Memory address width for the external image memory
MEM_AUNIT = AddrUnit.byte


AddrField = MemAddr.specialize(bitwidth=MEM_AWIDTH, include_dir=INCLUDE_DIR)
PixelField = IntField.specialize(bitwidth=PIXEL_BITWIDTH, signed=False, include_dir=INCLUDE_DIR)
KernelField = IntField.specialize(bitwidth=KERNEL_BITWIDTH, signed=True, include_dir=INCLUDE_DIR)
NrowField = IntField.specialize(bitwidth=16, signed=False, include_dir=INCLUDE_DIR)
NcolField = IntField.specialize(bitwidth=16, signed=False, include_dir=INCLUDE_DIR)
KernelSizeField = IntField.specialize(bitwidth=8, signed=False, include_dir=INCLUDE_DIR)


"""
Define the data schemas for the convolution accelerator
"""


class Conv2DError(IntEnum):
    NO_ERROR = 0
    INVALID_NROWS = 1
    INVALID_NCOLS = 2
    INVALID_KSIZE = 3
    ADDRESS_ERROR = 4


class Conv2DEvent(IntEnum):
    MAIN_START = 0
    MAIN_END = 1
    LOAD_START = 2
    LOAD_END = 3
    COMPUTE_START = 4
    COMPUTE_END = 5
    STORE_START = 6
    STORE_END = 7


Conv2DErrorField = EnumField.specialize(
    enum_type=Conv2DError,
    include_dir=INCLUDE_DIR,
    include_filename="conv2d_error.h",
)
Conv2DEventField = EnumField.specialize(
    enum_type=Conv2DEvent,
    bitwidth=3,
    include_dir=INCLUDE_DIR,
    include_filename="conv2d_event.h",
)


class Conv2DCmd(DataList):
    elements = {
        "nrows": {
            "schema": NrowField,
            "description": "Number of rows in the input image",
        },
        "ncols": {
            "schema": NcolField,
            "description": "Number of columns in the input image",
        },
        "kernel_size": {
            "schema": KernelSizeField,
            "description": "Size of the convolution kernel (assumed to be square)",
        },
        "input_addr": {
            "schema": AddrField,
            "description": (
                "Base address of the input image in external memory.  "
                "The image is stored in row-major order, meaning the first ncols elements correspond to the first row of the image, "
                "the next ncols elements correspond to the second row, and so on, "
                "with each pixel represented as an unsigned integer of bit width specified by PIXEL_BITWIDTH."),
        },
        "output_addr": {
            "schema": AddrField,
            "description": (
                "Base address of the output image in external memory.  "
                "The image is stored in the same row-major order as the input image, with each pixel represented as an unsigned interger "
                "of bit width PIXEL_BITWIDTH")
        },
        "kernel_addr": {
            "schema": AddrField,
            "description": (
                "Base address of the convolution kernel in external memory.  "
                "The kernel is stored in row-major order, meaning the first kernel_size elements correspond to the first row of the kernel, "
                "the next kernel_size elements correspond to the second row, and so on, "
                "with each element represented as a fixed point integer of bit width specified by KERNEL_BITWIDTH with KERNEL_FBITS fractional bits."),
        },
    }
    include_dir = INCLUDE_DIR
    include_filename = "conv2d_cmd.h"


class Conv2DResp(DataList):
    elements = {
        "error_code": {
            "schema": Conv2DErrorField,
            "description": "Error code indicating the status of the convolution operation",
        }
    }
    include_dir = INCLUDE_DIR
    include_filename = "conv2d_resp.h"

class Conv2DDebug(DataList):
    """
    A schema for sending internal debug information from the 
    accelerator back to the testbench during co-simuation.
    """
    elements = {
        "row_ind": {
            "schema": NrowField,
            "description": "Row index associated with the debug event",
        },
        "event": {
            "schema": Conv2DEventField,
            "description": "Debug event emitted by the convolution accelerator",
        }
    }
    include_dir = INCLUDE_DIR
    include_filename = "conv2d_debug.h"


SCHEMA_CLASSES = [
    Conv2DErrorField,
    Conv2DEventField,
    Conv2DCmd,
    Conv2DResp,
    Conv2DDebug,
]


def _stage_index(stage: str) -> int:
    return STAGE_FLOW.stage_index(stage)


def _vcd_trace_level(trace_level: str) -> str:
    return trace_level if trace_level in {"all", "port"} else "*"


def _remove_path_if_exists(path: Path) -> None:
    def _handle_remove_readonly(func, target, excinfo):
        _ = excinfo
        os.chmod(target, stat.S_IWRITE)
        func(target)

    if not path.exists():
        return
    if path.is_file() or path.is_symlink():
        try:
            path.unlink()
        except PermissionError:
            os.chmod(path, stat.S_IWRITE)
            path.unlink()
        return
    shutil.rmtree(path, onexc=_handle_remove_readonly)


@dataclass(slots=True)
class Conv2DSimResult:
    """Result bundle returned by Conv2DTest.simulate."""

    cmd: Conv2DCmd
    resp: Conv2DResp
    im_out: np.ndarray
    im_out_expected: np.ndarray

    @property
    def passed(self) -> bool:
        return np.array_equal(self.im_out, self.im_out_expected)


def _convolve2d_same(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """Compute a zero-padded fixed-point 2D correlation and saturate to the pixel range."""
    if image.ndim != 2 or kernel.ndim != 2:
        raise ValueError("image and kernel must both be 2D arrays.")

    image_acc = np.asarray(image, dtype=np.int64)
    kernel_acc = np.asarray(kernel, dtype=np.int64)
    acc = correlate2d(
        image_acc,
        kernel_acc,
        mode="same",
        boundary="fill",
        fillvalue=0,
    )
    shifted = acc >> KERNEL_FBITS
    saturated = np.clip(shifted, 0, (1 << PIXEL_BITWIDTH) - 1)
    return np.asarray(saturated, dtype=np.uint8)


class Conv2DAccel(object):
    """
    Python model for a memory-backed 2D convolution accelerator.
    """

    def __init__(
        self,
        mem: Memory,
        max_nrow: int = MAX_NROW,
        max_ncol: int = MAX_NCOL,
        max_kernel_size: int = MAX_KERNEL_SIZE,
    ):
        self.max_nrow = max_nrow
        self.max_ncol = max_ncol
        self.max_kernel_size = max_kernel_size
        self.mem = mem

    def compute_conv2d(self, cmd: Conv2DCmd) -> Conv2DResp:
        """
        Read the image and kernel from memory, run the convolution, and write back the output.
        
        The input image is stored in row-major order, meaning that the first ncols elements correspond to the first row of the image, the next ncols elements correspond to 
        the second row, and so on. The convolution kernel is also stored in row-major order. The output image is written back to memory in row-major order as well.
        """
        resp = Conv2DResp()

        nrows = int(cmd.nrows)
        ncols = int(cmd.ncols)
        kernel_size = int(cmd.kernel_size)

        if nrows <= 0 or nrows > self.max_nrow:
            resp.error_code = Conv2DError.INVALID_NROWS
            return resp

        if ncols <= 0 or ncols > self.max_ncol:
            resp.error_code = Conv2DError.INVALID_NCOLS
            return resp

        if kernel_size <= 0 or kernel_size > self.max_kernel_size:
            resp.error_code = Conv2DError.INVALID_KSIZE
            return resp

        image_shape = (nrows, ncols)
        kernel_shape = (kernel_size, kernel_size)

        try:

            # Read the input image and kernel from memory, converting from 
            # the raw word format to 2D numpy arrays with the appropriate shapes 
            # and data types.
            image_words = self.mem.read(
                int(cmd.input_addr),
                nwords=get_nwords(PixelField, word_bw=self.mem.word_size, 
                                  shape=image_shape) )
            image = read_array(
                    image_words,
                    elem_type=PixelField,
                    word_bw=self.mem.word_size,
                    shape=image_shape)
               

            kernel_words = self.mem.read(
                int(cmd.kernel_addr),
                nwords=get_nwords(KernelField, word_bw=self.mem.word_size, shape=kernel_shape),
            )
            kernel = read_array(
                    kernel_words,
                    elem_type=KernelField,
                    word_bw=self.mem.word_size,
                    shape=kernel_shape,
                )

            # We upconvert to int64 to avoid overflow if necessary to avoid overflow
            if (KERNEL_BITWIDTH + PIXEL_BITWIDTH) > 32:
                image = np.asarray(image, dtype=np.int64)
                kernel = np.asarray(kernel, dtype=np.int64)

            # Perform the correlation using scipy.signal.
            acc = correlate2d(
                image,
                kernel,
                mode="same",
                boundary="fill",
                fillvalue=0
            ) 
            shifted = acc >> KERNEL_FBITS
            output = np.clip(shifted, 0, (1 << PIXEL_BITWIDTH) - 1)
    
            # Serialize to unit32 words
            output_words = write_array(output, elem_type=PixelField, 
                                       word_bw=self.mem.word_size)
            
            # Write the output back to memory
            self.mem.write(int(cmd.output_addr), output_words)

        except ValueError:
            resp.error_code = Conv2DError.ADDRESS_ERROR
            return resp

        resp.error_code = Conv2DError.NO_ERROR
        return resp


class Conv2DTest(object):
    """Stateful test/demo harness for the Conv2D accelerator flow."""

    def __init__(
        self,
        seed: int = 7,
        nrows: int = 16,
        ncols: int = 16,
        kernel_size: int = 3,
        use_df: bool = False,
        example_dir: Path = EXAMPLE_DIR,
        include_dir: str = INCLUDE_DIR,
        mem_dwidth: int = MEM_DWIDTH,
        mem_awidth: int = MEM_AWIDTH,
    ):
        self.seed = int(seed)
        self.nrows = min(max(1, int(nrows)), MAX_NROW)
        self.ncols = min(max(1, int(ncols)), MAX_NCOL)
        self.kernel_size = min(max(1, int(kernel_size)), MAX_KERNEL_SIZE)
        self.use_df = bool(use_df)
        self.example_dir = Path(example_dir)
        self.include_dir = include_dir
        self.mem_dwidth = mem_dwidth
        self.mem_awidth = mem_awidth

        self.mem: Memory | None = None
        self.conv2d_accel: Conv2DAccel | None = None
        self.im_in: np.ndarray | None = None
        self.kernel: np.ndarray | None = None
        self.im_out: np.ndarray | None = None
        self.im_out_expected: np.ndarray | None = None
        self.cmd: Conv2DCmd | None = None
        self.resp: Conv2DResp | None = None
        self.input_addr: int | None = None
        self.output_addr: int | None = None
        self.kernel_addr: int | None = None

    @property
    def kernel_name(self) -> str:
        return "conv2d_df" if self.use_df else "conv2d"

    @property
    def project_name(self) -> str:
        return "pysilicon_conv2d_df_proj" if self.use_df else "pysilicon_conv2d_proj"

    @property
    def run_script_name(self) -> str:
        return "run_df.tcl" if self.use_df else "run.tcl"

    def gen_test_data(self) -> None:
        """Generate randomized image and fixed-point kernel inputs for a simulation run."""
        rng = np.random.default_rng(self.seed)
        self.im_in = rng.integers(
            0,
            1 << PIXEL_BITWIDTH,
            size=(self.nrows, self.ncols),
            dtype=np.uint8,
        )

        kernel_min = -(1 << (KERNEL_BITWIDTH - 1))
        kernel_max = 1 << (KERNEL_BITWIDTH - 1)
        self.kernel = rng.integers(
            kernel_min,
            kernel_max,
            size=(self.kernel_size, self.kernel_size),
            dtype=np.int16,
        ).astype(np.int8)

    def simulate(self) -> Conv2DSimResult:
        """Run the Python model and store both observed and expected output images."""
        if self.im_in is None or self.kernel is None:
            self.gen_test_data()

        assert self.im_in is not None
        assert self.kernel is not None

        self.mem = Memory(
            word_size=self.mem_dwidth,
            addr_size=self.mem_awidth,
            addr_unit=MEM_AUNIT,
        )
        self.conv2d_accel = Conv2DAccel(self.mem)

        image_shape = self.im_in.shape
        kernel_shape = self.kernel.shape
        nwords_image = get_nwords(PixelField, word_bw=self.mem.word_size, shape=image_shape)
        nwords_kernel = get_nwords(KernelField, word_bw=self.mem.word_size, shape=kernel_shape)
        nwords_output = get_nwords(PixelField, word_bw=self.mem.word_size, shape=image_shape)

        self.input_addr = self.mem.alloc(nwords_image)
        self.kernel_addr = self.mem.alloc(nwords_kernel)
        self.output_addr = self.mem.alloc(nwords_output)

        self.mem.write(
            self.input_addr,
            write_array(self.im_in, elem_type=PixelField, word_bw=self.mem.word_size),
        )
        self.mem.write(
            self.kernel_addr,
            write_array(self.kernel, elem_type=KernelField, word_bw=self.mem.word_size),
        )

        self.cmd = Conv2DCmd(
            nrows=self.nrows,
            ncols=self.ncols,
            kernel_size=self.kernel_size,
            input_addr=self.input_addr,
            output_addr=self.output_addr,
            kernel_addr=self.kernel_addr,
        )
        self.resp = self.conv2d_accel.compute_conv2d(self.cmd)

        output_words = self.mem.read(
            self.output_addr,
            nwords=get_nwords(PixelField, word_bw=self.mem.word_size, shape=image_shape),
        )
        self.im_out = read_array(
            output_words,
            elem_type=PixelField,
            word_bw=self.mem.word_size,
            shape=image_shape,
        )
        self.im_out = np.asarray(self.im_out, dtype=np.uint8)
        self.im_out_expected = _convolve2d_same(self.im_in, self.kernel)

        return Conv2DSimResult(
            cmd=self.cmd,
            resp=self.resp,
            im_out=self.im_out,
            im_out_expected=self.im_out_expected,
        )

    def gen_vitis_code(self) -> list[Path]:
        """Generate schema and utility headers needed for the Vitis flow."""
        cfg = CodeGenConfig(root_dir=self.example_dir, util_dir=self.include_dir)
        generated_paths: list[Path] = []
        for schema_class in SCHEMA_CLASSES:
            generated_paths.append(schema_class.gen_include(cfg=cfg, word_bw_supported=WORD_BW_SUPPORTED))
        generated_paths.append(gen_array_utils(PixelField, WORD_BW_SUPPORTED, cfg=cfg))
        generated_paths.append(gen_array_utils(KernelField, WORD_BW_SUPPORTED, cfg=cfg))
        copy_streamutils(cfg)
        return generated_paths

    def write_input_files(self, data_dir: Path | None = None) -> Path:
        """Write Conv2D test inputs for the file-based Vitis testbench."""
        if self.cmd is None or self.im_in is None or self.kernel is None:
            self.simulate()

        assert self.cmd is not None
        assert self.im_in is not None
        assert self.kernel is not None

        if data_dir is None:
            data_dir = self.example_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        (data_dir / "params.json").write_text(
            json.dumps(
                {
                    "nrows": self.nrows,
                    "ncols": self.ncols,
                    "kernel_size": self.kernel_size,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        write_uint32_file(
            self.im_in,
            elem_type=PixelField,
            file_path=data_dir / "im_in_array.bin",
        )
        write_uint32_file(
            self.kernel,
            elem_type=KernelField,
            file_path=data_dir / "kernel_array.bin",
        )
        return data_dir

    def read_vitis_outputs(self, data_dir: Path, validate: bool = True) -> Conv2DSimResult:
        """Read file-based Vitis outputs and compare them against the Python model."""
        if self.cmd is None or self.resp is None or self.im_out_expected is None:
            self.simulate()

        assert self.cmd is not None
        assert self.resp is not None
        assert self.im_out_expected is not None

        resp = Conv2DResp().read_uint32_file(data_dir / "resp_data.bin")
        im_out = np.asarray(
            read_uint32_file(
                data_dir / "im_out_array.bin",
                elem_type=PixelField,
                shape=(self.nrows, self.ncols),
            ),
            dtype=np.uint8,
        )

        if validate and not resp.is_close(self.resp):
            raise RuntimeError(
                "Response mismatch after Vitis simulation.\n"
                f"  got:      error_code={resp.error_code}\n"
                f"  expected: error_code={self.resp.error_code}"
            )
        if validate and not np.array_equal(im_out, self.im_out_expected):
            raise RuntimeError(
                "Output mismatch after Vitis simulation.\n"
                f"  got:\n{im_out}\n"
                f"  expected:\n{self.im_out_expected}"
            )

        return Conv2DSimResult(
            cmd=self.cmd,
            resp=resp,
            im_out=im_out,
            im_out_expected=self.im_out_expected,
        )

    def write_csynth_reports(self, data_dir: Path, soln: str = "solution1") -> dict[str, Path] | None:
        """Parse csynth.xml and write loop/resource summaries into the data directory."""
        solution_dir = self.example_dir / self.project_name / soln
        report_xml = solution_dir / "syn" / "report" / "csynth.xml"
        if not report_xml.exists():
            return None

        data_dir.mkdir(parents=True, exist_ok=True)
        parser = CsynthParser(sol_path=str(solution_dir))
        parser.get_loop_pipeline_info()
        parser.get_resources()

        loop_csv = data_dir / "csynth_loop_info.csv"
        res_csv = data_dir / "csynth_resources.csv"
        loop_json = data_dir / "csynth_loop_info.json"

        parser.loop_df.to_csv(loop_csv)
        parser.res_df.to_csv(res_csv)
        loop_records = json.loads(parser.loop_df.reset_index(names="loop_path").to_json(orient="records"))
        loop_json.write_text(json.dumps(loop_records, indent=2), encoding="utf-8")

        return {
            "loop_csv": loop_csv,
            "res_csv": res_csv,
            "loop_json": loop_json,
        }

    def test_vitis(
        self,
        start_at: str = "csim",
        through: str = "csynth",
        trace_level: str = "none",
        live_output: bool = False,
        allow_csim_errors: bool = False,
        reset_includes: bool = False,
    ) -> Conv2DSimResult | None:
        """Run a contiguous stage range of the Conv2D Vitis flow."""
        if trace_level not in TRACE_LEVELS:
            raise ValueError(
                f"Unsupported trace level '{trace_level}'. Expected one of {TRACE_LEVELS}."
            )

        start_at, through = STAGE_FLOW.validate_range(start_at, through)
        start_idx = _stage_index(start_at)
        through_idx = _stage_index(through)

        if self.cmd is None:
            self.simulate()

        data_dir = self.example_dir / "data"
        logs_dir = self.example_dir / "logs"
        project_dir = self.example_dir / self.project_name

        if start_at == "csim":
            _remove_path_if_exists(project_dir)
            _remove_path_if_exists(logs_dir)
            if reset_includes:
                _remove_path_if_exists(self.example_dir / self.include_dir)
            self.gen_vitis_code()
            data_dir = self.write_input_files()
        else:
            if start_at in {"csynth", "cosim", "generate_vcd"} and not project_dir.exists():
                raise RuntimeError(
                    f"Cannot start at '{start_at}' without an existing project at {project_dir}."
                )
            if start_at in {"csynth", "cosim", "generate_vcd"}:
                solution_dir = project_dir / "solution1"
                if not solution_dir.exists():
                    raise RuntimeError(
                        f"Cannot start at '{start_at}' without an existing solution at {solution_dir}."
                    )
            if start_at in {"csynth", "cosim"} and not data_dir.exists():
                raise RuntimeError(
                    f"Cannot start at '{start_at}' without existing Vitis input data at {data_dir}."
                )

        vitis_result: Conv2DSimResult | None = None
        vitis_stdout = ""
        vitis_stderr = ""

        if start_idx <= _stage_index("cosim"):
            vitis_through = through if through in VITIS_STAGES else "cosim"
            executed_vitis_stages = VITIS_STAGE_FLOW.range_names(start_at, vitis_through)

            print(
                f"Performing Vitis stages {start_at} through {vitis_through}. "
                "This may take minutes."
            )
            if "cosim" in executed_vitis_stages:
                print(f"Trace level: {trace_level}")

            try:
                result = toolchain.run_vitis_hls(
                    self.example_dir / self.run_script_name,
                    work_dir=self.example_dir,
                    capture_output=not live_output,
                    env={
                        "PYSILICON_CONV2D_START_AT": start_at,
                        "PYSILICON_CONV2D_THROUGH": vitis_through,
                        "PYSILICON_CONV2D_TRACE_LEVEL": trace_level,
                    },
                )
            except subprocess.CalledProcessError as exc:
                if exc.stdout:
                    print(exc.stdout)
                if exc.stderr:
                    print(exc.stderr)
                raise RuntimeError(
                    "Vitis execution failed. "
                    f"See logs under {logs_dir} and generated files under {project_dir}."
                ) from exc

            vitis_stdout = result.stdout or ""
            vitis_stderr = result.stderr or ""

            if "csynth" in executed_vitis_stages:
                csynth_outputs = self.write_csynth_reports(data_dir)
                if csynth_outputs is not None:
                    print(f"CSynth loop info written to: {csynth_outputs['loop_csv']}")
                    print(f"CSynth resources written to: {csynth_outputs['res_csv']}")

            if any(stage in executed_vitis_stages for stage in ("csim", "cosim")):
                vitis_result = self.read_vitis_outputs(data_dir, validate=not allow_csim_errors)

        if vitis_stdout:
            print(vitis_stdout)
        if vitis_stderr:
            print(vitis_stderr)

        generate_vcd_idx = _stage_index("generate_vcd")
        if start_idx <= generate_vcd_idx <= through_idx:
            vcd_path = self.generate_vcd(trace_level=_vcd_trace_level(trace_level))
            print(f"VCD written to: {vcd_path}")

        return vitis_result

    def generate_vcd(
        self,
        output_vcd: str | None = None,
        soln: str | None = "solution1",
        trace_level: str = "*",
    ) -> Path:
        """Generate a VCD file by re-running the Vivado RTL simulation."""
        from pysilicon.scripts.xsim_vcd import run_xsim_vcd

        if output_vcd is None:
            output_vcd = "dump_df.vcd" if self.use_df else "dump.vcd"

        return run_xsim_vcd(
            top=self.kernel_name,
            comp=self.project_name,
            out=output_vcd,
            soln=soln,
            trace_level=trace_level,
            workdir=self.example_dir,
        )


def main() -> None:
    """Command-line entry point for the Conv2D accelerator example."""
    parser = argparse.ArgumentParser(description="Run the Conv2D accelerator example.")
    parser.add_argument("--seed", type=int, default=7, help="Random seed for test data generation.")
    parser.add_argument("--nrows", type=int, default=16, help="Number of image rows.")
    parser.add_argument("--ncols", type=int, default=16, help="Number of image columns.")
    parser.add_argument("--kernel_size", type=int, default=3, help="Square kernel size.")
    parser.add_argument(
        "--df",
        action="store_true",
        help="Run the dataflow Conv2D kernel and Vitis project instead of the regular kernel.",
    )
    parser.add_argument(
        "--skip_vitis",
        action="store_true",
        help="Only run the Python side of the example.",
    )
    parser.add_argument(
        "--start_at",
        choices=STAGES,
        default="csim",
        help="First stage to execute. Starting at csim clears the Vitis project and logs.",
    )
    parser.add_argument(
        "--reset-includes",
        action="store_true",
        help="When starting at csim, also delete the generated include directory before regenerating it.",
    )
    parser.add_argument(
        "--through",
        choices=STAGES,
        default="csynth",
        help="Final stage to execute.",
    )
    parser.add_argument(
        "--trace_level",
        choices=TRACE_LEVELS,
        default="none",
        help="RTL co-simulation trace level passed to Vitis.",
    )
    parser.add_argument(
        "--live_output",
        action="store_true",
        help="Stream Vitis stdout/stderr directly to the terminal while it runs.",
    )
    parser.add_argument(
        "--allow_csim_errors",
        action="store_true",
        help="Allow csim/cosim output mismatches with the Python model without aborting the flow.",
    )
    args = parser.parse_args()

    if _stage_index(args.start_at) > _stage_index(args.through):
        parser.error(f"--start_at {args.start_at} must not come after --through {args.through}.")

    test = Conv2DTest(
        seed=args.seed,
        nrows=args.nrows,
        ncols=args.ncols,
        kernel_size=args.kernel_size,
        use_df=args.df,
    )

    if args.start_at == "csim" or args.skip_vitis:
        result = test.simulate()
        print(
            f"Python simulation: error_code={result.resp.error_code.name}, "
            f"passed={result.passed}"
        )

    if args.skip_vitis:
        return

    vitis_result = test.test_vitis(
        start_at=args.start_at,
        through=args.through,
        trace_level=args.trace_level,
        live_output=args.live_output,
        allow_csim_errors=args.allow_csim_errors,
        reset_includes=args.reset_includes,
    )
    if vitis_result is not None:
        print(
            f"Vitis simulation: error_code={vitis_result.resp.error_code.name}, "
            f"passed={vitis_result.passed}"
        )


if __name__ == "__main__":
    main()
