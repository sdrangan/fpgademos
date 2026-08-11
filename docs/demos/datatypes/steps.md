---
title: Running the Demo in Steps
parent: Integers, Overflow and Bit Packing
nav_order: 1
has_children: false
---

# Building a Design in Steps

Hardware is not built in one go.  Even a small design goes through a sequence of
stages, and each stage consumes what the previous one produced:

~~~
    model in Python  ->  generate test vectors  ->  write the RTL
        ->  simulate  ->  compare against the model  ->  synthesise
        ->  check timing and resources  ->  ...
~~~

The stages are slow and uneven.  Python modelling takes seconds; a simulation
takes minutes; synthesis can take an hour.  So you almost never want to run the
whole thing — you want to re-run the one stage you just changed, and reuse
everything before it.

Doing that by hand is how mistakes happen.  You change the Python model, re-run
the simulation, forget to regenerate the vectors, and compare the new RTL against
last week's expected answers.  The comparison passes.  Nothing tells you.

The [Waveflow](https://sdrangan.github.io/waveflow/docs/) package has a system
for this called the **BuildDag**, and the demos and labs in this class use it to
walk through each stage.  It is worth ten minutes now because you will see it in
every unit from here on.

## Steps and artifacts

Two ideas, and that is genuinely all of it.

A **step** is one stage of the build.  A **artifact** is a named thing a step
produces — usually a file, sometimes a Python object held in memory.

Every step declares what it **consumes** and what it **produces**:

~~~python
class IntProdGenStep(BuildStep):
    description = "Python golden model for int_prod; writes the stimulus and expected outputs."
    consumes = ["int_prod_source"]
    produces = {"int_prod_vectors": Path("vectors/int_prod_in.txt")}

    def run(self, config, **_):
        return {"int_prod_vectors": gen_int_prod_vectors(config.root_dir / "vectors")}
~~~

Notice what the step does *not* say: it never mentions which step runs before it.
It only names the artifact `int_prod_source`, and something else in the graph
declares that it produces an artifact by that name.  The dependency is inferred
from the names.

That is why it is a **DAG** — a directed acyclic graph.  You describe what each
step needs and what it makes, and the graph of dependencies falls out.  Waveflow
then works out a legal order to run them in.

The `run()` method is deliberately thin.  In this demo every step body is a
single call into an ordinary Python function, so those functions can also be
imported and called directly.  The build system orchestrates; it does not hide
anything from you.

## Building the graph

The whole graph for this demo is assembled in one function:

~~~python
def build_datatypes_dag() -> BuildDag:
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
        outputs={"int_prod_sv": Path("vectors/int_prod_sv.txt")},
        sim_dir=Path("sim/int_prod"),
        plusargs={"vecdir": Path("vectors")},
    ))
    dag.add(IntProdCheckStep(name="int_prod_check"))
    dag.add(IntProdDocsStep(name="int_prod_docs"))

    # ... the same four steps again for samp_pack ...

    return dag
~~~

A `SourceStep` is a step with no work to do: it just declares that a file exists
and is a starting point.  That matters because it puts the `.sv` files *into* the
dependency graph — edit `int_prod.sv` and the simulation that depends on it
becomes out of date automatically.

`SvSimStep` is Waveflow's built-in step for running a SystemVerilog testbench
through Vivado's simulator.  It compiles, elaborates and runs, and it declares
the file the testbench writes so the graph knows what the simulation actually
produced.

The result for this demo is two independent chains:

~~~
int_prod_source  ─→ int_prod_gen  ─→ int_prod_sim  ─→ int_prod_check  ─→ int_prod_docs
samp_pack_source ─→ samp_pack_gen ─→ samp_pack_sim ─→ samp_pack_check ─→ samp_pack_docs
~~~

They never touch each other, which is exactly why this is a graph and not a list.
Asking for a `samp_pack` stage runs nothing from `int_prod` at all.

## Driving it from the command line

The script ends with `run_dag_cli`, which gives every build in this class the
same set of commands.

### What is in the build

~~~bash
    python datatypes_build.py --list-steps
~~~

Just the step names, in the order they would run.

~~~bash
    python datatypes_build.py --list-steps-verbose
~~~

The same, with each step's description and its artifacts:

~~~
int_prod_gen
    Python golden model for int_prod; writes the stimulus and expected outputs.
    consumes: int_prod_source
    produces: int_prod_vectors
int_prod_sim
    Run a SystemVerilog testbench through xvlog/xelab/xsim.
    consumes: int_prod_source, int_prod_tb_source, int_prod_vectors
    produces: int_prod_sim, int_prod_sv
~~~

This listing is generated from the graph itself, so it cannot go out of date.
When you want to know what a build actually does, run this before reading
anything.

~~~bash
    python datatypes_build.py --list-artifacts
~~~

Every artifact, which step produces it, and where it lands on disk.

### What is already built

~~~bash
    python datatypes_build.py --status
~~~

For each artifact: whether it exists, how old it is, and whether anything it
depends on has changed since.  Answers "did I actually run this?", which is a
more common question than you would think.

### Running

~~~bash
    python datatypes_build.py --through int_prod_gen
~~~

Runs everything needed to produce `int_prod_gen`, and stops.  This is the one you
will use most.

The build tells you what it did with each step:

~~~
int_prod_source:
    int_prod.sv
    UP-TO-DATE
int_prod_gen:
    vectors\int_prod_in.txt
    RUNNING...
    PASSED
~~~

`UP-TO-DATE` means the step's outputs are already newer than everything it
depends on, so it was skipped.  That is the mechanism that lets you re-run a
later stage without repeating the earlier ones — and it is also why `--through`
is all you need to run a single stage in isolation.  There is no `--only` flag,
and it would not add anything: everything before your target is skipped anyway.

`--through` on a machine with **no Vivado installed** still gets you through
`int_prod_gen` and `samp_pack_gen`, which is the entire Python half of the demo.

To run the whole thing, both branches, leave the flag off:

~~~bash
    python datatypes_build.py
~~~

### Forcing a rebuild

Freshness is judged by file timestamps, which is usually right and occasionally
not — if you want a step to run again regardless:

~~~bash
    python datatypes_build.py --force-step int_prod_sim   # just this one
    python datatypes_build.py --force                     # all of them
~~~

## When something goes wrong

A failing step stops the build and reports where:

~~~
samp_pack_check:
    results\samp_pack_report.json
    RUNNING...
    FAILED: STOP — SystemVerilog disagreed with the Python golden model: ...
~~~

followed by the full Python traceback, with the file and line.  Read the last few
lines of it first — that is where the actual problem is, and the frames above it
are just the build system getting there.

---

Go to [the integer product](./int_prod.md).
