"""datatypes — the Unit 1 demo build.

Two independent parts, each a branch of one DAG:

* **int_prod** — the same product shown four ways (full, truncated, saturated,
  and split into halves), so the cost of each is visible side by side.
* **samp_pack** — a timestamped complex sample packed into one 32-bit word and
  unpacked again, including the unpack that forgets ``$signed``.

Run it a stage at a time::

    python datatypes_build.py --list-steps-verbose   # what the stages are
    python datatypes_build.py --status               # what is already built
    python datatypes_build.py --through int_prod_gen # Python only, no Vivado
    python datatypes_build.py --through int_prod_sim # + the SystemVerilog
    python datatypes_build.py                        # everything, both parts

``--through samp_pack_check`` skips the int_prod branch entirely: the two
branches are independent, which is what makes this a graph rather than a list.

Every step body is one call into a plain function below, so the functions can be
imported and called directly — the DAG orchestrates, it does not hide.
"""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

import numpy as np

from waveflow.build.build import BuildConfig, BuildDag, BuildStep, SourceStep
from waveflow.build.cli import run_dag_cli
from waveflow.build.svsim_steps import SvSimStep

_SOURCE_DIR = Path(__file__).resolve().parent

W = 8            # int_prod width
TW, DW = 8, 12   # samp_pack field widths
NSAMP = 100      # samples in the samp_pack part
SEED = 20260810  # fixed, so the committed figures do not churn


# ---------------------------------------------------------------------------
# int_prod — the Python golden model
# ---------------------------------------------------------------------------

def wrap(value, width: int):
    """Reduce *value* to *width* bits, two's complement — what truncation does."""
    mask = (1 << width) - 1
    out = np.asarray(value) & mask
    return np.where(out >= 1 << (width - 1), out - (1 << width), out)


def saturate(value, width: int):
    """Clamp *value* into the signed *width*-bit range — the other response to overflow."""
    lo, hi = -(1 << (width - 1)), (1 << (width - 1)) - 1
    return np.clip(value, lo, hi)


def int_prod_model(a, b, width: int = W) -> dict[str, Any]:
    """Every output of ``int_prod.sv``, computed in Python at full precision first."""
    a = np.asarray(a, dtype=np.int64)
    b = np.asarray(b, dtype=np.int64)
    prod = a * b
    trunc = wrap(prod, width)
    return {
        "a": a,
        "b": b,
        "prod": prod,
        "hi": (prod >> width) & ((1 << width) - 1),
        "lo": prod & ((1 << width) - 1),
        "trunc": trunc,
        "sat": saturate(prod, width),
        "overflow": (prod != trunc).astype(np.int64),
        "hi_nonzero": (((prod >> width) & ((1 << width) - 1)) != 0).astype(np.int64),
    }


#: The teaching vectors, in the order the testbench prints them.
INT_PROD_CASES = [
    (3, 5),       # fits — the baseline
    (100, 100),   # wrapping says 16; saturation says 127
    (-100, 100),  # the same, on the negative side
    (16, 16),     # two nonzero inputs multiply to zero
    (20, 20),     # two positives multiply to a negative
    (-1, 1),      # hi_nonzero cries wolf; there is no overflow
]


def int_prod_inputs(width: int = W) -> tuple[np.ndarray, np.ndarray]:
    """The teaching cases first, then the full signed grid behind them.

    The cases lead so the testbench's printed table is the one the docs discuss;
    the grid gives an exhaustive Python-vs-SystemVerilog comparison and the data
    for the heatmaps.
    """
    lo, hi = -(1 << (width - 1)), (1 << (width - 1)) - 1
    grid = np.arange(lo, hi + 1, dtype=np.int64)
    ga, gb = (x.ravel() for x in np.meshgrid(grid, grid, indexing="ij"))
    ca = np.array([c[0] for c in INT_PROD_CASES], dtype=np.int64)
    cb = np.array([c[1] for c in INT_PROD_CASES], dtype=np.int64)
    return np.concatenate([ca, ga]), np.concatenate([cb, gb])


