"""Regenerate the waveflow API snapshot at ``plans/waveflow_api.md``.

Introspects the *installed* waveflow package (see ``requirements-dev.txt``) and
emits a Markdown listing of every public module, class, and function, with
one-line docstring summaries. Only names *defined* in a module are listed, so
re-exports do not appear twice.

Run with the hwdesign venv Python, from the repo root::

    ..\\hwdesign-venv\\Scripts\\python.exe plans/introspect_waveflow.py api_body.md

With no argument it writes to stdout. Output is always UTF-8 (the listing
contains ``->`` arrows and other non-cp1252 characters, so a bare
``> file`` redirect on Windows would fail).

The migration-relevant commentary at the top of ``waveflow_api.md`` is written
by hand; this script emits only the body below the ``---`` separator.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil
import sys

import waveflow

# Subpackages whose contents are not worth listing: large generated corpora and
# vendored data that would swamp the useful API surface.
SKIP_PREFIXES = ("waveflow.mcp.corpus", "waveflow.mcp.resources")


def first_line(obj) -> str:
    """Return the first non-empty line of an object's docstring, or ''."""
    doc = inspect.getdoc(obj) or ""
    for line in doc.splitlines():
        if line.strip():
            return line.strip()
    return ""


def public_methods(cls) -> list[str]:
    """Public methods defined on cls itself (not inherited from object/base)."""
    names = []
    for name, member in vars(cls).items():
        if name.startswith("_"):
            continue
        if inspect.isfunction(member) or isinstance(member, (classmethod, staticmethod, property)):
            names.append(name)
    return sorted(names)


def signature_of(fn) -> str:
    try:
        return str(inspect.signature(fn))
    except (ValueError, TypeError):
        return "(...)"


def emit_module(modname: str, out) -> None:
    try:
        mod = importlib.import_module(modname)
    except Exception as exc:  # noqa: BLE001 - report, don't abort the sweep
        print(f"### `{modname}` — ⚠️ import failed: {type(exc).__name__}: {exc}\n", file=out)
        return

    classes, functions = [], []
    for name, obj in vars(mod).items():
        if name.startswith("_"):
            continue
        if getattr(obj, "__module__", None) != modname:
            continue  # imported here, defined elsewhere — list it at its source
        if inspect.isclass(obj):
            classes.append((name, obj))
        elif inspect.isfunction(obj):
            functions.append((name, obj))

    if not classes and not functions:
        return

    header = f"### `{modname}`"
    doc = first_line(mod)
    if doc:
        header += f" — {doc}"
    print(header + "\n", file=out)

    if classes:
        print("**Classes:**", file=out)
        for name, cls in sorted(classes):
            line = f"- `{name}`"
            doc = first_line(cls)
            if doc:
                line += f" — {doc}"
            methods = public_methods(cls)
            if methods:
                line += f"  _(methods: {', '.join(methods)})_"
            print(line, file=out)
        print(file=out)

    if functions:
        print("**Functions:**", file=out)
        for name, fn in sorted(functions):
            line = f"- `{name}{signature_of(fn)}`"
            doc = first_line(fn)
            if doc:
                line += f" — {doc}"
            print(line, file=out)
        print(file=out)


def write_listing(out) -> None:
    pkg_dir = waveflow.__path__[0]
    print(f"waveflow package dir: `{pkg_dir}`\n", file=out)

    print("## Top-level `waveflow` namespace\n", file=out)
    all_names = getattr(waveflow, "__all__", None)
    print(
        f"_(`__all__` = {all_names})_\n" if all_names else "_(no `__all__` defined)_\n",
        file=out,
    )
    print("Public names re-exported at `waveflow.*`:", file=out)
    for name in sorted(n for n in vars(waveflow) if not n.startswith("_")):
        obj = getattr(waveflow, name)
        kind = "module" if inspect.ismodule(obj) else type(obj).__name__
        print(f"- `{name}` ({kind}) — {first_line(obj)}", file=out)
    print(file=out)

    emit_module("waveflow", out)
    for _, modname, _ in sorted(
        pkgutil.walk_packages(waveflow.__path__, prefix="waveflow."),
        key=lambda t: t[1],
    ):
        if modname.startswith(SKIP_PREFIXES):
            continue
        emit_module(modname, out)


def main() -> None:
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w", encoding="utf-8") as out:
            write_listing(out)
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        write_listing(sys.stdout)


if __name__ == "__main__":
    main()
