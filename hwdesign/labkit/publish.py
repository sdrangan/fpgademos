"""publish — derive a lab's public tree from its annotated solution.

Reads ``lab.toml`` in the solution lab directory, classifies every file, and
writes the student tree::

    hwdesign-soln/labs/prng/prng.sv     ->  hwdesign/labs/prng/partial/prng.sv
    hwdesign-soln/labs/prng/tb_prng.sv  ->  hwdesign/labs/prng/tb_prng.sv

``partial/`` is where the redacted files land because a student's work sits at the
top level, where ``git pull`` cannot reach it.

The guards below all fail the publish rather than warning.  This tool writes into
a public git repository, and a repository's history is not something an apology
can fix.
"""
from __future__ import annotations

import fnmatch
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from hwdesign.labkit.markers import MARKERS, MarkerError, is_supported, redact

__all__ = ["LabManifest", "PublishError", "PublishReport", "load_manifest", "publish"]

#: Build residue that no lab should have to enumerate.  Without this, the
#: unlisted-file-is-an-error rule is unusable: hwdesign-soln/labs/cubic holds
#: fourteen entries and most are artifacts.
DEFAULT_IGNORE = (
    "lab.toml", "sim/", "eval/", "vectors/", "submission/", "test_outputs/",
    "autograder_build/", "__pycache__/", ".pytest_cache/", "results/",
    "*.zip", "*.pyc", "*.wdb", "*.jou", "*.log", "*.pb",
    "submitted_results.json",
)

#: Below this length a dropped line is too common to be evidence of a leak
#: (``end``, ``);``, ``else begin``).  The stronger filter is *kept* lines, below.
_LEAK_MIN_LEN = 10


class PublishError(Exception):
    """A publish that must not proceed."""


@dataclass
class LabManifest:
    """The parsed ``lab.toml``."""

    name: str
    root: Path
    public: Path
    full: list[str] = field(default_factory=list)
    partial: list[str] = field(default_factory=list)
    private: list[str] = field(default_factory=list)
    ignore: list[str] = field(default_factory=list)
    allow_shared: list[str] = field(default_factory=list)

    @property
    def ignore_patterns(self) -> tuple[str, ...]:
        return tuple(DEFAULT_IGNORE) + tuple(self.ignore)


@dataclass
class PublishReport:
    """What a publish did, or would do under ``--dry-run``."""

    copied: list[Path] = field(default_factory=list)
    redacted: list[Path] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    blocks: int = 0
    dry_run: bool = False

    def summary(self) -> str:
        what = "would write" if self.dry_run else "wrote"
        return (f"{what} {len(self.copied)} file(s) whole, "
                f"{len(self.redacted)} redacted ({self.blocks} solution block(s)), "
                f"{len(self.skipped)} private")


def _load_toml(path: Path) -> dict[str, Any]:
    try:
        import tomllib
    except ModuleNotFoundError:  # Python 3.10
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ModuleNotFoundError:
            raise PublishError(
                "Reading lab.toml needs tomllib (Python 3.11+) or the tomli backport. "
                "Install tomli, or run this on 3.11+.") from None
    return tomllib.loads(path.read_text(encoding="utf-8"))


def load_manifest(lab_dir: Path | str) -> LabManifest:
    """Read and validate ``lab.toml`` from *lab_dir*."""
    lab_dir = Path(lab_dir).resolve()
    path = lab_dir / "lab.toml"
    if not path.exists():
        raise PublishError(f"No lab.toml in {lab_dir}.")

    data = _load_toml(path).get("lab")
    if not isinstance(data, dict):
        raise PublishError(f"{path}: expected a [lab] table.")
    for key in ("name", "public"):
        if key not in data:
            raise PublishError(f"{path}: [lab] is missing required key '{key}'.")

    public = Path(data["public"])
    public = (lab_dir / public).resolve() if not public.is_absolute() else public.resolve()

    # Guard 5: the two trees must be disjoint.  Publishing into the solution repo
    # (or out of a subdirectory of the public one) is always a mistake, and the
    # kind that is only obvious afterwards.
    if _is_relative(public, lab_dir) or _is_relative(lab_dir, public):
        raise PublishError(
            f"{path}: public path {public} overlaps the solution directory {lab_dir}. "
            f"The student tree must live in a different repository.")

    return LabManifest(
        name=str(data["name"]), root=lab_dir, public=public,
        full=[str(x) for x in data.get("full", [])],
        partial=[str(x) for x in data.get("partial", [])],
        private=[str(x) for x in data.get("private", [])],
        ignore=[str(x) for x in data.get("ignore", [])],
        allow_shared=[str(x).strip() for x in data.get("allow_shared", [])],
    )


