"""Build a lab's Gradescope autograder zip.

Run from a lab directory:

    cd labs/prng
    build_lab_autograder

It writes ``autograder_build/`` -- the shared ``gradescope/`` template plus the
lab's own ``autograder_config.xml`` -- and zips it to ``autograder.zip``, which
is what gets uploaded under **Configure Autograder**.

This lived in ``waveflow.scripts`` until the pysilicon-to-waveflow migration
moved the general tooling upstream and left this behind by accident.  It is
course-specific in the way that matters: the thing it packages is
``<repo>/gradescope/autograde.py``, which reads this course's
``autograder_config.xml`` and copies this course's ``submitted_results.json``
through to Gradescope.  Nothing about it is reusable by another waveflow user.

The move also fixes what broke it.  The old version resolved the template as
``Path(__file__).parent.parent.parent / "gradescope"``, which pointed inside the
waveflow clone; when the template moved to this repository the command started
failing with a bare ``FileNotFoundError`` naming a path that no longer existed.
:func:`find_shared_dir` searches upward for a directory that actually holds the
template, so moving either tree again does not silently break the other -- and
``--shared`` is there for the case where the search is wrong.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


#: What ``gradescope/`` must contain to be the template. ``autograde.py`` alone
#: would match a lab's own build output, which is a copy rather than the source.
TEMPLATE_FILES = ("autograde.py", "run_autograder", "setup.sh", "requirements.txt")

#: How far up from this file to look for the repository's ``gradescope/``.
_SEARCH_DEPTH = 5


class BuildError(Exception):
    """Something the instructor can fix, reported without a traceback."""


def find_shared_dir(start: Path | None = None) -> Path:
    """The repository's ``gradescope/`` template directory.

    Searched for rather than computed from a fixed number of ``..`` steps: that
    is exactly the coupling that broke this command once already.
    """
    origin = (start or Path(__file__)).resolve()
    for parent in list(origin.parents)[:_SEARCH_DEPTH]:
        candidate = parent / "gradescope"
        if all((candidate / name).is_file() for name in TEMPLATE_FILES):
            return candidate

    raise BuildError(
        f"could not find the shared gradescope/ template above {origin}. "
        f"It must be a directory named 'gradescope' holding {', '.join(TEMPLATE_FILES)}. "
        "Pass --shared to point at it explicitly."
    )


def load_config(config_path: Path) -> list[str]:
    """The required-file names from ``autograder_config.xml``.

    Parsed rather than merely copied.  A malformed config used to travel all
    the way to Gradescope and fail there, in a container whose only feedback is
    a zero for whoever submitted first.
    """
    if not config_path.is_file():
        raise BuildError(
            f"{config_path} does not exist. A lab autograder needs an "
            "autograder_config.xml listing the files a submission must contain; "
            "see an existing lab for the shape."
        )

    try:
        root = ET.parse(config_path).getroot()
    except ET.ParseError as exc:
        raise BuildError(f"{config_path}: failed to parse XML: {exc}") from exc

    if root.tag != "autograder":
        raise BuildError(
            f"{config_path}: root element must be <autograder>, found <{root.tag}>."
        )

    required = [
        (element.text or "").strip() for element in root.findall("./required_files/file")
    ]
    if not required or not all(required):
        raise BuildError(
            f"{config_path}: no <required_files><file> entries. The list is the only "
            "check the autograder performs, so an empty one accepts any upload."
        )

    # The names are matched against a flat submission directory: GradeReportStep
    # zips its bundle with `arcname=Path(rel).name`, so a config entry carrying a
    # directory can never match what the student actually uploads.
    with_dirs = [name for name in required if "/" in name or "\\" in name]
    if with_dirs:
        raise BuildError(
            f"{config_path}: {', '.join(with_dirs)} contain a directory, but a "
            "submission zip is flat -- list the base name only."
        )

    return required


def build(lab_dir: Path, config_path: Path, shared: Path) -> tuple[Path, list[str]]:
    """Write ``autograder_build/`` and ``autograder.zip``. Returns (zip, required)."""
    required = load_config(config_path)

    build_dir = lab_dir / "autograder_build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir()

    for name in TEMPLATE_FILES:
        shutil.copy(shared / name, build_dir / name)
    shutil.copy(config_path, build_dir / "autograder_config.xml")

    zip_path = Path(shutil.make_archive(str(lab_dir / "autograder"), "zip", build_dir))
    return zip_path, required


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="build_lab_autograder",
        description="Build a lab's Gradescope autograder zip from the shared template.",
    )
    parser.add_argument(
        "--config", default="autograder_config.xml", metavar="PATH",
        help="The lab's autograder config (default: autograder_config.xml in this directory).",
    )
    parser.add_argument(
        "--shared", default=None, metavar="DIR",
        help="The gradescope/ template directory. Found automatically by default.",
    )
    args = parser.parse_args(argv)

    lab_dir = Path.cwd()
    try:
        shared = Path(args.shared).resolve() if args.shared else find_shared_dir()
        if args.shared:
            missing = [name for name in TEMPLATE_FILES if not (shared / name).is_file()]
            if missing:
                raise BuildError(f"{shared}: template is missing {', '.join(missing)}.")
        zip_path, required = build(lab_dir, lab_dir / args.config, shared)
    except BuildError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"template: {shared}")
    print(f"created:  {zip_path}")
    print(f"a submission must contain {len(required)} file(s): {', '.join(required)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
