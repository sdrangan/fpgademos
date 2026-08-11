"""Tier 1 — the Python golden models for the Unit 1 demo.

No DAG, no toolchain: these call the plain functions in ``datatypes_build.py``
directly.  They are the cheapest check that a waveflow change has not broken the
demo, and they are the reason those functions are kept out of the step bodies.

Most of these are stated as *properties* — claims that must hold for every input
— rather than comparisons against stored values, so they cover far more than the
handful of vectors the testbench prints.
"""
from __future__ import annotations

import numpy as np
import pytest

W = 8
TW, DW = 8, 12


# ---------------------------------------------------------------------------
# int_prod
# ---------------------------------------------------------------------------

class TestWrapAndSaturate:
    def test_wrap_is_identity_when_the_value_fits(self, datatypes):
        values = np.arange(-128, 128)
        assert np.array_equal(datatypes.wrap(values, W), values)

    def test_wrap_keeps_only_the_low_bits(self, datatypes):
        # 400 -> 0b110010000; the low 8 bits are 0b10010000, which reads as -112.
        assert int(datatypes.wrap(400, W)) == -112

    def test_wrap_lands_in_range(self, datatypes):
        values = np.arange(-40000, 40000, 7)
        out = datatypes.wrap(values, W)
        assert out.min() >= -128 and out.max() <= 127

    def test_wrap_agrees_with_the_value_modulo_2_to_the_w(self, datatypes):
        values = np.arange(-5000, 5000)
        assert np.array_equal(datatypes.wrap(values, W) % 256, values % 256)

    def test_saturate_clamps_to_the_rails(self, datatypes):
        assert int(datatypes.saturate(10000, W)) == 127
        assert int(datatypes.saturate(-10000, W)) == -128

    def test_saturate_is_identity_when_the_value_fits(self, datatypes):
        values = np.arange(-128, 128)
        assert np.array_equal(datatypes.saturate(values, W), values)

    def test_saturate_never_changes_the_sign(self, datatypes):
        values = np.arange(-40000, 40000, 13)
        out = datatypes.saturate(values, W)
        assert np.array_equal(np.sign(out), np.sign(values))


class TestIntProdModel:
    def test_overflow_is_exactly_when_trunc_differs(self, datatypes):
        """The defining property: overflow means the 8-bit answer is not the true one."""
        a, b = datatypes.int_prod_inputs(W)
        m = datatypes.int_prod_model(a, b, W)
        assert np.array_equal(m["overflow"] == 1, m["prod"] != m["trunc"])

    def test_hi_and_lo_reconstruct_the_product(self, datatypes):
        a, b = datatypes.int_prod_inputs(W)
        m = datatypes.int_prod_model(a, b, W)
        rebuilt = datatypes.wrap((m["hi"] << W) | m["lo"], 2 * W)
        assert np.array_equal(rebuilt, m["prod"])

    def test_hi_nonzero_disagrees_with_overflow_on_negatives(self, datatypes):
        """The naive unsigned test fires on every negative product; that is the lesson."""
        m = datatypes.int_prod_model([-1], [1], W)
        assert int(m["overflow"][0]) == 0
        assert int(m["hi_nonzero"][0]) == 1

    def test_sat_and_trunc_agree_exactly_when_there_is_no_overflow(self, datatypes):
        a, b = datatypes.int_prod_inputs(W)
        m = datatypes.int_prod_model(a, b, W)
        no_ovf = m["overflow"] == 0
        assert np.array_equal(m["sat"][no_ovf], m["trunc"][no_ovf])

    def test_sat_is_monotonic_in_the_true_product(self, datatypes):
        a, b = datatypes.int_prod_inputs(W)
        m = datatypes.int_prod_model(a, b, W)
        order = np.argsort(m["prod"], kind="stable")
        assert np.all(np.diff(m["sat"][order]) >= 0)

    @pytest.mark.parametrize("a,b,prod,trunc,sat,ovf,hi_nz", [
        (3, 5, 15, 15, 15, 0, 0),
        (100, 100, 10000, 16, 127, 1, 1),
        (-100, 100, -10000, -16, -128, 1, 1),
        (16, 16, 256, 0, 127, 1, 1),
        (20, 20, 400, -112, 127, 1, 1),
        (-1, 1, -1, -1, -1, 0, 1),
    ])
    def test_the_documented_teaching_vectors(self, datatypes, a, b, prod, trunc, sat, ovf, hi_nz):
        """These exact values appear in docs/demos/datatypes/int_prod.md."""
        m = datatypes.int_prod_model([a], [b], W)
        assert (int(m["prod"][0]), int(m["trunc"][0]), int(m["sat"][0]),
                int(m["overflow"][0]), int(m["hi_nonzero"][0])) == (prod, trunc, sat, ovf, hi_nz)

    def test_inputs_start_with_the_teaching_cases(self, datatypes):
        a, b = datatypes.int_prod_inputs(W)
        assert list(zip(a[:6].tolist(), b[:6].tolist())) == datatypes.INT_PROD_CASES

    def test_inputs_cover_the_whole_grid(self, datatypes):
        a, b = datatypes.int_prod_inputs(W)
        assert len(a) == len(datatypes.INT_PROD_CASES) + 256 * 256
        assert set(a.tolist()) == set(range(-128, 128))


