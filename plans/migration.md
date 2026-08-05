# hwdesign → waveflow Migration Plan

A staged plan for migrating this repo off its vendored, partly-stale package
snapshot and onto the external **waveflow** package. Written so each step can be
handed to Claude CLI (or done by hand) as a self-contained prompt.

## Background (the "crazy history")

1. Course originally shipped with a package called **xilinxutils**.
2. A parallel package, **pysilicon**, was developed in a separate repo and grew
   to a superset of xilinxutils.
3. Mid-class, pysilicon was *manually copied* into this repo at
   [`pysilicon/`](../pysilicon/) and xilinxutils references were partly renamed.
   This vendored copy is now a frozen, partly-stale snapshot — e.g.
   [`pysilicon/__init__.py`](../pysilicon/__init__.py) still self-identifies as
   `xilinxutils`.
4. Class ended; work on this repo stopped.
5. The external package was renamed **waveflow** (pysilicon was taken on PyPI)
   and has since evolved well beyond pysilicon.
   Docs: https://sdrangan.github.io/waveflow/docs/ — published on PyPI.

## Decisions (locked)

- **End state:** hwdesign *stays* as the course website (units, labs, docs,
  demos, gradescope). The vendored `pysilicon/` is **deleted** and **replaced by
  a thin, course-specific `hwdesign` package** (flat layout: `hwdesign/`, i.e.
  `hwdesign/hwdesign/__init__.py`, matching the author's other packages) that
  is built *on top of* waveflow. General-purpose functionality imports **waveflow**
  directly; course-specific code lives in `hwdesign`. Nothing physically moves out
  of this repo.
- **What goes where (hard rule — this is the lesson from the history):**
  - **waveflow** — anything general-purpose / reusable beyond this course
    (HLS build/sim wrappers, VCD & timing utilities, data schemas, array/memory
    helpers).
  - **hwdesign** — only what makes sense *because of this course*: lab/assignment
    autograders, gradescope glue, lab test scaffolding, demo helpers tied to
    specific assignments, and the compat/adapter shim. `hwdesign` **depends on**
    waveflow; waveflow **never** depends on `hwdesign`.
  - **Rule of thumb:** "Would another waveflow user want this?" → push it
    **upstream** to waveflow. "Only makes sense for *this course's* labs/units?"
    → keep it in `hwdesign`. When course code matures into something general,
    migrate it up to waveflow. This discipline is what prevents `hwdesign` from
    becoming pysilicon 2.0 — exactly the failure that created this mess.
- **Dependency mechanism:** **editable local checkout now**
  (`pip install -e ../waveflow`), with the intent to **pin to a released
  version** (`waveflow==X.Y.Z`) when the course runs (~September 2026). The
  switch is a one-line change in the requirements file — editable does not lock
  us in. A thin local adapter (Step 5) keeps that switch and waveflow's ongoing
  churn contained to one file.
- **Incremental is fine:** the course is not running. Most demos/examples may
  stay broken during the migration as long as the breakage is *legible*
  (clear errors, doc banners) rather than mysterious.
- **Integration is per-unit and bespoke (KEY).** waveflow is now a large,
  sophisticated architecture, and each course unit will integrate a *different*
  part of it in a *different* way — this is **not** a uniform find-and-replace of
  `pysilicon` → `waveflow`. Consequence: **no global compat adapter** (Step 5),
  **no single reusable recipe** (Step 6 establishes a *workflow*, not a code
  template), and units are integrated **one at a time** (Step 7).
- **Retired:** the old `autograde_llm_latex` script/console-entry is deleted
  (no waveflow equivalent, not carried forward).

## Current state (re-measured 2026-08-05)

Counts below exclude `plans/` and the deleted `pysilicon/` tombstone.

- **262 references** to `xilinxutils` (102) / `pysilicon` (160) across **~50
  course-content files** (demos, unit figure notebooks, labs, docs). Down from
  ~236-across-~65 in June only because the vendored package was deleted — **no
  course content has been migrated yet**.
- **4** files reference `waveflow`, and all 4 are packaging/wiring
  (`pyproject.toml`, `requirements-dev.txt`, `hwdesign/__init__.py`,
  `docs/getting_started/index.md`) — no course material imports it yet.
- `demos/` is ~632 MB on disk but only ~89 tracked files — the bulk is
  gitignored Vitis/Vivado build output, **not** content to migrate.

### Superseded June measurements (kept so the numbers above read in context)

- `pyproject.toml` used to declare *this repo* as the installable `pysilicon`
  package (console scripts `xsim_vcd`, `sv_sim`, …) — the old vendoring model.
  **Demoted in Step 3**; it now declares `hwdesign`, depending on waveflow.

## Environment & how to run pip (measured 2026-06-23)

- **venv:** `C:\Users\sdran\Documents\repos\hwdesign-venv`.
- **Always target the venv Python explicitly** — do not rely on activation state
  (a new shell / `cd` / background task can lose it):
  `C:\Users\sdran\Documents\repos\hwdesign-venv\Scripts\python.exe -m pip ...`.
  This guarantees installs/uninstalls hit this venv, never global Python.
- **Installed packages (verified 2026-08-05):** `waveflow` and `hwdesign`, both
  editable, both refreshed via
  `...\hwdesign-venv\Scripts\python.exe -m pip install -r requirements-dev.txt`.
  The old editable `pysilicon` install was removed back in Step 3.
  **Editable installs go stale in one specific way:** Python source is picked up
  live, but recorded dependencies and console-script shims are a snapshot taken
  at install time. In August the venv was missing 10 of waveflow's 13 entry
  points for exactly this reason. Re-run the command above after waveflow adds
  a script or a dependency.
- **The editable install follows whichever branch is checked out in
  `../pysilicon`** — it changed branches mid-session on 2026-08-05. When
  something breaks inexplicably, check
  `git -C ../pysilicon branch --show-current` *first*.
- **A student-like second venv is planned but not yet created.** Students install
  with `pip install git+https://github.com/sdrangan/waveflow.git` (repo is
  public); the dev venv cannot detect course material that accidentally depends
  on unpushed waveflow work. Refreshing such a venv needs
  `--force-reinstall --no-deps`, since waveflow's version stays `0.1.0`.
- **waveflow source = `../pysilicon`** (i.e.
  `C:\Users\sdran\Documents\repos\pysilicon`). That folder *is* the waveflow git
  repo (remote `github.com/sdrangan/waveflow.git`, package name `waveflow`); the
  folder kept its old name and that is purely cosmetic — pip installs it as
  `waveflow` and imports stay `import waveflow`. This is the single source of
  truth you develop in, so install editable from it: `-e ../pysilicon`. Update it
  with `git -C ../pysilicon pull`. (Renaming the folder to `../waveflow` later is
  safe — git history lives in `.git`, not the folder name — just re-point the
  editable install.)

## Guiding principles

- Steps 1–4 are **non-destructive** (tag, install, inventory). Only Step 7
  deletes anything. Do them in order.
- Units import waveflow **directly**, each in the way that fits that unit — there
  is no global adapter (see Decisions: integration is per-unit and bespoke).
- Drive the work off the **tracker** (Step 4), integrating **one unit per
  session** (Step 7). Stop and resume anytime.

---

## Step 1 — Safety net (non-destructive) — ✅ DONE 2026-06-23

**Goal:** make the current frozen state permanently recoverable before deleting
anything.

**Status:** annotated tag `pre-waveflow-migration` (→ commit `1a6d058`) created;
working branch `waveflow-migration` created and checked out. Recover anytime with
`git checkout pre-waveflow-migration`.

> **Prompt:** Create an annotated git tag `pre-waveflow-migration` on the current
> HEAD capturing the pre-migration state, and a working branch
> `waveflow-migration` off it. Do not modify any files. Confirm the tag and
> branch exist and report the commit they point to.

**Done when:** `git tag` lists `pre-waveflow-migration` and you are on
`waveflow-migration`.

---

## Step 2 — Install and observe waveflow (non-destructive) — ✅ DONE 2026-06-23

**Goal:** establish the ground-truth API to migrate *toward*.

**Status:** `waveflow` installed editable from `../pysilicon` into the hwdesign
venv (pulled in scikit-learn, simpy, typer, rich — waveflow has grown well beyond
old pysilicon). `import waveflow` loads from
`C:\Users\sdran\Documents\repos\pysilicon\waveflow`. API surface captured in
[`plans/waveflow_api.md`](waveflow_api.md). Key finding: **many old pysilicon
modules map by a near namespace-swap** (`pysilicon.utils.*` → `waveflow.utils.*`,
`pysilicon.hw.*` → `waveflow.hw.*`, etc.) — but per-symbol signatures have evolved,
so verify each, don't assume.

waveflow source: the local clone at **`../pysilicon`** (= the waveflow repo, see
Environment section). Install it editable into the venv.

> **Prompt:** Install the external waveflow package into the hwdesign venv. Use
> the venv Python explicitly for every pip call (see the Environment section:
> `...\hwdesign-venv\Scripts\python.exe -m pip ...`). Install editable from the
> local clone: `... -m pip install -e ../pysilicon` (that folder is the waveflow
> repo; it installs as the `waveflow` package).
> Then introspect the installed `waveflow` package and produce a Markdown summary
> at `plans/waveflow_api.md` listing its top-level modules, public classes, and
> public functions (name + one-line docstring summary). Report which install
> method you used. Do not change any repo files other than creating that summary.

**Done when:** `plans/waveflow_api.md` exists and `python -c "import waveflow"`
succeeds.

---

## Step 3 — Repurpose the package: `pysilicon` → course-specific `hwdesign` — ✅ DONE 2026-06-23

**Goal:** stop building this repo as the `pysilicon` package (an old waveflow
clone); instead build a thin, course-specific `hwdesign` package that depends on
waveflow.

**Status:** `pyproject.toml` now declares `hwdesign` (flat layout,
`include = ["hwdesign*"]`, static version 0.1.0, no console scripts, depends on
`waveflow`). Created `hwdesign/__init__.py`; deleted `pysilicon.egg-info/`;
`pip uninstall pysilicon` → `pip install -e .`. Added `requirements-dev.txt`
(two editable installs: `-e ../pysilicon` for waveflow, `-e .` for hwdesign).
Verified: `import hwdesign` (0.1.0) and `import waveflow` both load. Console-script
triage: all general scripts now come from `waveflow.scripts.*`;
`autograde_llm_latex` deleted; `pysilicon_copy` retired. Vendored `pysilicon/` dir
left in place (removed in Step 7).

> **Prompt:** This repo should no longer build itself as the `pysilicon` package
> (that was an old vendored clone of waveflow). Instead it should build a thin,
> course-specific `hwdesign` package that *depends on* waveflow. (1) Rewrite
> `pyproject.toml` to declare a `hwdesign` package using flat layout (package dir
> `hwdesign/`, i.e. `hwdesign/hwdesign/`), depending on `waveflow`. Scope package
> discovery with `[tool.setuptools.packages.find] include = ["hwdesign*"]` so the
> non-package top-level dirs (units, demos, labs, docs, gradescope, extra) are not
> picked up. Create `hwdesign/__init__.py`.
> (2) Drop the old `pysilicon` console scripts for now; re-add only course-specific
> ones later if needed (note: `autograde_llm_latex` is already deleted — do not
> re-add it). (3) Delete `pysilicon.egg-info/`. (4) Document the waveflow
> dependency in `requirements-dev.txt` using whichever install source was chosen
> in Step 2 (local `-e ../waveflow`, or
> `-e "git+https://github.com/sdrangan/waveflow.git#egg=waveflow"`), with a comment
> that it becomes `waveflow==X.Y.Z` when the course runs (~Sept 2026), and document
> installing this repo's package editable too (`pip install -e .`). (5) For each old console script (`xsim_vcd`,
> `collect_overlay`, `sv_sim`, `sv_synth`, `sv_impl`, `autograde_llm_latex`,
> `build_lab_autograder`, `pysilicon_copy`), check `plans/waveflow_api.md` and
> note in the plan whether it now lives in waveflow, belongs in `hwdesign`, or is
> retired. Do **not** delete the vendored `pysilicon/` directory yet.

