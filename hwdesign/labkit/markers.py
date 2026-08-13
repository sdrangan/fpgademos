"""markers — turn an annotated solution file into the student's version.

The grammar is one marker pair around the code to drop::

        // TODO:  Compute the following intermediate values
        // x2_s1_next = ...  x squared term
    // BEGIN SOLUTION
        x2_s1_next = sat( (x_s0 * x_s0) >>> FBITS );
    // END SOLUTION

The TODO comment sits *outside* the block, because a comment is harmless in both
versions.  That is the whole reason this stays small: the existing solutions
already write their TODO text inline above the code it stands for, so nothing has
to express "text for the student" — only "code to drop".

Two optional sections cover what the *solution* must not contain:

``BEGIN TODO``
    Lines emitted verbatim into the student file.  Needed only when the text
    would be wrong in the solution (``// y is not driven yet``).

``BEGIN STUB``
    Lines written commented in the solution and emitted *un*commented.  Rare, but
    not dispensable: a Python function whose entire body sits inside a SOLUTION
    block leaves ``def f():`` followed by nothing, which will not parse.

The annotated file is the solution — it compiles and runs as it stands, with no
generation step.  Only the student version is derived.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

__all__ = [
    "MarkerError", "Redaction", "comment_syntax", "is_supported", "redact",
    "BEGIN_SOLUTION", "BEGIN_TODO", "BEGIN_STUB", "END_SOLUTION", "MARKERS",
]

BEGIN_SOLUTION = "BEGIN SOLUTION"
BEGIN_TODO = "BEGIN TODO"
BEGIN_STUB = "BEGIN STUB"
END_SOLUTION = "END SOLUTION"

#: Every marker token, for the "did one survive into the output?" guard.
MARKERS = (BEGIN_SOLUTION, BEGIN_TODO, BEGIN_STUB, END_SOLUTION)

#: Extension → (line-comment opener, optional closer).
_SYNTAX: dict[str, tuple[str, str]] = {
    **{ext: ("//", "") for ext in
       (".sv", ".svh", ".v", ".vh", ".c", ".h", ".cpp", ".hpp", ".cc", ".tpp")},
    **{ext: ("#", "") for ext in
       (".py", ".tcl", ".sh", ".toml", ".cfg", ".yml", ".yaml")},
    ".md": ("<!--", "-->"),
}


class MarkerError(Exception):
    """A malformed annotation.  Always fatal — a half-read marker could leak."""


@dataclass
class Redaction:
    """The result of redacting one file."""

    text: str
    #: Non-blank lines removed, stripped.  The publish guard checks these against
    #: everything it is about to write.
    dropped: list[str] = field(default_factory=list)
    #: Non-blank lines that survived, stripped — the "this was never secret" set
    #: that keeps the leak guard from firing on ``end`` or ``);``.
    kept: list[str] = field(default_factory=list)
    blocks: int = 0


def comment_syntax(path: Path | str) -> tuple[str, str]:
    """Return the ``(open, close)`` comment delimiters for *path*'s extension."""
    ext = Path(path).suffix.lower()
    if ext not in _SYNTAX:
        raise MarkerError(
            f"No comment syntax known for '{ext}' ({path}). Add it to markers._SYNTAX "
            f"rather than guessing — redacting with the wrong prefix silently ships "
            f"the solution.")
    return _SYNTAX[ext]


def is_supported(path: Path | str) -> bool:
    return Path(path).suffix.lower() in _SYNTAX


def _marker_of(line: str, opener: str, closer: str) -> str | None:
    """Return the marker token on *line*, or ``None`` if it is not a marker line.

    A marker must be the entire comment: ``// BEGIN SOLUTION`` is one,
    ``x = 1; // BEGIN SOLUTION here`` is not.  Anything looser and a line of
    prose mentioning a marker would silently change what ships.
    """
    stripped = line.strip()
    if not stripped.startswith(opener):
        return None
    body = stripped[len(opener):]
    if closer and body.endswith(closer):
        body = body[: -len(closer)]
    body = body.strip()
    return body if body in MARKERS else None


def _uncomment(line: str, opener: str, closer: str) -> str:
    """Strip one comment prefix from a STUB line, preserving its indentation.

    ``    # return 0`` → ``    return 0``.  Exactly one following space is
    consumed, so the author controls the resulting indentation directly.
    """
    indent_len = len(line) - len(line.lstrip())
    indent, rest = line[:indent_len], line[indent_len:]
    if not rest.startswith(opener):
        raise MarkerError(
            f"STUB line is not a comment, so it would appear in the solution too: {line!r}")
    rest = rest[len(opener):]
    if rest.startswith(" "):
        rest = rest[1:]
    if closer:
        rest = rest.rstrip()
        if rest.endswith(closer):
            rest = rest[: -len(closer)].rstrip()
    return indent + rest


def redact(text: str, path: Path | str) -> Redaction:
    """Produce the student version of *text*, annotated for *path*'s language.

    Raises :class:`MarkerError` on anything malformed — unbalanced, nested, or
    out-of-order markers.  There is no recovery mode on purpose: a marker the
    parser guesses at is a marker that might not remove what it was meant to.
    """
    opener, closer = comment_syntax(path)
    out: list[str] = []
    dropped: list[str] = []
    kept: list[str] = []
    blocks = 0
    state = "out"  # out | solution | todo | stub

    def fail(lineno: int, message: str) -> None:
        raise MarkerError(f"{path}:{lineno}: {message}")

    for lineno, line in enumerate(text.split("\n"), start=1):
        marker = _marker_of(line, opener, closer)

        if marker is None:
            if state == "solution":
                if line.strip():
                    dropped.append(line.strip())
                continue

            if state == "stub":
                line = _uncomment(line, opener, closer)
            out.append(line)

            # Everything that survives counts as "not secret", including the
            # TODO and STUB sections.  Those are content the author wrote *for*
            # the student file, so by construction they cannot be a leak — and a
            # STUB is often a cut-down version of the solution it replaces, so
            # its lines collide with dropped ones routinely.  `return out_path`
            # in the prng lab is exactly that: the last line of the solution and
            # the whole of the stub.
            if line.strip():
                kept.append(line.strip())
            continue

        if marker == BEGIN_SOLUTION:
            if state != "out":
                fail(lineno, f"{BEGIN_SOLUTION} inside an open block — markers do not nest.")
            state, blocks = "solution", blocks + 1
        elif marker == BEGIN_TODO:
            if state != "solution":
                fail(lineno, f"{BEGIN_TODO} must follow {BEGIN_SOLUTION} directly.")
            state = "todo"
        elif marker == BEGIN_STUB:
            if state not in ("solution", "todo"):
                fail(lineno, f"{BEGIN_STUB} must appear inside a {BEGIN_SOLUTION} block.")
            state = "stub"
        else:  # END_SOLUTION
            if state == "out":
                fail(lineno, f"{END_SOLUTION} with no {BEGIN_SOLUTION} open.")
            state = "out"

    if state != "out":
        raise MarkerError(
            f"{path}: reached end of file with a {BEGIN_SOLUTION} block still open.")

    return Redaction(text="\n".join(out), dropped=dropped, kept=kept, blocks=blocks)
