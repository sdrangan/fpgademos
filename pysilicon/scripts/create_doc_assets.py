"""
create_doc_assets.py - Incremental doc asset (figure) generator for pysilicon.

Regenerates auto-generated documentation figures only when they are missing or
when a source dependency is newer than the oldest existing output.

Usage examples
--------------
Regenerate all registered doc sets (incremental)::

    create-doc-assets --docs all

Regenerate timing figures only::

    create-doc-assets --docs timing

Check whether figures are up-to-date without writing anything::

    create-doc-assets --docs all --status

Force-regenerate even if already up-to-date::

    create-doc-assets --docs timing --force

List available doc sets::

    create-doc-assets --list

Multiple doc sets (comma-separated)::

    create-doc-assets --docs timing,schema
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Callable

# ---------------------------------------------------------------------------
# Repository root (pysilicon/scripts/ lives two levels below the root)
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# DocSet definition
# ---------------------------------------------------------------------------

class DocSet:
    """Describes a single doc-figure set and knows how to build itself."""

    def __init__(
        self,
        name: str,
        dependencies: list[Path],
        output_files: list[Path],
        generator: Callable[[Path], list[Path]],
        output_dir: Path,
    ) -> None:
        """
        Parameters
        ----------
        name:
            Identifier for this doc set (e.g. ``"timing"``).
        dependencies:
            File paths whose modification time is checked to detect staleness.
        output_files:
            Expected output files.  If any are absent the set is considered stale.
        generator:
            Callable ``(output_dir: Path) -> list[Path]`` that produces the
            output files when called.
        output_dir:
            Directory passed to *generator*.
        """
        self.name = name
        self.dependencies = dependencies
        self.output_files = output_files
        self.generator = generator
        self.output_dir = output_dir

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------

    def missing_outputs(self) -> list[Path]:
        """Return output files that do not exist on disk."""
        return [p for p in self.output_files if not p.exists()]

    def newest_dep_mtime(self) -> float | None:
        """Return the highest mtime among existing dependencies (or None)."""
        mtimes = [p.stat().st_mtime for p in self.dependencies if p.exists()]
        return max(mtimes) if mtimes else None

    def oldest_output_mtime(self) -> float | None:
        """Return the lowest mtime among existing outputs (or None if any missing)."""
        if self.missing_outputs():
            return None
        mtimes = [p.stat().st_mtime for p in self.output_files]
        return min(mtimes) if mtimes else None

    def is_stale(self) -> bool:
        """Return True if any output is missing or a dep is newer than an output."""
        if self.missing_outputs():
            return True
        oldest_out = self.oldest_output_mtime()
        newest_dep = self.newest_dep_mtime()
        if oldest_out is None or newest_dep is None:
            return True
        return newest_dep > oldest_out

    def status_lines(self) -> list[str]:
        """Return human-readable status lines for this doc set."""
        lines: list[str] = []
        missing = self.missing_outputs()
        if missing:
            lines.append(f"  [missing] {len(missing)} output(s) not found:")
            for p in missing:
                lines.append(f"    - {p.relative_to(_REPO_ROOT)}")
        elif self.is_stale():
            lines.append("  [stale]   dependency newer than oldest output")
        else:
            lines.append("  [ok]      up-to-date")
        return lines

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self) -> list[Path]:
        """Run the generator and return list of written paths."""
        return self.generator(self.output_dir)


# ---------------------------------------------------------------------------
# Registry builder
# ---------------------------------------------------------------------------

def _load_timing_generator() -> Callable[[Path], list[Path]]:
    """Dynamically import save_timing_figures from the example script."""
    example_path = _REPO_ROOT / "examples" / "timing" / "basic_timing_diagram.py"
    spec = importlib.util.spec_from_file_location("basic_timing_diagram", example_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {example_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod.save_timing_figures  # type: ignore[attr-defined]


def _build_registry() -> dict[str, DocSet]:
    """Return the complete registry of doc sets keyed by name."""
    timing_output_dir = _REPO_ROOT / "docs" / "guide" / "_static" / "timing"
    timing_deps = [
        _REPO_ROOT / "examples" / "timing" / "basic_timing_diagram.py",
        _REPO_ROOT / "pysilicon" / "utils" / "timing.py",
    ]
    timing_outputs = [
        timing_output_dir / "basic_timing_diagram.png",
    ]

    registry: dict[str, DocSet] = {
        "timing": DocSet(
            name="timing",
            dependencies=timing_deps,
            output_files=timing_outputs,
            generator=_load_timing_generator(),
            output_dir=timing_output_dir,
        ),
    }
    return registry


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def run(
    doc_names: list[str],
    *,
    status_only: bool = False,
    force: bool = False,
) -> int:
    """
    Process the requested doc sets.

    Parameters
    ----------
    doc_names:
        Names of the doc sets to process (already expanded from 'all').
    status_only:
        If True, only print status information; do not regenerate files.
    force:
        If True, regenerate even if already up-to-date.

    Returns
    -------
    int
        Exit code (always 0 – status is informational).
    """
    registry = _build_registry()

    for name in doc_names:
        if name not in registry:
            print(f"[create-doc-assets] Unknown doc set: {name!r} (use --list to see available sets)")
            continue

        doc = registry[name]

        if status_only:
            stale_label = "STALE" if doc.is_stale() else "OK"
            print(f"{name}: {stale_label}")
            for line in doc.status_lines():
                print(line)
            continue

        if not force and not doc.is_stale():
            print(f"{name}: up-to-date (skip).  Use --force to rebuild.")
            continue

        reason = "forced" if force else ("missing output(s)" if doc.missing_outputs() else "stale")
        print(f"{name}: regenerating ({reason}) ...")
        written = doc.build()
        for p in written:
            print(f"  wrote: {Path(p).relative_to(_REPO_ROOT)}")

    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="create-doc-assets",
        description="Incrementally regenerate auto-generated documentation figures.",
    )
    parser.add_argument(
        "--docs",
        metavar="NAMES",
        default="all",
        help=(
            "Comma-separated list of doc sets to process, or 'all'. "
            "Example: --docs timing  or  --docs timing,schema"
        ),
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print whether each doc set is up-to-date; do not modify files.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if outputs are already up-to-date.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print available doc sets and exit.",
    )

    args = parser.parse_args(argv)

    registry = _build_registry()

    if args.list:
        print("Available doc sets:")
        for name in registry:
            print(f"  {name}")
        return 0

    if args.docs.strip().lower() == "all":
        doc_names = list(registry.keys())
    else:
        doc_names = [n.strip() for n in args.docs.split(",") if n.strip()]

    return run(doc_names, status_only=args.status, force=args.force)


if __name__ == "__main__":
    sys.exit(main())