**Done when:** `pip install -e .` installs a `hwdesign` package that imports
cleanly, `egg-info` is gone, and waveflow is a declared editable dependency.

---

## Step 4 — Build the migration tracker (non-destructive, highest-value first move) — ✅ DONE 2026-06-23

**Goal:** turn the "crazy history" into a finite, resumable checklist.

**Status:** [`plans/migration_tracker.md`](migration_tracker.md) created —
unit-grouped, per-file table with ref counts, category, status, and an
integration-notes column. Findings: ~51 course-content files (~25 xilinxutils in
earlier units' figure notebooks + intro demos; ~25 pysilicon in heavier later
demos — conv2d, histogram, stream, pipeline, sharedmem; `demos/pipeline` mixed).
Vendored `pysilicon/` package (~17 files) flagged for wholesale Step-7 deletion.

> **Prompt:** Scan every tracked file in this repo for references to
> `xilinxutils`, `pysilicon`, and `waveflow`. Produce a Markdown table at
> `plans/migration_tracker.md` with one row per file containing: file path
> (as a clickable relative link), which package(s) it references, the count of
> references, a guessed category (`dead-xilinxutils` / `live-pysilicon` /
> `already-waveflow` / `mixed`), a status column initialized to `todo` (other
> values: `integrated` / `deferred` / `deleted`), and a short free-text
> "integration notes" column (left blank for now; filled per unit during Steps
> 6–7). Group the table **by course unit** where possible (map each demo / lab /
> figure-notebook to the unit it supports — e.g. `fixp`→unit03, `fifo`→unit05,
> `pipeline`→unit06/07), with an "unassigned/shared" group for the rest. Above the
> table, summarize totals per category so I can see how much is dead xilinxutils
> code I can simply delete versus live pysilicon to rework. Read-only — change
> nothing but that new file.

