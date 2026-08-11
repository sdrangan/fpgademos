"""Tier 2 — the whole flow, including the SystemVerilog simulation.

Needs Vivado, so these are marked ``vivado`` and skipped when it is not
available.  They run against a temporary build root: the ``.sv`` sources come
from the repo, but vectors, sim scratch and reports are written under ``tmp_path``
so running the suite never disturbs the checked-in demo state.

The assertions are thin on purpose.  The check steps raise on any mismatch, so
"the DAG ran to completion" already means "SystemVerilog agreed with Python on
every row".
"""
from __future__ import annotations

import pytest

from waveflow.build.build import BuildConfig

from .conftest import needs_vivado

pytestmark = [pytest.mark.vivado, needs_vivado]


def _run_through(datatypes, tmp_path, target):
    dag = datatypes.build_datatypes_dag()
    results = dag.run(BuildConfig(root_dir=tmp_path), through=target)
    failed = {n: r.message for n, r in results.items() if not r.success}
    assert not failed, f"steps failed: {failed}"
    return results


class TestSampPack:
    def test_simulation_matches_python(self, datatypes, tmp_path):
        _run_through(datatypes, tmp_path, "samp_pack_check")
        report = tmp_path / "results" / "samp_pack_report.json"
        assert report.exists()

    def test_report_records_a_full_match(self, datatypes, tmp_path):
        import json
        _run_through(datatypes, tmp_path, "samp_pack_check")
        data = json.loads((tmp_path / "results" / "samp_pack_report.json").read_text())
        assert data["match"] is True
        assert data["round_trip_ok"] is True
        assert data["rows"] == datatypes.NSAMP


class TestIntProd:
    @pytest.mark.slow
    def test_simulation_matches_python_over_the_whole_input_space(self, datatypes, tmp_path):
        import json
        _run_through(datatypes, tmp_path, "int_prod_check")
        data = json.loads((tmp_path / "results" / "int_prod_report.json").read_text())
        assert data["match"] is True
        assert data["rows"] == len(datatypes.INT_PROD_CASES) + 256 * 256


class TestFailureIsLoud:
    def test_a_corrupted_result_file_fails_the_check(self, datatypes, tmp_path):
        """The check step is the gate; it must raise rather than pass quietly."""
        _run_through(datatypes, tmp_path, "samp_pack_check")

        sv = tmp_path / "vectors" / "samp_pack_sv.txt"
        lines = sv.read_text(encoding="utf-8").splitlines()
        parts = lines[1].split()
        parts[1] = str(int(parts[1]) + 1)          # corrupt one value
        lines[1] = " ".join(parts)
        sv.write_text("\n".join(lines) + "\n", encoding="utf-8")

        with pytest.raises(RuntimeError, match="STOP"):
            datatypes.check_samp_pack(tmp_path / "vectors",
                                      tmp_path / "results" / "samp_pack_report.json")