def gen_int_prod_vectors(vec_dir: Path, width: int = W) -> Path:
    """Write ``int_prod_in.txt`` (the stimulus) and ``int_prod_golden.txt`` (Python's answer)."""
    vec_dir = Path(vec_dir)
    vec_dir.mkdir(parents=True, exist_ok=True)
    a, b = int_prod_inputs(width)
    model = int_prod_model(a, b, width)

    in_path = vec_dir / "int_prod_in.txt"
    in_path.write_text("".join(f"{x} {y}\n" for x, y in zip(a, b)), encoding="utf-8")

    cols = ["a", "b", "prod", "hi", "lo", "trunc", "sat", "overflow", "hi_nonzero"]
    rows = ["  ".join(str(int(model[c][i])) for c in cols) for i in range(len(a))]
    (vec_dir / "int_prod_golden.txt").write_text(
        " ".join(cols) + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return in_path


def check_int_prod(vec_dir: Path, report_path: Path) -> Path:
    """Compare the SystemVerilog outputs against the Python golden model, row by row."""
    vec_dir, report_path = Path(vec_dir), Path(report_path)
    cols = ["a", "b", "prod", "hi", "lo", "trunc", "sat", "overflow", "hi_nonzero"]
    golden = _read_table(vec_dir / "int_prod_golden.txt", cols)
    actual = _read_table(vec_dir / "int_prod_sv.txt", cols)
    return _write_report("int_prod", golden, actual, cols, report_path)


# ---------------------------------------------------------------------------
# samp_pack — the Python golden model
# ---------------------------------------------------------------------------

def pack_sample(t: int, re: int, im: int, tw: int = TW, dw: int = DW) -> int:
    """Pack one sample into a single word.

    The masks are not optional.  Python integers are unbounded and negative
    values have infinitely many leading ones, so without ``& mask`` a negative
    real part would overwrite the timestamp above it.  SystemVerilog needs no
    masks here because the field widths are declared.
    """
    mask = (1 << dw) - 1
    return ((t & ((1 << tw) - 1)) << (2 * dw)) | ((re & mask) << dw) | (im & mask)


def unpack_sample(word: int, tw: int = TW, dw: int = DW) -> tuple[int, int, int]:
    """Take a packed word apart again, sign-extending the two signed fields."""
    mask = (1 << dw) - 1
    t = (word >> (2 * dw)) & ((1 << tw) - 1)
    return t, int(wrap((word >> dw) & mask, dw)), int(wrap(word & mask, dw))


def unpack_sample_bad(word: int, dw: int = DW) -> int:
    """The real part read back without sign extension — the ``$signed`` bug."""
    return (word >> dw) & ((1 << dw) - 1)


def gen_samp_pack_vectors(vec_dir: Path, nsamp: int = NSAMP, seed: int = SEED) -> Path:
    """Write ``samp_pack_in.txt`` and ``samp_pack_golden.txt``.

    The timestamp is a counter rather than a random value — that is what a real
    sample stream carries, and it makes the I/Q plot's colouring meaningful.
    The four edge cases are forced into the first rows.
    """
    vec_dir = Path(vec_dir)
    vec_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    lo, hi = -(1 << (DW - 1)), (1 << (DW - 1)) - 1
    edge = [lo, hi, 0, -1]
    re = np.concatenate([np.array(edge, dtype=np.int64),
                         rng.integers(lo, hi + 1, nsamp - len(edge), dtype=np.int64)])
    im = np.concatenate([np.array(edge[::-1], dtype=np.int64),
                         rng.integers(lo, hi + 1, nsamp - len(edge), dtype=np.int64)])
    t = np.arange(nsamp, dtype=np.int64) % (1 << TW)

    in_path = vec_dir / "samp_pack_in.txt"
    in_path.write_text("".join(f"{a} {b} {c}\n" for a, b, c in zip(t, re, im)),
                       encoding="utf-8")

    cols = ["t", "re", "im", "word", "t_out", "re_out", "im_out", "re_bad"]
    rows = []
    for ti, ri, ii in zip(t, re, im):
        word = pack_sample(int(ti), int(ri), int(ii))
        to, ro, io = unpack_sample(word)
        rows.append("  ".join(str(v) for v in
                              (ti, ri, ii, word, to, ro, io, unpack_sample_bad(word))))
    (vec_dir / "samp_pack_golden.txt").write_text(
        " ".join(cols) + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return in_path


def check_samp_pack(vec_dir: Path, report_path: Path) -> Path:
    """Cross-language equality, plus the round-trip property, over every sample."""
    vec_dir, report_path = Path(vec_dir), Path(report_path)
    cols = ["t", "re", "im", "word", "t_out", "re_out", "im_out", "re_bad"]
    golden = _read_table(vec_dir / "samp_pack_golden.txt", cols)
    actual = _read_table(vec_dir / "samp_pack_sv.txt", cols)
    report = _write_report("samp_pack", golden, actual, cols, report_path, raise_on_fail=False)

    bad = [i for i in range(len(golden["t"]))
           if (actual["t_out"][i], actual["re_out"][i], actual["im_out"][i])
           != (golden["t"][i], golden["re"][i], golden["im"][i])]
    if bad:
        raise RuntimeError(
            f"STOP — round-trip failed on {len(bad)} sample(s); first at row {bad[0]}")
    data = json.loads(report.read_text(encoding="utf-8"))
    data["round_trip_ok"] = True
    report.write_text(json.dumps(data, indent=2), encoding="utf-8")
    if not data["match"]:
        raise RuntimeError(
            f"STOP — SystemVerilog disagreed with the Python golden model: {data['first_diff']}")
    return report


# ---------------------------------------------------------------------------
# Shared comparison helpers
# ---------------------------------------------------------------------------

def _read_table(path: Path, cols: list[str]) -> dict[str, list[int]]:
    lines = Path(path).read_text(encoding="utf-8").strip().splitlines()
    if not lines:
        raise RuntimeError(f"{path} is empty — did the simulation run?")
    header, *body = lines
    names = header.split()
    if names != cols:
        raise RuntimeError(f"{path}: expected columns {cols}, found {names}")
    out: dict[str, list[int]] = {c: [] for c in cols}
    for line in body:
        for name, value in zip(cols, line.split()):
            out[name].append(int(value))
    return out


def _write_report(part, golden, actual, cols, report_path: Path,
                  *, raise_on_fail: bool = True) -> Path:
    n_golden, n_actual = len(golden[cols[0]]), len(actual[cols[0]])
    first_diff = None
    if n_golden != n_actual:
        first_diff = {"reason": "row count", "python": n_golden, "systemverilog": n_actual}
    else:
        for i in range(n_golden):
            for c in cols:
                if golden[c][i] != actual[c][i]:
                    first_diff = {"row": i, "column": c,
                                  "python": golden[c][i], "systemverilog": actual[c][i]}
                    break
            if first_diff:
                break

    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps({
        "part": part, "rows": n_golden, "match": first_diff is None,
        "first_diff": first_diff,
    }, indent=2), encoding="utf-8")

    if first_diff is not None and raise_on_fail:
        raise RuntimeError(
            f"STOP — SystemVerilog disagreed with the Python golden model: {first_diff}")
    return report_path


# ---------------------------------------------------------------------------
# Plots, written into the docs tree only when they actually change
# ---------------------------------------------------------------------------

def write_if_different(rendered: Path, tracked: Path) -> bool:
    """Copy *rendered* over *tracked* only if the bytes differ.  Returns True if copied.

    matplotlib does not emit byte-identical PNGs across runs even for identical
    data, so overwriting unconditionally would leave the repository dirty after
    every build.  Comparing bytes is robust regardless of what metadata the
    backend decides to embed.
    """
    tracked = Path(tracked)
    tracked.parent.mkdir(parents=True, exist_ok=True)
    if tracked.exists() and tracked.read_bytes() == Path(rendered).read_bytes():
        return False
    shutil.copyfile(rendered, tracked)
    return True


def _savefig(fig, path: Path) -> None:
    # Software=None drops the matplotlib version tag, the main source of
    # spurious byte differences between otherwise identical renders.
    fig.savefig(path, dpi=110, bbox_inches="tight", metadata={"Software": None})


def plot_int_prod(vec_dir: Path, out_dir: Path, images_dir: Path, width: int = W) -> list[Path]:
    """Heatmaps of the true product, the truncated one, the saturated one, and the overflow mask."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    lo, hi = -(1 << (width - 1)), (1 << (width - 1)) - 1
    grid = np.arange(lo, hi + 1, dtype=np.int64)
    ga, gb = np.meshgrid(grid, grid, indexing="ij")
    m = int_prod_model(ga.ravel(), gb.ravel(), width)
    shape = ga.shape
    extent = [lo, hi, lo, hi]

    lim = 1 << (width - 1)
    panels = [("true product  a*b", m["prod"], "RdBu_r", None),
              ("trunc  (kept in 8 bits)", m["trunc"], "RdBu_r", [-lim, 0, lim - 1]),
              ("sat  (clamped to 8 bits)", m["sat"], "RdBu_r", [-lim, 0, lim - 1]),
              ("overflow  (1 = trunc is wrong)", m["overflow"], "gray_r", [0, 1])]

    fig, axes = plt.subplots(1, 4, figsize=(16, 4.2))
    for ax, (title, data, cmap, ticks) in zip(axes, panels):
        im = ax.imshow(np.asarray(data).reshape(shape), origin="lower",
                       extent=extent, cmap=cmap, aspect="equal")
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("a")
        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04,
                            ticks=ticks if ticks else None)
        cbar.ax.tick_params(labelsize=8)
    axes[0].set_ylabel("b")
    for ax in axes[1:]:
        ax.set_yticklabels([])
    fig.suptitle(f"Signed {width}x{width} multiply: what each output does with overflow",
                 fontsize=12)
    fig.tight_layout()

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rendered = out_dir / "int_prod_overflow.png"
    _savefig(fig, rendered)
    plt.close(fig)

    tracked = Path(images_dir) / "int_prod_overflow.png"
    write_if_different(rendered, tracked)
    return [tracked]


def plot_samp_pack(vec_dir: Path, out_dir: Path, images_dir: Path) -> list[Path]:
    """The samples on the I/Q plane, then the same samples read back without ``$signed``."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cols = ["t", "re", "im", "word", "t_out", "re_out", "im_out", "re_bad"]
    g = _read_table(Path(vec_dir) / "samp_pack_golden.txt", cols)

    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(11.5, 5))
    s0 = ax0.scatter(g["re"], g["im"], c=g["t"], cmap="viridis", s=28)
    ax0.set_title("unpacked correctly, with $signed")
    ax0.set_ylabel("imag")

    ax1.scatter(g["re_bad"], g["im"], c=g["t"], cmap="viridis", s=28)
    ax1.set_title("unpacked without $signed")
    ax1.set_yticklabels([])

    lo, hi = -(1 << (DW - 1)), (1 << (DW - 1)) - 1
    for ax in (ax0, ax1):
        ax.axhline(0, lw=0.5, color="0.6")
        ax.axvline(0, lw=0.5, color="0.6")
        ax.set_xlabel("real")
        ax.set_ylim(lo * 1.1, hi * 1.1)
    ax0.set_xlim(lo * 1.1, hi * 1.1)
    ax1.set_xlim(lo * 1.1, (1 << DW) * 1.05)
    fig.suptitle("Every negative sample folds into the positive range", fontsize=12)
    fig.tight_layout()
    # Colourbar last and outside the axes, so it cannot collide with the right panel.
    fig.colorbar(s0, ax=[ax0, ax1], label="timestamp", fraction=0.04, pad=0.02)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rendered = out_dir / "samp_pack_iq.png"
    _savefig(fig, rendered)
    plt.close(fig)

    tracked = Path(images_dir) / "samp_pack_iq.png"
    write_if_different(rendered, tracked)
    return [tracked]