**Done when:** `plans/migration_tracker.md` exists with a per-file, unit-grouped
status table and category totals — the burn-down list for the per-unit work.

---

## Step 5 — Keep the `hwdesign` package thin (NO global compat adapter)

**Goal:** keep the course package minimal. **Integration is per-unit and
bespoke** (see Decisions): waveflow is now a large architecture and each unit
will wire into a *different* part of it, in a different way. A uniform
old-pysilicon→waveflow re-export shim would therefore be the wrong abstraction —
it assumes a uniform migration that does not exist. So there is **no
`hwdesign/compat.py`**.

> **Prompt:** Do **not** build a global waveflow compatibility module. Leave the
> `hwdesign` package minimal (just `hwdesign/__init__.py` from Step 3). Units
> import waveflow directly, each in the way that suits that unit. Only lift code
> into `hwdesign/` when an actual course-specific helper turns out to be shared by
> **two or more** units during integration (Steps 6–7) — and record each such
> shared helper in `plans/migration_tracker.md`. Until then, add nothing.

**Done when:** `hwdesign` is installed and importable, and stays empty of
speculative shared code.

---

## Step 6 — Integrate the FIRST unit end-to-end (establish the *workflow*)

**Goal:** integrate one unit fully against waveflow's **current** architecture to
establish the *process* — how to wire a unit to waveflow, how to track status,
how to update that unit's docs — knowing each later unit will integrate
differently. The output is a workflow, **not** a reusable code template.