# ---------------------------------------------------------------------------
# samp_pack
# ---------------------------------------------------------------------------

class TestPackUnpack:
    def test_round_trip_over_the_whole_field_range(self, datatypes):
        """unpack(pack(x)) == x — the property the testbench also checks."""
        rng = np.random.default_rng(0)
        lo, hi = -(1 << (DW - 1)), (1 << (DW - 1)) - 1
        for _ in range(2000):
            t = int(rng.integers(0, 1 << TW))
            re = int(rng.integers(lo, hi + 1))
            im = int(rng.integers(lo, hi + 1))
            assert datatypes.unpack_sample(datatypes.pack_sample(t, re, im)) == (t, re, im)

    @pytest.mark.parametrize("re", [-2048, 2047, 0, -1])
    @pytest.mark.parametrize("im", [-2048, 2047, 0, -1])
    def test_round_trip_on_the_edge_cases(self, datatypes, re, im):
        assert datatypes.unpack_sample(datatypes.pack_sample(7, re, im)) == (7, re, im)

    def test_packed_word_fits_in_32_bits(self, datatypes):
        word = datatypes.pack_sample(255, -2048, -2048)
        assert 0 <= word < (1 << 32)

    def test_fields_do_not_bleed_into_each_other(self, datatypes):
        """Without the masks, a negative real part would overwrite the timestamp."""
        for re in (-1, -2048, 2047):
            t, _, _ = datatypes.unpack_sample(datatypes.pack_sample(0xAB, re, -1))
            assert t == 0xAB

    def test_bad_unpack_differs_exactly_on_negative_reals(self, datatypes):
        rng = np.random.default_rng(1)
        lo, hi = -(1 << (DW - 1)), (1 << (DW - 1)) - 1
        for _ in range(500):
            re = int(rng.integers(lo, hi + 1))
            word = datatypes.pack_sample(3, re, 0)
            _, good, _ = datatypes.unpack_sample(word)
            bad = datatypes.unpack_sample_bad(word)
            assert (bad != good) == (re < 0)

    def test_bad_unpack_folds_negatives_upward(self, datatypes):
        word = datatypes.pack_sample(0, -1000, 0)
        assert datatypes.unpack_sample_bad(word) == 3096   # quoted in samp_pack.md


class TestGeneratedVectors:
    def test_generation_is_deterministic(self, datatypes, tmp_path):
        """A fixed seed is what keeps the committed figures from churning."""
        a, b = tmp_path / "a", tmp_path / "b"
        datatypes.gen_samp_pack_vectors(a)
        datatypes.gen_samp_pack_vectors(b)
        assert (a / "samp_pack_in.csv").read_bytes() == (b / "samp_pack_in.csv").read_bytes()
        assert (a / "samp_pack_golden.csv").read_bytes() == (b / "samp_pack_golden.csv").read_bytes()

    def test_edge_cases_are_present(self, datatypes, tmp_path):
        datatypes.gen_samp_pack_vectors(tmp_path)
        rows = (tmp_path / "samp_pack_in.csv").read_text(encoding="utf-8").splitlines()[1:]
        res = {int(r.split(",")[1]) for r in rows if r.strip()}
        assert {-2048, 2047, 0, -1} <= res

    def test_timestamp_is_a_counter_not_noise(self, datatypes, tmp_path):
        datatypes.gen_samp_pack_vectors(tmp_path)
        rows = [r for r in (tmp_path / "samp_pack_in.csv").read_text(
            encoding="utf-8").splitlines()[1:] if r.strip()]
        assert [int(r.split(",")[0]) for r in rows] == list(range(len(rows)))

    def test_int_prod_vectors_round_trip_through_the_file(self, datatypes, tmp_path):
        datatypes.gen_int_prod_vectors(tmp_path)
        text = (tmp_path / "int_prod_golden.csv").read_text(encoding="utf-8")
        header = text.splitlines()[0].split(",")
        assert header == ["a", "b", "prod", "hi", "lo", "trunc", "sat", "overflow", "hi_nonzero"]


class TestWriteIfDifferent:
    def test_copies_when_absent(self, datatypes, tmp_path):
        src, dst = tmp_path / "s.png", tmp_path / "out" / "d.png"
        src.write_bytes(b"image")
        assert datatypes.write_if_different(src, dst) is True
        assert dst.read_bytes() == b"image"

    def test_does_not_touch_an_identical_file(self, datatypes, tmp_path):
        """This is what keeps `git status` clean after a rebuild."""
        src, dst = tmp_path / "s.png", tmp_path / "d.png"
        src.write_bytes(b"image")
        dst.write_bytes(b"image")
        before = dst.stat().st_mtime_ns
        assert datatypes.write_if_different(src, dst) is False
        assert dst.stat().st_mtime_ns == before

    def test_copies_when_content_changed(self, datatypes, tmp_path):
        src, dst = tmp_path / "s.png", tmp_path / "d.png"
        src.write_bytes(b"new")
        dst.write_bytes(b"old")
        assert datatypes.write_if_different(src, dst) is True
        assert dst.read_bytes() == b"new"
