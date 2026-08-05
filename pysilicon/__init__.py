"""Tombstone for the vendored ``pysilicon`` package — it has been removed.

This directory used to hold a manually-copied snapshot of the external
``pysilicon`` package. That package was renamed to **waveflow** and has evolved
well beyond the snapshot, so the vendored copy was deleted during the waveflow
migration (see ``plans/migration.md``).

This stub exists only so that not-yet-migrated course material fails with a
useful message instead of a bare ``ModuleNotFoundError``. Delete this whole
directory once every unit in ``plans/migration_tracker.md`` is `integrated` or
`deferred`.
"""

raise ModuleNotFoundError(
    "The vendored 'pysilicon' package has been removed - this course material "
    "has not been migrated to waveflow yet.\n"
    "\n"
    "  * Install waveflow:  pip install -r requirements-dev.txt\n"
    "  * Import from it directly, e.g. 'from waveflow.hw.dataschema import ...'\n"
    "    (module map: plans/waveflow_api.md; per-file status: "
    "plans/migration_tracker.md)\n"
    "  * The old vendored source is still in git history:\n"
    "        git show pre-waveflow-migration:pysilicon/<path>\n"
)