**First unit: `unit00_course_intro` + the install story** (decided 2026-08-05,
superseding the `unit03_fixp` recommendation below). Rationale: it starts the
course at its actual beginning and forces the install path to be real, which
closes the two open placeholders in Getting Started (§3 "Get the code & set up
Python", §4 "Run your first demo") — the gap the Docs track was created for.

Scope, per the tracker's "Intro demos (unit00–01)" group:
- `units/unit00_course_intro/` — slides only, no code refs; nothing to port.
- Getting Started §3 — write the real install path, condensing
  `docs/support/repo/python.md` (x:8, currently the stale xilinxutils story).
- `units/unit01_basic_logic/figs/logic_figs.ipynb` (x:4) → `waveflow.utils.timing`.
- `demos/simp_fun/timing_diag.ipynb` (x:9) + `docs/demos/simp_fun/simulation.md`
  (x:4) → the timing-diagram demo; the natural candidate for Getting Started §4.
- `demos/scalar_fun/notebooks/view_timing.ipynb` (x:7).

**Verify against a student-like install.** These files are what a new student
runs first, so a passing run in the dev venv is not sufficient evidence — the dev
venv resolves waveflow from a local clone that is often on a feature branch. See
"Environment" above.

> **Prompt (original, superseded — kept for context):** Pick one self-contained
> unit and integrate it end-to-end against
> waveflow's *current* API (per `plans/waveflow_api.md`) — recommended:
> `unit03_fixp` / the `fixp` demo, since fixed-point maps cleanly onto
> `waveflow.hw.fixpoint` + `waveflow.utils.fixputils`. Rewrite its imports and
> code as the new architecture requires (do **not** reach for old pysilicon call
> shapes), run its notebook/demo to confirm it works, and update its docs page
> plus the Getting Started "what currently works" list. Then add a short
> **integration log** entry at the bottom of this plan noting what was
> unit-specific vs. potentially reusable. Mark the unit `integrated` in
> `plans/migration_tracker.md`. Stop for review.

**Done when:** one unit runs on current waveflow, its docs reflect it, and the
integration log + tracker are updated.

---

## Step 7 — Integrate remaining units one at a time (each bespoke); retire pysilicon

**Status (2026-08-05):** part (1) — retiring the vendored package — is **✅ DONE,
pulled forward ahead of Step 6** at the author's request, since breaking every
demo at once is acceptable while the course is not running and makes the
remaining work legible. All 37 vendored files deleted; `pysilicon/__init__.py`
left as a tombstone that raises a pointer to waveflow. See the audit in
`plans/migration_tracker.md`. Part (2) — per-unit integration — is **not started**;
every course row in the tracker is still `todo`.

**Goal:** work unit by unit. Treat every unit as a *fresh* integration problem —
do not assume the previous unit's approach transfers. Retire the vendored
pysilicon when convenient; the course is not running, so partially-integrated
state is fine as long as breakage is legible.

> **Prompt:** (1) When you're ready, delete the vendored `pysilicon/` directory
> (it remains in git history via the `pre-waveflow-migration` tag); optionally
> leave a stub `pysilicon/__init__.py` that raises a clear "migrated to waveflow —
> integrate this unit" error so any not-yet-integrated unit fails legibly.
> (2) Take the next unit from `plans/migration_tracker.md` and integrate it
> end-to-end against waveflow's current API **in whatever way fits that unit** —
> different units will use different waveflow subsystems
> (`hw.dataschema`, `hw.fixpoint`, `build.*`, `simulation.*`, `utils.vcd/timing`,
> `toolchain.*`, …). Update its docs + the Getting Started works-list; set its
> tracker status. For units not worth integrating now, mark them `deferred` and
> add a "⚠️ Under migration" banner to their docs. Integrate **one unit per
> session** and stop for review.

**Done when:** each unit in the tracker is `integrated` or `deferred` (none
silently `todo`), and `pysilicon/` is gone.

---

## Docs track — build the docs as we migrate (runs alongside Steps 3–7)

**Why:** the site (just-the-docs theme) currently has **no front door**.
Installation instructions are scattered across four Support sub-sections
(Vitis/Vivado, FPGA boards, GitHub repo, NYU remote), so a first-time visitor —
or the author returning after a break — goes looking for "Getting Started" and
finds nothing. Fix that with a curated top-level **Getting Started** section,
filled in as the migration progresses.

**Design decisions:**
- **Add a new top-level `Getting Started` section** at `nav_order: 1` (the
  curated, linear front door). Bump the existing sections down: Demos → 2,
  Support Material → 3, NYU class → 4, Labs → 5, AI Autograder → 6, Project → 7.
- **Link, don't move, the heavy tool-install pages.** The Vitis/Vivado install
  (`docs/support/amd/`, ~12 screenshots) and board pages (`docs/support/hw_setup/`)
  stay whole under Support Material as reference; Getting Started *sequences and
  links into* them rather than absorbing/fragmenting them.
- **Pull the "get the code + Python environment" content up** into Getting
  Started — that's the genuine core (`docs/support/repo/python.md` + `repo.md`),
  and it is changing in this migration anyway (waveflow + hwdesign editable
  installs from Step 3).
- Most students take the **free-software path**; boards/NYU-server are optional
  "going further" links, not front-and-center.

**Target Getting Started outline:**
1. *What you need* — free-software path vs full board path.
2. *Install the tools* — links to Support ▸ Vitis/Vivado and ▸ FPGA boards.
3. *Get the code & set up Python* — clone repo; `pip install -e .` (hwdesign)
   and the waveflow editable install from Step 2/3. **Owned here.** (fill at Step 3)
4. *Run your first demo* — link to the golden-slice demo. (fill at Step 6)

### Docs prompt A — scaffold the front door (do early, alongside Step 3) — ✅ DONE 2026-06-23

**Status:** created `docs/getting_started/index.md` (`nav_order: 1`) with the
four-part outline; sections 1–2 link to Support ▸ Vitis/Vivado and ▸ FPGA Boards;
sections 3–4 are marked placeholders (filled by Docs prompt B / first-unit work).
Renumbered the other top-level sections: Demos 2, Support 3, NYU 4, Labs 5, AI
Autograder 6, Project 7. Added a top-of-page "⚠️ Under migration" banner.


> **Prompt:** Create a new top-level docs section "Getting Started" for the
> just-the-docs site. Add `docs/getting_started/index.md` with front matter
> `title: Getting Started`, `parent: Hardware Design`, `nav_order: 1`,
> `has_children: true`, and renumber the other top-level section index files so
> the order becomes Getting Started (1), Demos (2), Support Material (3), NYU
> class (4), Labs (5), AI Autograder (6), Project (7). Populate the page with the
> four-part outline above: sections 1–2 link to the existing Support pages
> (`docs/support/amd/`, `docs/support/hw_setup/`); leave clearly-marked
> placeholders for section 3 (Get the code & Python env — filled in Step 3) and
> section 4 (Run your first demo — filled in Step 6). Do not delete or move the
> existing Support pages.

### Docs prompt B — fill as the migration proceeds

> **Prompt:** Update Getting Started section 3 ("Get the code & set up Python")
> from the install story established in Step 3 (clone repo; `pip install -e .`;
> the chosen waveflow install; the Sept release-pin note), reusing/condensing
> `docs/support/repo/python.md`. [After Step 6:] fill section 4 to point at the
> first migrated demo as the recommended first run. As more demos/units migrate,
> keep a short "what currently works" list in Getting Started and add
> "⚠️ Under migration" banners to docs pages whose code is not yet ported.

---

## How to use this plan with Claude CLI

- Run steps **in order**; 1–4 are safe and reversible, only 7 deletes content.
- Hand Claude one **Prompt** block at a time. After Steps 4+ you can also say
  e.g. *"continue the migration: do the next 3 `todo` demos in
  `plans/migration_tracker.md` following the recipe in `plans/migration.md`."*
- The tracker (`plans/migration_tracker.md`) is the source of truth for
  progress — keep it updated so the work is resumable across sessions.
- The **Docs track** runs alongside the steps: do Docs prompt A early (with
  Step 3) to stand up the Getting Started front door, then Docs prompt B as
  install/demo details land (Steps 3 and 6+).

## Per-unit integration log (append one entry per unit, from Step 6 on)

Each unit's integration is bespoke, so this is a **log**, not a reusable recipe.
For each integrated unit, capture: which waveflow subsystems it used, what was
unit-specific, anything that turned out reusable (→ candidate for the `hwdesign`
package), and any waveflow gaps/bugs found (→ upstream to waveflow).

_TBD — first entry added during Step 6._
