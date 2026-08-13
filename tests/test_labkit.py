"""Tier 0 — labkit turns an annotated solution into a student tree, or refuses to.

Fixtures are synthetic rather than the real labs: the solutions live in the
private repository and must not be copied here, even as test data. What is being
tested is the engine and the guards, and neither needs a real lab to exercise.

The guards get as much attention as the happy path on purpose. This tool writes
into a public git repository, and the failure it exists to prevent — a solution
in the public history — is one that cannot be undone.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from hwdesign.labkit.markers import MarkerError, redact
from hwdesign.labkit.publish import PublishError, load_manifest, publish

SV = textwrap.dedent("""\
    module cubic (input logic clk, output logic signed [15:0] y);
        always_comb begin
            // TODO:  Compute the following intermediate values
            // x2_s1_next = ...  x squared term
    // BEGIN SOLUTION
            x2_s1_next = sat( (x_s0 * x_s0) >>> FBITS );
            ax1_s1_next = sat( ((a1_s0 * x_s0) >>> FBITS) + a0_s0 );
    // END SOLUTION
        end
    endmodule
    """)

PY = textwrap.dedent("""\
    import numpy as np

    def subc_divide(a, b, nbits=16):
        if b == 0:
            raise ValueError("Division by zero is not allowed.")

        # TODO: Implement the conditional subtraction division algorithm
    # BEGIN SOLUTION
        z = np.uint32(0)
        for _ in range(nbits):
            z <<= 1
        return z
    # BEGIN STUB
    #     return np.uint32(0)
    # END SOLUTION
    """)


# ---------------------------------------------------------------------------
# The engine
# ---------------------------------------------------------------------------

def test_solution_block_is_removed_and_the_todo_comment_stays():
    result = redact(SV, Path("cubic.sv"))

    assert "x2_s1_next = sat(" not in result.text
    assert "// TODO:  Compute the following intermediate values" in result.text
    assert "// x2_s1_next = ...  x squared term" in result.text
    # The surrounding structure has to survive, or the file will not elaborate.
    assert "always_comb begin" in result.text and "endmodule" in result.text
    assert result.blocks == 1


def test_stub_is_uncommented_with_its_indentation_intact():
    result = redact(PY, Path("subc_divide.py"))

    # The STUB line is written at column 0; stripping "# " leaves the four spaces
    # the author put after it, which is the indent a function body needs.
    assert "    return np.uint32(0)" in result.text.split("\n")
    assert "z = np.uint32(0)" not in result.text
    # The TODO comment lives outside the block, so it needs no directive.
    assert "    # TODO: Implement the conditional subtraction" in result.text


def test_todo_section_emits_student_only_text():
    src = "// BEGIN SOLUTION\nassign y = x;\n// BEGIN TODO\n// TODO: drive y\n// END SOLUTION\n"
    result = redact(src, Path("m.sv"))

    assert "assign y = x;" not in result.text
    assert "// TODO: drive y" in result.text


def test_no_marker_leaves_the_file_alone():
    src = "module m; endmodule\n"
    assert redact(src, Path("m.sv")).text == src


def test_a_marker_must_be_the_whole_comment():
    """Otherwise prose mentioning a marker would silently change what ships."""
    src = "int x = 1; // BEGIN SOLUTION is the marker we use\nint y = 2;\n"
    result = redact(src, Path("m.cpp"))
    assert result.blocks == 0 and result.text == src


@pytest.mark.parametrize("src,expected", [
    ("// END SOLUTION\n", "with no BEGIN SOLUTION open"),
    ("// BEGIN SOLUTION\n// BEGIN SOLUTION\n// END SOLUTION\n", "markers do not nest"),
    ("// BEGIN SOLUTION\nx;\n", "still open"),
    ("// BEGIN TODO\n// hi\n// END SOLUTION\n", "must follow BEGIN SOLUTION"),
])
def test_malformed_markers_raise(src, expected):
    with pytest.raises(MarkerError, match=expected):
        redact(src, Path("m.sv"))


def test_unknown_extension_refuses_rather_than_guessing():
    with pytest.raises(MarkerError, match="No comment syntax known"):
        redact("anything", Path("thing.vhdl"))


# ---------------------------------------------------------------------------
# Publishing
# ---------------------------------------------------------------------------

def _lab(tmp_path: Path, manifest: str, files: dict[str, str] | None = None) -> Path:
    soln = tmp_path / "soln" / "labs" / "prng"
    soln.mkdir(parents=True)
    (soln / "lab.toml").write_text(textwrap.dedent(manifest), encoding="utf-8")
    for rel, text in (files or {"prng.sv": SV, "tb_prng.sv": "// testbench\n"}).items():
        path = soln / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return soln


BASIC = """
    [lab]
    name = "prng"
    public = "../../../pub/labs/prng"
    full = ["tb_prng.sv"]
    partial = ["prng.sv"]
    """


def test_publish_splits_full_from_partial(tmp_path):
    soln = _lab(tmp_path, BASIC)
    report = publish(soln)

    pub = tmp_path / "pub" / "labs" / "prng"
    assert (pub / "tb_prng.sv").read_text(encoding="utf-8") == "// testbench\n"
    assert "x2_s1_next = sat(" not in (pub / "partial" / "prng.sv").read_text(encoding="utf-8")
    assert (len(report.copied), len(report.redacted), report.blocks) == (1, 1, 1)


def test_dry_run_writes_nothing(tmp_path):
    soln = _lab(tmp_path, BASIC)
    report = publish(soln, dry_run=True)

    assert not (tmp_path / "pub").exists()
    assert len(report.redacted) == 1 and report.dry_run


def test_private_files_are_not_published(tmp_path):
    soln = _lab(tmp_path, """
        [lab]
        name = "prng"
        public = "../../../pub/labs/prng"
        full = ["tb_prng.sv"]
        partial = ["prng.sv"]
        private = ["notes.md"]
        """, {"prng.sv": SV, "tb_prng.sv": "// tb\n", "notes.md": "the answer is 42\n"})
    publish(soln)

    pub = tmp_path / "pub" / "labs" / "prng"
    assert not (pub / "notes.md").exists()
    assert not (pub / "partial" / "notes.md").exists()


def test_build_residue_is_ignored_by_default(tmp_path):
    soln = _lab(tmp_path, BASIC)
    (soln / "sim" / "prng").mkdir(parents=True)
    (soln / "sim" / "prng" / "xsim.log").write_text("noise", encoding="utf-8")
    (soln / "submitted_results.json").write_text("{}", encoding="utf-8")
    (soln / "solution.zip").write_bytes(b"PK")

    publish(soln)   # would raise on an unlisted file if these were not ignored
    assert not (tmp_path / "pub" / "labs" / "prng" / "sim").exists()


# ---------------------------------------------------------------------------
# The guards
# ---------------------------------------------------------------------------

def test_an_unlisted_file_is_an_error(tmp_path):
    soln = _lab(tmp_path, BASIC)
    (soln / "helper.py").write_text("# helper\n", encoding="utf-8")

    with pytest.raises(PublishError, match="in no list in lab.toml"):
        publish(soln)
    assert not (tmp_path / "pub").exists()


def test_a_listed_file_that_does_not_exist_is_an_error(tmp_path):
    soln = _lab(tmp_path, """
        [lab]
        name = "prng"
        public = "../../../pub/labs/prng"
        full = ["tb_prng.sv", "gone.sv"]
        partial = ["prng.sv"]
        """)
    with pytest.raises(PublishError, match="do not exist"):
        publish(soln)


def test_a_partial_file_with_no_markers_is_an_error(tmp_path):
    """The likeliest way to ship a whole solution: forget the annotations."""
    soln = _lab(tmp_path, BASIC, {"prng.sv": "module m; endmodule\n", "tb_prng.sv": "// tb\n"})

    with pytest.raises(PublishError, match="contains no BEGIN SOLUTION"):
        publish(soln)
    assert not (tmp_path / "pub").exists()


def test_a_solution_line_reaching_the_output_is_caught(tmp_path):
    """The leak guard: the same code listed as full and redacted as partial."""
    soln = _lab(tmp_path, """
        [lab]
        name = "prng"
        public = "../../../pub/labs/prng"
        full = ["tb_prng.sv"]
        partial = ["prng.sv"]
        """, {"prng.sv": SV,
              # A stray copy of a solution line in a file shipped whole.
              "tb_prng.sv": "// tb\nx2_s1_next = sat( (x_s0 * x_s0) >>> FBITS );\n"})

    with pytest.raises(PublishError, match="contains a line from inside a BEGIN SOLUTION"):
        publish(soln)


def test_the_leak_guard_does_not_fire_on_stub_lines(tmp_path):
    """A STUB is often a cut-down solution, so its lines collide with dropped ones.

    They are author-written student-facing content by construction, so they can
    never be a leak — flagging them would make STUB unusable.
    """
    src = ("def f(path):\n"
           "# BEGIN SOLUTION\n"
           "    do_something_elaborate(path)\n"
           "    return path_to_the_answer\n"
           "# BEGIN STUB\n"
           "#     return path_to_the_answer\n"
           "# END SOLUTION\n")
    soln = _lab(tmp_path, BASIC, {"prng.sv": SV, "tb_prng.sv": "// tb\n",
                                  "helper.py": src})
    (soln / "lab.toml").write_text(textwrap.dedent("""
        [lab]
        name = "prng"
        public = "../../../pub/labs/prng"
        full = ["tb_prng.sv"]
        partial = ["prng.sv", "helper.py"]
        """), encoding="utf-8")

    publish(soln)   # must not raise
    out = (tmp_path / "pub/labs/prng/partial/helper.py").read_text(encoding="utf-8")
    assert "    return path_to_the_answer" in out
    assert "do_something_elaborate" not in out


def test_allow_shared_excuses_reviewed_boilerplate(tmp_path):
    """Library boilerplate can be identical in a solution block and a shipped file."""
    soln = _lab(tmp_path, BASIC, {
        "prng.sv": ("module m;\n// BEGIN SOLUTION\n"
                    "    always_comb this_is_the_real_answer = 1;\n"
                    "    common_boilerplate_call(argument);\n"
                    "// END SOLUTION\nendmodule\n"),
        "tb_prng.sv": "// tb\ncommon_boilerplate_call(argument);\n"})

    with pytest.raises(PublishError, match="contains a line from inside"):
        publish(soln)

    (soln / "lab.toml").write_text(textwrap.dedent("""
        [lab]
        name = "prng"
        public = "../../../pub/labs/prng"
        full = ["tb_prng.sv"]
        partial = ["prng.sv"]
        allow_shared = ["common_boilerplate_call(argument);"]
        """), encoding="utf-8")
    publish(soln)   # now allowed

    # The excuse is narrow: it does not extend to anything else in the block.
    assert "this_is_the_real_answer" not in (
        tmp_path / "pub/labs/prng/partial/prng.sv").read_text(encoding="utf-8")


def test_the_leak_guard_does_not_fire_on_structural_lines(tmp_path):
    """``end`` and ``);`` are dropped constantly and are not evidence of anything."""
    src = "module m;\n    always_comb begin\n// BEGIN SOLUTION\n        y = x;\n// END SOLUTION\n    end\nendmodule\n"
    soln = _lab(tmp_path, BASIC, {"prng.sv": src, "tb_prng.sv": "    end\n        y = x;\n"})

    publish(soln)   # must not raise: both lines are short and appear outside the block


def test_publishing_into_the_solution_tree_is_refused(tmp_path):
    soln = _lab(tmp_path, """
        [lab]
        name = "prng"
        public = "./out"
        full = ["tb_prng.sv"]
        partial = ["prng.sv"]
        """)
    with pytest.raises(PublishError, match="overlaps the solution directory"):
        load_manifest(soln)


def test_a_partial_file_with_no_comment_syntax_is_refused(tmp_path):
    soln = _lab(tmp_path, """
        [lab]
        name = "prng"
        public = "../../../pub/labs/prng"
        partial = ["data.bin"]
        """, {"data.bin": "\x00binary\n"})
    with pytest.raises(MarkerError, match="cannot be redacted"):
        publish(soln)


# ---------------------------------------------------------------------------
# The CLI
# ---------------------------------------------------------------------------

def test_check_reports_stale_then_clean(tmp_path, capsys):
    from hwdesign.labkit.publish import main

    soln = _lab(tmp_path, BASIC)
    assert main(["check", str(soln)]) == 1
    assert "stale:" in capsys.readouterr().out

    assert main(["publish", str(soln)]) == 0
    capsys.readouterr()
    assert main(["check", str(soln)]) == 0
    assert "up to date" in capsys.readouterr().out


def test_cli_reports_an_error_without_a_traceback(tmp_path, capsys):
    from hwdesign.labkit.publish import main

    soln = _lab(tmp_path, BASIC)
    (soln / "helper.py").write_text("# helper\n", encoding="utf-8")

    assert main(["publish", str(soln)]) == 1
    assert "in no list in lab.toml" in capsys.readouterr().err