# ---------------------------------------------------------------------------
# Steps — each body is one call into a function above
# ---------------------------------------------------------------------------

_IMAGES = Path("../../docs/demos/datatypes/images")


@dataclass(kw_only=True)
class IntProdGenStep(BuildStep):
    description = "Python golden model for int_prod; writes the stimulus and expected outputs."
    consumes = ["int_prod_source"]
    produces = {"int_prod_vectors": Path("vectors/int_prod_in.txt")}
    params: ClassVar[dict] = {}

    def run(self, config: BuildConfig, **_) -> dict[str, Any]:
        return {"int_prod_vectors": gen_int_prod_vectors(config.root_dir / "vectors")}


@dataclass(kw_only=True)
class IntProdCheckStep(BuildStep):
    description = "Compare the SystemVerilog int_prod outputs against the Python golden model."
    consumes = ["int_prod_sv"]
    produces = {"int_prod_report": Path("results/int_prod_report.json")}
    params: ClassVar[dict] = {}

    def run(self, config: BuildConfig, **_) -> dict[str, Any]:
        return {"int_prod_report": check_int_prod(
            config.root_dir / "vectors", config.root_dir / "results/int_prod_report.json")}


@dataclass(kw_only=True)
class IntProdDocsStep(BuildStep):
    description = "Render the int_prod overflow heatmaps into the docs image directory."
    consumes = ["int_prod_report"]
    produces = {"int_prod_figure": _IMAGES / "int_prod_overflow.png"}
    params: ClassVar[dict] = {}

    def run(self, config: BuildConfig, **_) -> dict[str, Any]:
        figures = plot_int_prod(config.root_dir / "vectors",
                                config.root_dir / "results",
                                config.root_dir / _IMAGES)
        return {"int_prod_figure": figures[0]}


