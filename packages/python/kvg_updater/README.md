# kvg-updater

Generic GitHub-Releases self-updater for PyInstaller-built desktop apps
(Tkinter, or any other GUI toolkit PyInstaller can bundle). Extracted from
KVGrainy's original `updater.py`.

## Install

Pin to a released `KVG_Standards` tag — never `@main`, see
[`../../../update-check-versioning.md`](../../../update-check-versioning.md):

```
kvg-updater @ git+https://github.com/gerp93/KVG_Standards.git@v0.3.0#subdirectory=packages/python/kvg_updater
```

## Usage

Write a thin app-specific wrapper (e.g. your own `updater.py`):

```python
from kvg_updater import check_for_update, download_update, apply_update_and_restart

try:
    from _version import __version__ as CURRENT_VERSION
except ImportError:
    CURRENT_VERSION = "0.0.0-dev"

GITHUB_REPO = "gerp93/KVGrainy"
APP_NAME = "KVGrainy"

def check():
    return check_for_update(GITHUB_REPO, APP_NAME, CURRENT_VERSION)
```

`check_for_update` only ever returns non-`None` for a packaged (frozen)
build with a real `CURRENT_VERSION` — it's a no-op running from source.

Asset naming assumes a release built via `release-python-gui.yml`
(`{app_name}-windows.exe` / `{app_name}-macos` / `{app_name}-linux`) — no
extra config needed if you're already using that workflow.

## Not yet verified for Flet apps

This module assumes a PyInstaller `--onefile` binary at `sys.executable`.
A `flet build` output has a different layout; confirm `sys.executable`
still resolves to the right path to replace before wiring this into a Flet
app (e.g. KVGenius) — don't assume it just works.
