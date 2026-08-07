---
title: Plannng the Project
parent: Project
nav_order: 2
has_children: false
---

## AI‑Based Planning of Your Project

### Overview

As described before, the project is designed around an [**AI‑assisted planning workflow**](./ai_workflow.md). 
Before you begin implementing your hardware IP, you will use AI tools to help you explore design options, refine your architecture, and iteratively improve your specification. The planning phase has two stages:

- **Initial Plan** — a high‑level description of your IP’s purpose, behavior, and overall architecture, written with the help of AI to clarify the problem and surface design choices. **This is submitted and graded** (20 points), and is the subject of this page.
- **[Detailed Design Plan](./plan.md)** — module interfaces, testbench strategy, and an incremental development path. This is **not submitted**, but it produces the documents that most of your final grade is based on.

The initial plan is evaluated using the [LLM grader](../aiautograder/), which provides rubric‑aligned feedback to help you strengthen your design. As usual, you can submit to the LLM grader as many times as you want until you are satisfied with the design.  You are expected to use AI tools actively throughout this process—not as a replacement for your own reasoning, but as a structured partner in exploring alternatives, checking consistency, and improving clarity.

---

## GitHub Repository

All project materials must be maintained in a **GitHub repository**.  
To begin, create a new repo for your team and place all planning documents, code, and results there.

Why GitHub?

- It provides **version control**, allowing you to track changes and collaborate effectively.
- It is the standard tool used in industry for hardware and software development.
- It keeps your documentation, code, and test results organized in one place.
- The **LLM grader uses web search** to inspect your repository directly, enabling it to read your planning documents, module definitions, and final implementation.

Your repo will become the central artifact of your project — treat it as a professional engineering repository.

---

## Initial Plan

Create a file named something like `initial_plan.md` in your repo.  
This document should contain **three short sections**, written clearly and concisely.
I will put some [examples](./example_plans/) if you want some ideas.  

### 1. Project Team

List the members of your project team by name. Each project needs **at least two
students**. A one‑person submission will be accepted, but you will be told to find
a partner.

### 2. IP Definition

Describe:

- **What your IP does**  
  The core functionality, the problem it solves, and the domain it applies to.

- **How it interacts with the PS and peripherals**  
  What data it receives, what it outputs, and how it is controlled.

- **The mathematical operations involved**  
  Be precise. Include formulas, pseudo‑code, or algorithmic descriptions as needed.

A good IP definition makes the intended behavior unambiguous.

### 3. IP Architecture

Describe:

- **The major sub‑modules**  
  What components your design will be broken into.

- **How the sub‑modules communicate**  
  Interfaces, dataflow, control signals, memory access, etc.

- **Why modularization matters**  
  Explain why you are decomposing the design in this way and how it supports incremental development and testing.

### Submitting the Initial Plan

To submit your initial plan to the LLM grader:

1. Commit `initial_plan.md` to your GitHub repo.
2. Copy the **GitHub URL** of the file.
3. Paste the URL into the LLM grader submission box.

The grader has been provided with the rubric for this stage and will give structured feedback.  
You are encouraged to use AI extensively while drafting this document — the clearer your plan, the more effective AI will be in later stages.

### Grading the Initial Plan (20 points)

This submission is scored entirely by the LLM grader — unlike the
[final submission](./final.md), the instructor does not adjust the result.

| Category | Points | What earns credit |
|---|---|---|
| **a. GitHub repo** | 2 | A link to the repo, page, or file holding the outline |
| **b. Project team** | 2 | Team members clearly named — you need **at least two students** |
| **c. IP definition** | 6 | What the IP does and the mathematical operations it performs (4) · why those operations suit hardware acceleration (2) |
| **d. IP architecture** | 10 | Sub‑modules described (5) · interfaces described (5) · up to **−2** if one module is oversized |

Where points are most often lost:

- **Submitting without a repo link.** You may paste the outline directly into the
  submission box instead, and the other 18 points are still available — but the
  2 repo points are not. Create the repo.
- **Vague mathematics.** "It processes the signal" does not earn the 4 points.
  Name the operation — matrix multiply, FIR filter, FFT, sorting network — and
  include pseudo‑code or a Python snippet if the operation is unusual. Standard
  operations do not need elaborate detail.
- **Weak motivation.** "Hardware is faster" earns nothing for the 2 motivation
  points. Say *why*: the operation is computationally intensive, highly
  parallel, or latency‑critical.
- **Vague interfaces.** Naming an interface is not enough. Say whether you are
  using AXI4‑Stream, FIFOs, or shared memory, and state what information each
  one carries.
- **One large module.** A single module is acceptable if the design is genuinely
  small, but an oversized monolithic block costs up to 2 points. Decomposing it
  also gives you more parallelism.

The grader will also suggest existing AMD IPs — an FFT core, for example — where
one could replace something you were planning to build yourself. Following that
advice does not cost you points, and it usually saves effort.

{: .note }
> Before clicking **Grade**, select a high‑reasoning model such as `gpt-5.4` using
> the gear icon beside the Grade button. You may submit as many times as you like.

---

## After the Initial Plan

The initial plan is the only planning document that is submitted and graded.

Before you start building, though, you should work out your module definitions,
your verification strategy, and an incremental development path. Those are not
submitted — but they determine most of your final grade, because the final
rubric scores the documentation that grows out of them. See
[Detailed Design Plan](./plan.md) for what to develop and how to use an AI
assistant well while doing it.

---

By following this planning process, you will create a clear, structured roadmap for your project — one that supports effective collaboration, AI‑assisted development, and a smooth path to your final implementation.

---

Go to [detailed design plan](./plan.md)