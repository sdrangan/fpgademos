"""hwdesign — course-specific helpers for the Introduction to Hardware Design course.

This is a thin layer built *on top of* the external ``waveflow`` package. It holds
only material that is specific to this course (lab/assignment autograders,
gradescope glue, shared demo/lab scaffolding). General-purpose hardware-design
functionality lives in ``waveflow`` and is imported from there directly.

Design rule (so this does not regrow into a parallel general-purpose package, the
way pysilicon once did): if a helper would be useful to any waveflow user, push it
upstream into waveflow; keep here only what makes sense *because of this course*.

During development, ``waveflow`` is installed editable from the local clone at
``../pysilicon`` (the waveflow repo); see ``requirements-dev.txt``.
"""

__version__ = "0.1.0"
