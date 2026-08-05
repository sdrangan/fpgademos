---
title: Getting Started
parent: Hardware Design
nav_order: 1
has_children: false
---

# Getting Started

This is the front door to the course: the shortest path from "I just arrived" to
"I ran something." It sequences the setup and links into the detailed
[Support Material](../support/) reference for the parts you need.

> ⚠️ **Under migration (June 2026).** The course tooling is being moved onto the
> [waveflow](https://sdrangan.github.io/waveflow/docs/) package, one unit at a
> time. Sections 3–4 below are being filled in as that work lands; some demos may
> not run yet.

## 1. What you need

Most of the course can be done with **free software only**:

- **Vitis HLS and Vivado** (AMD) — the core tools for designing, simulating, and
  synthesizing hardware. Free to install.
- **Python** — for the demos, simulation, and analysis (via the `waveflow`
  package and this course's `hwdesign` helpers).

You only need an **FPGA board** for the optional hardware-deployment sections.
Everything else runs in simulation on your laptop.

## 2. Install the tools

- **Vitis & Vivado:** follow [Support ▸ Vitis and Vivado](../support/amd/) for
  download and installation (including the Windows walkthrough and which device
  to select).
- **FPGA board (optional):** if you have one, see
  [Support ▸ FPGA Boards](../support/hw_setup/) for the PYNQ-Z2 / RFSoC 4x2 setup.

## 3. Get the code & set up Python

Two steps, in order:

1. **[Clone the repository](../support/repo/repo.md)** — all the course material
   lives in one GitHub repo.
2. **[Install the Python packages](../support/repo/package.md)** — create a
   virtual environment, then install `waveflow` (the hardware modeling
   framework, from GitHub) and `hwdesign` (this course's helpers, from your
   clone). That page ends with a snippet to verify the install.

Instructors and course assistants who need to modify course material or
`waveflow` itself should follow
[Developer Setup](../support/repo/developer.md) instead — students do not need
it.

## 4. Run your first demo

> _To be written (after the first unit is integrated onto waveflow). This will
> point you at one known-working demo to run end-to-end so you can confirm your
> setup._

## Where to go next

- [Demos](../demos/) — worked examples used throughout the course.
- [Labs](../labs/) — hands-on assignments.
- [Support Material](../support/) — the full reference for tools, boards, the
  repository, and the NYU remote server.
