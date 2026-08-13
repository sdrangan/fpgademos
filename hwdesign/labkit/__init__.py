"""labkit — publish a lab's public student tree from its annotated solution.

Instructor-side. The solution repository is private and is the source; the public
tree under ``hwdesign/labs/<lab>`` is a build output.  See ``plans/labkit.md``.

    python -m hwdesign.labkit lint    labs/prng
    python -m hwdesign.labkit publish labs/prng --dry-run
    python -m hwdesign.labkit publish labs/prng

The student-side counterpart is ``StudentSourceStep`` in
:mod:`hwdesign.grading`, which copies a file up out of ``partial/`` the first
time a lab is built.
"""
from hwdesign.labkit.markers import MarkerError, Redaction, redact
from hwdesign.labkit.publish import (
    LabManifest, PublishError, PublishReport, load_manifest, publish,
)

__all__ = [
    "MarkerError", "Redaction", "redact",
    "LabManifest", "PublishError", "PublishReport", "load_manifest", "publish",
]
