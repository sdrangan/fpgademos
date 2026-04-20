import argparse
import filecmp
import shutil
from pathlib import Path


DIRS_TO_COPY = ["build", "hw", "toolchain", "utils", "scripts"]
IGNORE_SUFFIXES = [".pyc", ".pyo", ".log", ".tmp", "~"]


def _should_ignore(path: Path) -> bool:
    return any(path.name.endswith(suffix) for suffix in IGNORE_SUFFIXES)


def _files_match(src_file: Path, dst_file: Path) -> bool:
    return filecmp.cmp(src_file, dst_file, shallow=False)


def _parse_bool_arg(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value

    normalized = value.strip().lower()
    if normalized in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off"}:
        return False

    raise argparse.ArgumentTypeError(f"Invalid boolean value: {value}")


def _copy_tree(
    src_dir: Path,
    dst_dir: Path,
    *,
    overwrite: bool,
    reset: bool,
) -> tuple[int, int, int]:
    copied = 0
    updated = 0
    skipped = 0

    for src_file in src_dir.rglob("*"):
        if not src_file.is_file():
            continue
        if _should_ignore(src_file):
            skipped += 1
            continue

        rel_path = src_file.relative_to(src_dir)
        dst_file = dst_dir / rel_path
        dst_file.parent.mkdir(parents=True, exist_ok=True)

        if not dst_file.exists():
            shutil.copy2(src_file, dst_file)
            copied += 1
            print(f"Copied {src_file} to {dst_file}")
            continue

        src_stat = src_file.stat()
        dst_stat = dst_file.stat()

        if reset:
            shutil.copy2(src_file, dst_file)
            updated += 1
            print(f"Reset copied {src_file} to {dst_file}")
            continue

        if _files_match(src_file, dst_file):
            print(f"Skipped {dst_file}, already up to date")
            skipped += 1
            continue

        if src_stat.st_mtime > dst_stat.st_mtime:
            shutil.copy2(src_file, dst_file)
            updated += 1
            print(f"Updated {dst_file} with newer {src_file}")
        elif overwrite:
            shutil.copy2(src_file, dst_file)
            updated += 1
            print(f"Updated {dst_file} with changed {src_file} despite non-newer timestamp")
        else:
            print(f"Warning: destination file has modifications; skipping {dst_file}")
            print(f"  Source: {src_file} (mtime={src_stat.st_mtime})")
            print(f"  Destination: {dst_file} (mtime={dst_stat.st_mtime})")
            skipped += 1

    return copied, updated, skipped


def main() -> None:
    """
    Copy mirrored pysilicon package files from a source repo into this repo.

    The hwdesign repo currently carries a temporary mirror of selected
    ``pysilicon`` package directories. This script syncs the mirrored package
    content from a source pysilicon repo into a destination hwdesign repo.

    For each directory in ``DIRS_TO_COPY``, the script verifies that both
    ``<src>/pysilicon/<dir>`` and ``<dst>/pysilicon/<dir>`` exist. It then walks
    the source tree recursively and:

                - copies files that are missing in the destination,
                - updates destination files when the source file is newer,
                - when ``--overwrite`` is true, updates destination files when contents
                    differ even if the source mtime is older or equal,
                - when ``--overwrite`` is false, warns and skips differing destination
                    files whose source is not newer,
                - when ``--reset`` is true, copies every source file regardless of status,
                - skips files whose destination is already up to date.

    At the end it prints a summary of copied, updated, and skipped files.

    Defaults
    --------
    ``--src`` defaults to the current working directory. If ``--dst`` is not
    provided, it defaults to ``src_root / .. / pysilicon``.

    Example
    -------
    python pysilicon_copy.py --src repos/pysilicon --dst repos/hwdesign
    """
    parser = argparse.ArgumentParser(
        description="Copy mirrored pysilicon package files from one repo into another."
    )
    parser.add_argument(
        "--src",
        default=".",
        help="Path to the source pysilicon repository root (default: current working directory).",
    )
    parser.add_argument(
        "--dst",
        help="Path to the destination hwdesign repository root (default: src_root/../pysilicon).",
    )
    parser.add_argument(
        "--overwrite",
        type=_parse_bool_arg,
        nargs="?",
        const=True,
        default=True,
        help="Overwrite differing destination files when source is not newer (default: true).",
    )
    parser.add_argument(
        "--reset",
        type=_parse_bool_arg,
        nargs="?",
        const=True,
        default=False,
        help="Copy all source files regardless of timestamps or contents (default: false).",
    )
    args = parser.parse_args()

    src_root = Path(args.src).expanduser().resolve()
    if args.dst is None:
        dst_root = (src_root.parent / "pysilicon").resolve()
    else:
        dst_root = Path(args.dst).expanduser().resolve()

    copied_total = 0
    updated_total = 0
    skipped_total = 0

    for dir_name in DIRS_TO_COPY:
        src_dir = src_root / "pysilicon" / dir_name
        dst_dir = dst_root / "pysilicon" / dir_name

        if not src_dir.exists():
            raise FileNotFoundError(
                f"Source directory does not exist: {src_dir}. Check --src."
            )

        if not dst_dir.exists():
            raise FileNotFoundError(
                f"Destination directory does not exist: {dst_dir}. Check --dst."
            )

        copied, updated, skipped = _copy_tree(
            src_dir=src_dir,
            dst_dir=dst_dir,
            overwrite=args.overwrite,
            reset=args.reset,
        )
        copied_total += copied
        updated_total += updated
        skipped_total += skipped

    print(
        f"Summary: copied={copied_total}, updated={updated_total}, skipped={skipped_total}"
    )


if __name__ == "__main__":
    main()