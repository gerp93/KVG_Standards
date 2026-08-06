"""User-configurable SQLite file location for Python desktop apps.

Mirrors Sweeper's src/main/dbLocation.ts (Electron) so Python apps that
store their own data in SQLite get the same behavior: a default location
under the app's own data directory, an optional override the user can
point elsewhere (for backup/syncing a folder outside the app's own files),
and a copy-on-relocate so moving the file never loses data.

This package only manages the path/config bookkeeping — it doesn't open
the database or restart the app. Callers are responsible for:
- Opening their sqlite3 connection at get_effective_db_path().
- After set_db_path()/reset_to_default_db_path(), closing that connection
  and restarting the process (the on-disk path an already-open sqlite3
  connection is using can't be swapped out from under it) — see this
  package's README for the restart pattern.

Usage:

    from pathlib import Path
    from kvg_dblocation import DbLocation

    # data_dir: wherever this app already keeps its own per-user data
    # (KVGenius: core.CACHE_DIR's parent; don't invent a second convention).
    db_location = DbLocation(data_dir=Path(CACHE_DIR).parent, default_filename="kvgenius.db")

    conn = sqlite3.connect(str(db_location.get_effective_db_path()))
    ...
    db_location.set_db_path(Path("/path/to/backup-synced-folder/kvgenius.db"))
    # then close conn and restart the process
"""
import json
import shutil
from pathlib import Path
from typing import Optional


class DbLocation:
    """Manages one SQLite file's location: a default path under `data_dir`,
    optionally overridden via a small JSON config stored alongside it."""

    def __init__(self, data_dir: Path, default_filename: str, config_filename: str = "db_location.json"):
        self.data_dir = Path(data_dir)
        self.default_filename = default_filename
        self.config_path = self.data_dir / config_filename

    def get_default_db_path(self) -> Path:
        return self.data_dir / self.default_filename

    def _read_config(self) -> dict:
        if not self.config_path.exists():
            return {}
        try:
            return json.loads(self.config_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _write_config(self, config: dict) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    def get_effective_db_path(self) -> Path:
        """The database file this app should actually open: a user-chosen
        location, or the default."""
        configured: Optional[str] = self._read_config().get("db_path")
        return Path(configured) if configured else self.get_default_db_path()

    def is_using_default_location(self) -> bool:
        return "db_path" not in self._read_config()

    def set_db_path(self, new_path: Path) -> None:
        """Point the app at a different SQLite file. If nothing exists yet
        at the new location, the current database is copied there first so
        no data is lost. If a file already exists there, it's left alone
        and simply adopted as-is.

        Close any open connection to the current database before calling
        this — copying a file that's still open for writes can produce a
        corrupt or incomplete copy.
        """
        new_path = Path(new_path)
        current_path = self.get_effective_db_path()

        if not new_path.exists() and current_path.exists():
            new_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(current_path, new_path)

        config = self._read_config()
        config["db_path"] = str(new_path)
        self._write_config(config)

    def reset_to_default_db_path(self) -> None:
        config = self._read_config()
        config.pop("db_path", None)
        self._write_config(config)