@dataclass(kw_only=True)
class SampPackGenStep(BuildStep):
    description = "Python golden model for samp_pack; writes 100 samples and their packed words."
    consumes = ["samp_pack_source"]
    produces = {"samp_pack_vectors": Path("vectors/samp_pack_in.txt")}
    params: ClassVar[dict] = {}

    def run(self, config: BuildConfig, **_) -> dict[str, Any]:
        return {"samp_pack_vectors": gen_samp_pack_vectors(config.root_dir / "vectors")}


@dataclass(kw_only=True)
class SampPackCheckStep(BuildStep):
    description = "Cross-language equality plus the pack/unpack round-trip property."
    consumes = ["samp_pack_sv"]
    produces = {"samp_pack_report": Path("results/samp_pack_report.json")}
    params: ClassVar[dict] = {}

    def run(self, config: BuildConfig, **_) -> dict[str, Any]:
        return {"samp_pack_report": check_samp_pack(
            config.root_dir / "vectors", config.root_dir / "results/samp_pack_report.json")}


@dataclass(kw_only=True)
class SampPackDocsStep(BuildStep):
    description = "Render the samp_pack I/Q scatter plots into the docs image directory."
    consumes = ["samp_pack_report"]
    produces = {"samp_pack_figure": _IMAGES / "samp_pack_iq.png"}
    params: ClassVar[dict] = {}

    def run(self, config: BuildConfig, **_) -> dict[str, Any]:
        figures = plot_samp_pack(config.root_dir / "vectors",
                                 config.root_dir / "results",
                                 config.root_dir / _IMAGES)
        return {"samp_pack_figure": figures[0]}


