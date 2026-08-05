# Migration tracker (Step 4 output)

Per-file burn-down list for the **unit-by-unit, bespoke** waveflow integration.
Generated 2026-06-23 by scanning tracked files for `xilinxutils` / `pysilicon` /
`waveflow` references.

**Status values:** `todo` (default) · `integrated` (reworked onto current
waveflow & verified) · `deferred` (intentionally left broken for now, doc
bannered) · `deleted`.

**Reference counts** are *matching-line* counts: `x` = xilinxutils, `p` =
pysilicon. (Regenerate with `git grep -c -i -e <term>`.)

> Reminder (see `plans/migration.md`): this is **not** a uniform rename. Each unit
> integrates a *different* part of waveflow in a *different* way. The counts below
> tell you *where* old references live, not *how* to rewrite them — that is decided
> per unit at integration time.

## Totals

- **Course-content files referencing old packages:** ~51
  - xilinxutils-only: ~25 (cluster in the **earlier** units' figure notebooks +
    intro demos)
  - pysilicon-only: ~25 (cluster in the **heavier later** demos: conv2d,
    histogram, stream, pipeline, sharedmem)
  - `demos/pipeline` is **mixed** (both).
- **Vendored `pysilicon/` package files:** ~17 — *not* course content; these get
  removed wholesale in Step 7 (status `deleted` below).
- **already-waveflow:** only `pyproject.toml` (the new hwdesign manifest).
- **already migrated this session:** package repurposed (`pysilicon`→`hwdesign`),
  `autograde_llm_latex` deleted.

---

## By course unit

Integrate one group per session. `figs/*.ipynb` are the lecture-figure generators
for that unit; the demo/lab rows are the runnable material.

### Intro demos (unit00–01)
| File | refs | category | status | integration notes |
|---|---|---|---|---|
| [units/unit01_basic_logic/figs/logic_figs.ipynb](../units/unit01_basic_logic/figs/logic_figs.ipynb) | x:4 | dead-xilinxutils | todo | likely `waveflow.utils.timing` (TimingDiagram) |
| [demos/simp_fun/timing_diag.ipynb](../demos/simp_fun/timing_diag.ipynb) | x:9 | dead-xilinxutils | todo | timing-diagram demo → `waveflow.utils.timing` |
| [demos/scalar_fun/notebooks/view_timing.ipynb](../demos/scalar_fun/notebooks/view_timing.ipynb) | x:7 | dead-xilinxutils | todo | |
| [docs/demos/simp_fun/simulation.md](../docs/demos/simp_fun/simulation.md) | x:4 | dead-xilinxutils | todo | docs for simp_fun |

### unit02_fsm
| File | refs | category | status | integration notes |
|---|---|---|---|---|
| _(no old-package refs found; `demos/fsm` appears clean)_ | — | — | — | verify at integration |

### unit03_fixp
| File | refs | category | status | integration notes |
|---|---|---|---|---|
| [demos/fixp/piecewise.ipynb](../demos/fixp/piecewise.ipynb) | x:1 | dead-xilinxutils | todo | **recommended first unit** — maps to `waveflow.hw.fixpoint` + `waveflow.utils.fixputils` |

### unit04_procif
| File | refs | category | status | integration notes |
|---|---|---|---|---|
| [units/unit04_procif/figs/procif_figs.ipynb](../units/unit04_procif/figs/procif_figs.ipynb) | x:5 | dead-xilinxutils | todo | |
| [docs/demos/procif/fpga_build.md](../docs/demos/procif/fpga_build.md) | x:1 | dead-xilinxutils | todo | |
| [docs/demos/procif/rtlsim.md](../docs/demos/procif/rtlsim.md) | x:2 | dead-xilinxutils | todo | |

### unit05_fifo
| File | refs | category | status | integration notes |
|---|---|---|---|---|
| [units/unit05_fifo/figs/fifo_figs.ipynb](../units/unit05_fifo/figs/fifo_figs.ipynb) | x:5 | dead-xilinxutils | todo | |
| [demos/fifoif/python/datastructs.py](../demos/fifoif/python/datastructs.py) | x:1 | dead-xilinxutils | todo | likely `waveflow.hw.dataschema` |
| [demos/fifoif/python/gen_vitis_code.py](../demos/fifoif/python/gen_vitis_code.py) | x:1 | dead-xilinxutils | todo | codegen → compare to `waveflow.build.*` |
| [demos/fifoif/python/view_axi_stream.ipynb](../demos/fifoif/python/view_axi_stream.ipynb) | x:11 | dead-xilinxutils | todo | AXI-stream view → `waveflow.utils.vcd` |
| [demos/fifoif/fifo_fun_vitis/src/cmd.h](../demos/fifoif/fifo_fun_vitis/src/cmd.h) | x:1 | dead-xilinxutils | todo | C++ header comment/include |
| [demos/stream/avg_demo.ipynb](../demos/stream/avg_demo.ipynb) | p:3 | live-pysilicon | todo | |
| [demos/stream/poly_demo.ipynb](../demos/stream/poly_demo.ipynb) | p:14 | live-pysilicon | todo | |
| [docs/demos/fifoif/poly.md](../docs/demos/fifoif/poly.md) | p:2 | live-pysilicon | todo | |

