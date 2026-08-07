---
title: Final Submission
parent: Project
nav_order: 4
has_children: false
---

# Final Submission

## Submission Format

Similar to the [planning steps](./planning.md), simply submit the link to your GitHub repository to the LLM grader.  
The GitHub repo should contain **all documentation, code, and results** needed for the grader to evaluate your project.

The LLM grader can only assess what it can read directly from your repository, so your repo must include:

- Clear, well‑organized Markdown files — a `README.md` describing what you built, with your [planning documents](./plan.md) in a `plans/` directory  
- All RTL/HLS source code and testbench files  
- Simulation outputs, logs, or result summaries  
- Any diagrams, tables, or explanations referenced in your write‑up  
- A structure that makes it easy to navigate and understand your design

If someone — **or an automated tool like the LLM grader** — opened your repository, they should be able to understand your design, reproduce your results, and follow your reasoning without needing anything outside the repo.

# Final Grading (25 points total)

Grading happens in two stages:

1. **LLM grader — 20 points.** An explicit rubric applied automatically to your repository.
2. **Instructor assessment — 0 to 5 points.** Added on top of the grader's score.

## LLM grader rubric (20 points)

The grader reads your repository but **does not execute anything**. Every claim
therefore has to be supported by something it can read — documentation, result
tables, logs, or committed synthesis reports.

| Category | Points | What earns credit |
|---|---|---|
| **a. IP interface definition** | 4 | Core operations clearly defined (2) · messages and interfaces defined (2) |
| **b. IP design** | 6 | Architecture described (3) · design efficiency considered (3) |
| **c. Verification and evaluation** | 7 | Functional verification evidence (4) · performance and resource results (3) |
| **d. Organization and documentation** | 3 | Reproducibility and automation (3) · up to **−1** for a cluttered or incomplete repo |

What each category is looking for:

- **IP interface definition** — the computation the accelerator performs, specific
  enough that a reader can tell what inputs become what outputs; and the
  interfaces to the rest of the system (AXI4‑Stream, AXI‑Lite, shared memory,
  FIFOs, DMA, register maps), including what information they actually carry.
- **IP design** — a coherent top‑level architecture with its major blocks and how
  they connect, plus explicit reasoning about efficiency: pipelining,
  parallelism, buffering, reuse, memory access. A simple design is fine as long
  as you show you considered the tradeoffs.
- **Verification and evaluation** — credible evidence of functional correctness
  (simulation results, reference comparisons, testbench output), *and* synthesis
  or implementation numbers (latency, throughput, clock, utilization) interpreted
  against the goals you set.
- **Organization and documentation** — clear instructions plus some real
  automation: scripts, make targets, `.tcl` flows, or notebooks with a documented
  execution path. A README alone earns partial credit.

{: .warning }
> **The grader cross‑checks your documentation against your code.** If your
> write‑up claims a feature — a pipelined loop, an unrolled loop, a particular
> interface — the grader looks for the corresponding pragma or structure in your
> `.cpp`, `.h`, or `.tcl` files. If the claim is not backed by the code, that
> sub‑criterion is scored **0** and the discrepancy is noted. Make claims you can
> point to, and link to specific files where you can.

## Instructor assessment (0–5 points)

After the grader runs, the instructor reviews the result and adds between **0 and
5 points**. This covers what an automated rubric cannot judge — for example the
in‑class presentation, the ambition of the project, or work that is clearly
strong but does not map neatly onto a rubric line.

## Practical advice

- **Use `README.md` or `index.md`.** Markdown is the most AI‑readable format.
  Link out to sub‑pages for individual modules.
- **Commit your evidence.** The grader will not run your code, so synthesis
  reports and summary tables must be *in* the repository to earn verification
  credit.
- **Keep the repo clean.** Vivado and Vitis logs, journals, caches, and simulator
  output cost you up to a point if they make the repo hard to inspect. A large
  repo is fine if it is organized and the project files are easy to find.
- **Iterate before submitting.** You are encouraged to run the grader on your
  repository — or use other AI tools — and refine the design and documentation in
  response.
- **Check your grader settings.** Select a high‑reasoning model (for example
  `gpt-5.4`) via the gear icon in the preferences dialog, and set the timeout to
  at least 100 seconds so the grader has time to inspect the repo.

It is completely acceptable if your design deviated from the original plan — that
is the nature of research and learning. What matters is that the final
documentation clearly explains the design you actually built.