def _is_relative(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _ignored(rel: str, patterns: tuple[str, ...]) -> bool:
    parts = rel.split("/")
    for pattern in patterns:
        if pattern.endswith("/"):
            if pattern.rstrip("/") in parts:
                return True
        elif fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(parts[-1], pattern):
            return True
    return False


def _classify(manifest: LabManifest) -> tuple[list[str], list[str]]:
    """Walk the lab directory and split it into (full, partial), or raise.

    Guard 1: a file in no list and matching no ignore pattern is an error.  Both
    silent defaults are bugs found late — not shipping means students cannot
    build, shipping whole means the answer key is public — so the only safe rule
    is to make the author decide.
    """
    listed = {p: kind for kind, names in
              (("full", manifest.full), ("partial", manifest.partial),
               ("private", manifest.private))
              for p in names}

    found: list[str] = []
    for path in sorted(manifest.root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(manifest.root).as_posix()
        if _ignored(rel, manifest.ignore_patterns):
            continue
        found.append(rel)

    unlisted = [r for r in found if r not in listed]
    if unlisted:
        raise PublishError(
            "These files are in no list in lab.toml and match no ignore pattern:\n  "
            + "\n  ".join(unlisted)
            + "\n\nAdd each to full, partial, private, or ignore. There is no default: "
              "guessing either way is a bug you find after students do.")

    missing = [p for p in listed if p not in found]
    if missing:
        raise PublishError(
            f"lab.toml lists file(s) that do not exist: {', '.join(sorted(missing))}")

    return ([r for r in found if listed[r] == "full"],
            [r for r in found if listed[r] == "partial"])


def publish(lab_dir: Path | str, *, dry_run: bool = False) -> PublishReport:
    """Derive the student tree for the lab in *lab_dir*.

    Returns a :class:`PublishReport`.  Raises :class:`PublishError` or
    :class:`~hwdesign.labkit.markers.MarkerError` rather than writing anything
    questionable.
    """
    manifest = load_manifest(lab_dir)
    full, partial = _classify(manifest)

    report = PublishReport(dry_run=dry_run,
                           skipped=sorted(manifest.private))
    outputs: dict[Path, str] = {}   # destination -> text (or None for a binary copy)
    binaries: dict[Path, Path] = {}
    all_dropped: list[str] = []
    all_kept: set[str] = set()

    # Files copied whole are scanned but contribute nothing to `all_kept`.  A
    # solution line appearing in a file shipped whole is the leak — treating it
    # as "not secret because it is also in a shipped file" would be circular, and
    # would defeat the guard in exactly the case it exists for: a file listed as
    # full that should have been partial.
    scan: dict[Path, str] = {}

    for rel in full:
        src = manifest.root / rel
        dest = manifest.public / rel
        binaries[dest] = src
        report.copied.append(dest)
        try:
            scan[dest] = _read(src)
        except UnicodeDecodeError:
            pass  # a genuinely binary asset; nothing to scan for

    for rel in partial:
        src = manifest.root / rel
        if not is_supported(src):
            raise MarkerError(
                f"{rel} is listed as partial but has no known comment syntax, so it "
                f"cannot be redacted. List it as full or private instead.")
        result = redact(_read(src), src)

        # Guard 6: a partial file with no markers means the author either meant
        # 'full' or forgot the annotations -- and forgetting them ships everything.
        if result.blocks == 0:
            raise PublishError(
                f"{rel} is listed as partial but contains no {MARKERS[0]} block. "
                f"Either annotate it or list it as full.")

        dest = manifest.public / "partial" / rel
        outputs[dest] = result.text
        scan[dest] = result.text
        report.redacted.append(dest)
        report.blocks += result.blocks
        all_dropped.extend(result.dropped)
        all_kept.update(result.kept)

    # Both guards run over the whole published tree, not just the redacted part.
    _check_no_markers(scan)
    _check_no_leak(scan, all_dropped, all_kept | set(manifest.allow_shared))

    if not dry_run:
        for dest, src in binaries.items():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)
        for dest, text in outputs.items():
            dest.parent.mkdir(parents=True, exist_ok=True)
            # newline="\n" so the output does not depend on the platform that ran it.
            with open(dest, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)

    return report


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _check_no_markers(published: dict[Path, str]) -> None:
    """Guard 3 — no marker token may survive into a published file.

    In a redacted file that means a labkit bug; in a file copied whole it means
    the manifest lists as ``full`` something that was written to be ``partial``.
    """
    for dest, text in published.items():
        for lineno, line in enumerate(text.split("\n"), start=1):
            for marker in MARKERS:
                if marker in line:
                    raise PublishError(
                        f"{dest}:{lineno} would ship containing '{marker}'. Either the "
                        f"file is annotated but listed as full, or this is a labkit "
                        f"bug — nothing was written.")


def _check_no_leak(published: dict[Path, str], dropped: list[str], kept: set[str]) -> None:
    """Guard 4 — no line from inside a SOLUTION block may appear in the output.

    The only check that catches a leak the author cannot see by reading the diff:
    a stray ``END SOLUTION``, a block closed one line early, a file listed as
    ``full`` that should have been ``partial``.

    Three filters keep it from crying wolf.  A dropped line that also appears
    *outside* any solution block was never secret — ``end``, ``);``, ``return z``
    — and short lines are structural noise.

    The third is ``allow_shared`` in ``lab.toml``, for the case the other two
    miss: library boilerplate that happens to be identical inside a solution
    block and in a file shipped whole.  ``fig, ax = plt.subplots(...)`` and
    ``plt.close(fig)`` are real examples from the ``prng`` lab.  Nothing about
    them reveals an answer, and nothing about them can be recognised as generic
    by a checker — so the author says so explicitly, once, in a place that is
    reviewed with the rest of the manifest.  That is preferable to loosening the
    rule for everyone, and far preferable to contorting the solution to dodge a
    false positive.
    """
    suspect = {d for d in dropped if len(d) >= _LEAK_MIN_LEN and d not in kept}
    if not suspect:
        return
    for dest, text in published.items():
        for lineno, line in enumerate(text.split("\n"), start=1):
            if line.strip() in suspect:
                raise PublishError(
                    f"{dest}:{lineno} contains a line from inside a {MARKERS[0]} "
                    f"block:\n    {line.strip()}\nNothing was written.")


def main(argv: list[str] | None = None) -> int:
    """``python -m hwdesign.labkit <command> <lab_dir>``."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m hwdesign.labkit",
        description="Derive a lab's public student tree from its annotated solution.")
    sub = parser.add_subparsers(dest="command", required=True)

    for name, help_text in (
            ("publish", "Write the student tree."),
            ("check", "Exit 1 if publishing would change anything (the CI gate)."),
            ("lint", "Verify the markers parse. Writes nothing.")):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("lab_dir", type=Path, help="The solution lab directory (holds lab.toml).")
        if name == "publish":
            p.add_argument("--dry-run", action="store_true",
                           help="Report what would be written, and write nothing.")

    args = parser.parse_args(argv)

    try:
        if args.command == "lint":
            report = publish(args.lab_dir, dry_run=True)
            print(f"{args.lab_dir}: markers OK — {report.summary()}")
            return 0

        if args.command == "check":
            report = publish(args.lab_dir, dry_run=True)
            stale = _stale(args.lab_dir)
            for path in stale:
                print(f"stale: {path}")
            if stale:
                print(f"{len(stale)} file(s) differ from the solution. Run publish.")
                return 1
            print(f"{args.lab_dir}: student tree is up to date ({report.summary()})")
            return 0

        report = publish(args.lab_dir, dry_run=args.dry_run)
        for path in report.copied:
            print(f"  full     {path}")
        for path in report.redacted:
            print(f"  partial  {path}")
        print(report.summary())
        return 0

    except (PublishError, MarkerError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _stale(lab_dir: Path | str) -> list[Path]:
    """Paths whose published content differs from what a publish would produce."""
    manifest = load_manifest(lab_dir)
    full, partial = _classify(manifest)
    stale: list[Path] = []

    for rel in full:
        dest = manifest.public / rel
        if not dest.exists() or dest.read_bytes() != (manifest.root / rel).read_bytes():
            stale.append(dest)
    for rel in partial:
        dest = manifest.public / "partial" / rel
        want = redact(_read(manifest.root / rel), manifest.root / rel).text
        if not dest.exists() or _read(dest) != want:
            stale.append(dest)
    return stale