### unit06_timing
| File | refs | category | status | integration notes |
|---|---|---|---|---|
| [units/unit06_timing/figs/timing_figs.ipynb](../units/unit06_timing/figs/timing_figs.ipynb) | x:4 | dead-xilinxutils | todo | (note: figs also modified in working tree) |
| [demos/pipeline/view_timing.ipynb](../demos/pipeline/view_timing.ipynb) | x:9 | dead-xilinxutils | todo | |
| [demos/pipeline/poly_demo.py](../demos/pipeline/poly_demo.py) | x:4 | dead-xilinxutils | todo | |
| [demos/pipeline/pipeline_demo.ipynb](../demos/pipeline/pipeline_demo.ipynb) | p:11 | live-pysilicon | todo | `demos/pipeline` is **mixed** (x+p) |
| [units/unit06_timing/timing.pdf](../units/unit06_timing/timing.pdf) | x:2 | dead-xilinxutils | deferred | binary PDF — text mentions only; regenerate, don't edit |

### unit07_loopopt
| File | refs | category | status | integration notes |
|---|---|---|---|---|
| [units/unit07_loopopt/figs/loopopt_figs.ipynb](../units/unit07_loopopt/figs/loopopt_figs.ipynb) | x:5 | dead-xilinxutils | todo | |

### unit08_unroll
| File | refs | category | status | integration notes |
|---|---|---|---|---|
| [units/unit08_unroll/figs/unroll_figs.ipynb](../units/unit08_unroll/figs/unroll_figs.ipynb) | x:5 | dead-xilinxutils | todo | |
| [demos/vector_mult/vmult_vitis/scripts/synth_analysis.ipynb](../demos/vector_mult/vmult_vitis/scripts/synth_analysis.ipynb) | x:4 | dead-xilinxutils | todo | synth report → `waveflow.utils.csynthparse` |

### unit09_sharedmem
| File | refs | category | status | integration notes |
|---|---|---|---|---|
| [units/unit09_sharedmem/figs/sharedmem_figs.ipynb](../units/unit09_sharedmem/figs/sharedmem_figs.ipynb) | p:2 | live-pysilicon | todo | memory model → `waveflow.hw.memory` / `memif` |

### unit10_arrays — conv2d & histogram (heavy array/memory demos)
| File | refs | category | status | integration notes |
|---|---|---|---|---|
| [demos/conv2d/conv2d_demo.py](../demos/conv2d/conv2d_demo.py) | p:13 | live-pysilicon | todo | big example; `hw.arrayutils` / `hw.dataschema` |
| [demos/conv2d/conv2d_test.ipynb](../demos/conv2d/conv2d_test.ipynb) | p:6 | live-pysilicon | todo | |
| [demos/conv2d/timing_analysis.py](../demos/conv2d/timing_analysis.py) | p:3 | live-pysilicon | todo | |
| [demos/conv2d/view_timing.ipynb](../demos/conv2d/view_timing.ipynb) | p:2 | live-pysilicon | todo | |
| [demos/conv2d/run.tcl](../demos/conv2d/run.tcl) | p:18 | live-pysilicon | todo | TCL include paths → waveflow-generated headers |
| [demos/conv2d/run_df.tcl](../demos/conv2d/run_df.tcl) | p:19 | live-pysilicon | todo | TCL include paths |
| [demos/conv2d/conv2d.cpp](../demos/conv2d/conv2d.cpp) | p:1 | live-pysilicon | todo | C++ include of vendored header |
| [demos/conv2d/conv2d_df.cpp](../demos/conv2d/conv2d_df.cpp) | p:1 | live-pysilicon | todo | |
| [demos/conv2d/conv2d_tb.cpp](../demos/conv2d/conv2d_tb.cpp) | p:3 | live-pysilicon | todo | |
| [demos/histogram/hist_demo.py](../demos/histogram/hist_demo.py) | p:17 | live-pysilicon | todo | |
| [demos/histogram/view_timing.ipynb](../demos/histogram/view_timing.ipynb) | p:2 | live-pysilicon | todo | |
| [demos/histogram/run.tcl](../demos/histogram/run.tcl) | p:18 | live-pysilicon | todo | TCL include paths |
| [demos/histogram/hist.cpp](../demos/histogram/hist.cpp) | p:1 | live-pysilicon | todo | |
| [demos/histogram/hist_tb.cpp](../demos/histogram/hist_tb.cpp) | p:1 | live-pysilicon | todo | |

> **Note on `.tcl` / `.cpp` / `.h` rows:** these reference the vendored
> `pysilicon/build/*` headers (array_utils.h, memmgr.hpp, streamutils) and include
> paths. Under waveflow these are produced by `waveflow.build.*`
> (`StreamUtilsStep`, `MemMgrStep`, `ArrayUtilsStep`). Reworking them is part of
> each demo's bespoke integration.