def build_datatypes_dag() -> BuildDag:
    """Two independent branches: int_prod and samp_pack."""
    dag = BuildDag()

    dag.add(SourceStep(artifact="int_prod_source", path=_SOURCE_DIR / "int_prod.sv"))
    dag.add(SourceStep(artifact="int_prod_tb_source", path=_SOURCE_DIR / "tb_int_prod.sv"))
    dag.add(IntProdGenStep(name="int_prod_gen"))
    dag.add(SvSimStep(
        name="int_prod_sim",
        sources=[_SOURCE_DIR / "int_prod.sv"],
        tb=_SOURCE_DIR / "tb_int_prod.sv",
        consumes=["int_prod_source", "int_prod_tb_source", "int_prod_vectors"],
        sim_artifact="int_prod_sim",
        # Declaring what the testbench writes, not just the scratch directory, is what makes
        # freshness mean anything here: a run that died before writing still leaves sim/.
        outputs={"int_prod_sv": Path("vectors/int_prod_sv.txt")},
        sim_dir=Path("sim/int_prod"),
        plusargs={"vecdir": Path("vectors")},
    ))
    dag.add(IntProdCheckStep(name="int_prod_check"))
    dag.add(IntProdDocsStep(name="int_prod_docs"))

    dag.add(SourceStep(artifact="samp_pack_source", path=_SOURCE_DIR / "samp_pack.sv"))
    dag.add(SourceStep(artifact="samp_pack_tb_source", path=_SOURCE_DIR / "tb_samp_pack.sv"))
    dag.add(SampPackGenStep(name="samp_pack_gen"))
    dag.add(SvSimStep(
        name="samp_pack_sim",
        sources=[_SOURCE_DIR / "samp_pack.sv"],
        tb=_SOURCE_DIR / "tb_samp_pack.sv",
        consumes=["samp_pack_source", "samp_pack_tb_source", "samp_pack_vectors"],
        sim_artifact="samp_pack_sim",
        outputs={"samp_pack_sv": Path("vectors/samp_pack_sv.txt")},
        sim_dir=Path("sim/samp_pack"),
        plusargs={"vecdir": Path("vectors")},
    ))
    dag.add(SampPackCheckStep(name="samp_pack_check"))
    dag.add(SampPackDocsStep(name="samp_pack_docs"))

    return dag


def main() -> None:
    run_dag_cli(
        build_datatypes_dag,
        description="datatypes — Unit 1 demo: integer overflow, and packing a data structure.",
        default_through="samp_pack_docs",
        root_dir=_SOURCE_DIR,
    )


if __name__ == "__main__":
    main()
