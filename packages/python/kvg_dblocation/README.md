# kvg-dblocation

A user-configurable SQLite file location for Python desktop apps: a
default path under the app's own data directory, plus an optional
override the user can point at a different folder (for backup or syncing
a database file outside the app's install/data location). Mirrors
Sweeper's `src/main/dbLocation.ts` (Electron) — same default/effective/
set/reset shape, same copy-on-relocate behavior.

## Install

Pin to a released `KVG_Standards` tag — see
[`../../../db-location-versioning.md`](../../../db-location-versioning.md)
for the current interim `@main` exception (no tag exists yet):

```
kvg-dblocation @ git+https://github.com/gerp93/KVG_Standards.git@main#subdirectory=packages/python/kvg_dblocation
```

## Usage

```python
import sqlite3
from pathlib import Path
from kvg_dblocation import DbLocation

# data_dir should be wherever this app already keeps its per-user data —
# reuse an existing convention (e.g. KVGenius's core.CACHE_DIR's parent)
# rather than inventing a second one.
db_location = DbLocation(data_dir=Path(CACHE_DIR).parent, default_filename="kvgenius.db")

conn = sqlite3.connect(str(db_location.get_effective_db_path()))
```

Settings UI wiring (three actions, same as Sweeper's "Database Location"
section):

```python
def choose_existing_file(new_path: Path):
    """User picked an existing .db file via an open-file dialog."""
    conn.close()
    db_location.set_db_path(new_path)
    restart_app()

def choose_new_location(new_path: Path):
    """User picked a not-yet-existing path via a save-file dialog —
    set_db_path copies the current database there."""
    conn.close()
    db_location.set_db_path(new_path)
    restart_app()

def reset_to_default():
    conn.close()
    db_location.reset_to_default_db_path()
    restart_app()
```

**Always close the sqlite3 connection before calling `set_db_path`/
`reset_to_default_db_path`** — copying a file that's still open for writes
can produce a corrupt or incomplete copy, same caveat as Sweeper's
`main.ts` (`saveDatabase(db)` before `setDbPath`).

## Restarting after a location change

The app must restart after moving the database — an already-open sqlite3
connection can't be pointed at a new file path. Sweeper does this with
Electron's `app.relaunch()` + `app.exit()`. For a plain Python process,
re-exec after cleanup:

```python
import os
import sys

def restart_app():
    os.execv(sys.executable, [sys.executable] + sys.argv)
```

On Windows, if the app is a PyInstaller/Flet-built executable rather than
a `python` interpreter invocation, `sys.executable` is the built binary
itself, so this still works the same way. This hasn't been exercised
against a real Flet-built KVGenius binary yet — verify before relying on
it silently (same caveat class as `kvg_updater`'s bundle mode).

## What this package does not do

- Doesn't open the database connection itself — that stays app-specific
  (different apps may use `sqlite3` directly, an ORM, etc.).
- Doesn't restart the process — see above; that's a couple of lines the
  app owns, since the right restart mechanism can depend on how the app
  was launched.
- Doesn't validate that the chosen path is actually a valid SQLite file —
  if the user points it at garbage, that surfaces as a normal
  `sqlite3.DatabaseError` when the app tries to open it, same as it would
  without this package.