## Labs
| File | refs | category | status | integration notes |
|---|---|---|---|---|
| [labs/cubic/partial/cubic.ipynb](../labs/cubic/partial/cubic.ipynb) | x:1 | dead-xilinxutils | todo | |
| [docs/labs/cubic/sim_sing.md](../docs/labs/cubic/sim_sing.md) | x:2 | dead-xilinxutils | todo | |
| [docs/labs/cubic/test.md](../docs/labs/cubic/test.md) | x:2 | dead-xilinxutils | todo | |
| [labs/intersect/partial/line_inter.ipynb](../labs/intersect/partial/line_inter.ipynb) | p:6 | live-pysilicon | todo | |
| [labs/intersect/run_hls.tcl](../labs/intersect/run_hls.tcl) | p:3 | live-pysilicon | todo | TCL include paths |
| [docs/labs/intersect/csynth.md](../docs/labs/intersect/csynth.md) | p:1 | live-pysilicon | todo | |
| [docs/labs/subc/sv.md](../docs/labs/subc/sv.md) | x:2 | dead-xilinxutils | todo | |
| _labs/rootsolve_ | — | — | — | no old refs found; verify at integration |

## Projects & planning docs
| File | refs | category | status | integration notes |
|---|---|---|---|---|
| [docs/projects/planning.md](../docs/projects/planning.md) | p:1 | live-pysilicon | todo | |
| [docs/projects/example_projects/conv2d/evaluation.md](../docs/projects/example_projects/conv2d/evaluation.md) | p:1 | live-pysilicon | todo | |
| [docs/projects/example_projects/conv2d/ipdefinition.md](../docs/projects/example_projects/conv2d/ipdefinition.md) | p:1 | live-pysilicon | todo | |

## Support / install docs (→ folds into Getting Started, Docs track)
| File | refs | category | status | integration notes |
|---|---|---|---|---|
| ~~docs/support/repo/python.md~~ | x:8 | dead-xilinxutils | **integrated** | ✅ 2026-08-05 — **split and deleted**. Student install → [docs/support/repo/package.md](../docs/support/repo/package.md) (two packages explained, waveflow from GitHub, ordering caveat, verify snippet). Instructor/CA setup → [docs/support/repo/developer.md](../docs/support/repo/developer.md) (editable waveflow, staleness/branch/student-parity pitfalls, requirements regeneration). 3 inbound links repointed. |
| [docs/support/repo/repo.md](../docs/support/repo/repo.md) | — | — | **integrated** | ✅ 2026-08-05 — reviewed, left as-is (cloning only; no package refs) |
| [docs/support/nyuremote/python.md](../docs/support/nyuremote/python.md) | x:1 | dead-xilinxutils | todo | NYU-server python env page |

## Vendored `pysilicon/` package — ✅ DELETED 2026-08-05

All 37 tracked files removed; `pysilicon/__init__.py` is now a **tombstone** that
raises a `ModuleNotFoundError` pointing at waveflow, `plans/waveflow_api.md`, and
this tracker — so not-yet-migrated material fails legibly rather than mysteriously.
Delete the directory outright once every row above is `integrated` or `deferred`.

Pre-deletion audit: every *live* vendored file had an upstream equivalent at the
same relative path in waveflow (all of `build/*.h,.hpp,.cpp`, `hw/*`,
`toolchain/*`, `utils/*`, and 7 of 9 `scripts/*`). The only non-upstream files
were dead weight: `_version.py`, the `old/*` attic (5 xilinxutils-era files),
`scripts/pysilicon_copy.py` (retired with the vendoring model), and
`scripts/check_latex_soln.py` — **the one judgment call**: it is course-specific
(LaTeX solution checking, a plausible `hwdesign` candidate) but was already
broken, importing `from xilinxutils.parselatex import …`, a module that exists
nowhere. Deleted rather than carried forward per Step 5 ("add nothing
speculative"); restore it and its dependency if a grading unit needs them:
`git show pre-waveflow-migration:pysilicon/scripts/check_latex_soln.py` and
`…:pysilicon/old/parselatex.py`.

Recoverable in full via the `pre-waveflow-migration` tag. Files: `pysilicon/__init__.py`, `pysilicon/build/*`
(`__init__.py`, `array_utils.h`, `memmgr.hpp`, `memmgr_tb.hpp`, `streamutils.py`),
`pysilicon/hw/*` (`arrayutils.py`, `dataschema.py`, `memory.py`),
`pysilicon/toolchain/*`, `pysilicon/utils/*`, `pysilicon/scripts/*`
(`create_doc_assets.py`, `pysilicon_copy.py`, `xsim_vcd.py`, `check_latex_soln.py`,
`build_lab_autograder.py`, …), `pysilicon/old/*`. → **status: deleted**.

## Config (low priority / done)
| File | refs | category | status | integration notes |
|---|---|---|---|---|
| [pyproject.toml](../pyproject.toml) | p:2, w:6 | already-waveflow | integrated | repurposed to hwdesign this session |
| [.gitignore](../.gitignore) | x:1, p:3 | mixed | todo | ignore patterns; tidy when convenient |
