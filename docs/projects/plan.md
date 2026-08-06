---
title: Detailed Design Plan
parent: Project
nav_order: 3
has_children: false
---

# Detailed Design Plan

{: .important }
> **There is no submission and no grade for this stage.** Because of time
> constraints, the course goes directly from the
> [initial plan](./planning.md) to the [final submission](./final.md).
> Read this page anyway — the reason is below.

## Why this is not optional work

Nothing on this page is graded *now*. Almost all of it is graded *later*.

The [final rubric](./final.md#llm-grader-rubric-20-points) awards 20 points for
what the LLM grader can read in your repository. Three of its four categories
are decided by the work you do at this stage:

| What you develop here | Final rubric category | Points |
|---|---|---|
| Module definitions | b. IP design — architecture and efficiency | 6 |
| Testbench definition | c. Verification and evaluation | 7 |
| Development steps | d. Organization and documentation | 3 |
| | **Total** | **16 of 20** |

So the difference between a team that plans and a team that does not is *not*
whether these documents get written. It is whether they get written in week six,
when they still shape the design, or in the last week before the deadline, when
they can only describe whatever happened.

Verification is the sharpest example. Evidence of correctness cannot be produced
retroactively. If your golden model does not exist until the final week, you
have nothing to compare against, no results to show, and 7 of the 20 points are
simply gone. Building the reference alongside the design costs almost nothing;
reconstructing it at the end is usually impossible.

## Where to put it

Keep your planning documents in a `plans/` directory in your project repository:

```
your-repo/
├── README.md              <- authoritative: what you actually built
├── plans/
│   ├── initial_plan.md    <- your graded outline
│   ├── modules.md
│   ├── testbench.md
│   └── milestones.md
├── src/
└── results/
```

This supports the final rubric's "can a reader follow the development from
design to implementation" criterion, and it gives an AI assistant a stable place
to read your design context from.

---

## 1. Module Definitions

For each module, describe:

- Its **function** — what it computes, in one or two sentences.
- Its **inputs and outputs** — including data types and widths.
- **Message formats** and control signals — what actually crosses the interface.
- Any **timing assumptions** or sequencing requirements — what must happen
  before what, and what happens if data arrives faster than you can consume it.

Prefer several small modules over one large one. Decomposition is not just
tidiness: it is what lets you unit‑test pieces independently and what exposes
opportunities for parallelism.

## 2. Testbench Definition

This is the section most worth doing carefully, and the one most often skipped.

- **What is your golden model?** What defines *correct* for this design? Usually
  a Python reference implementation, as used in class. Write it early — it is
  what every later result is measured against.
- **What scenarios will you test?** Typical inputs, boundary values, and the
  cases you suspect will break.
- **How will you decide correctness?** Bit‑exact comparison, a tolerance on a
  floating‑point result, or a property that must hold. Say which, and why it is
  the right check for this design.
- **How will you measure performance?** Latency, throughput, initiation
  interval, resource utilization — and what target you are aiming for.

## 3. Development Steps

Break the project into **small, individually testable milestones**:

- What is the smallest piece you can build and verify on its own?
- What unit test proves each milestone works?
- In what order do the pieces integrate, and what do you test at each junction?

A good milestone list is one where you are never more than a few days from
something that runs. It is also the plan an AI assistant can actually help you
execute, one step at a time.

---

## Working with an AI assistant

You are expected to use AI throughout this project. The risk is not that you use
it — it is that you accept its first answer. A language model will confidently
produce a module decomposition that ignores initiation interval, assumes
unlimited on‑chip memory, or invents an interface that cannot be built. Early on,
plausible and correct are hard to tell apart.

Three habits that make the difference:

### Ask for alternatives, not an answer

Ask for **two or three different decompositions** of your design, then choose
between them and write down *why you rejected the others*. The rejection
reasoning is where the engineering happens, and it is the part the model cannot
do for you without you engaging.

### Interrogate the design

Put these back to the assistant — and make sure you understand the answers:

- What is the initiation interval of this loop, and what limits it?
- Where does this array live: registers, BRAM, or external memory?
- What happens if input arrives faster than this module can consume it?
- What is the bit width here, and where could it overflow?
- Which of these operations actually run in parallel, and which are serialized?

Vague answers to these questions are a reliable sign that the design is not yet
real.

### Remember the grader checks your claims against your code

{: .warning }
> The final grader **cross‑references your documentation against your source**.
> If a document claims a pipelined loop, an unrolled loop, or a particular
> interface, the grader looks for the corresponding pragma or structure in your
> `.cpp`, `.h`, or `.tcl` files. If it is not there, that criterion scores **0**
> and the discrepancy is noted.
>
> An AI‑written plan that you never reconciled with your implementation does not
> just fail to help — it actively costs you points.

## Keeping your plans honest

Designs change once real synthesis results arrive. That is expected and fine —
it is what the planning is for.

What matters at the end:

- **Your `README.md` is authoritative.** It must describe the design you
  actually built.
- **Label superseded plans as historical.** An abandoned design left sitting in
  `plans/` reads to the grader as a claim about what you delivered, and can cost
  you points under the cross‑reference rule above.
- **Say where and why the design changed.** Explaining that you replaced a
  systolic array with a simpler pipeline after seeing the resource numbers is
  good engineering documentation, not an admission of failure.

---

Go to [final submission](./final.md)
