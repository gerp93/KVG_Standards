# kvg-updater

Generic GitHub-Releases self-updater for Python desktop apps. Two modes:

- **Single-file mode** — PyInstaller `--onefile` builds (Tkinter, or any
  other GUI toolkit PyInstaller can bundle). Extracted from KVGrainy's
  original `updater.py`.
- **Bundle mode** — Flet apps, whose `flet build` output is a directory
  (Flutter-engine binary plus supporting files), not a single executable.

## Install

Pin to a released `KVG_Standards` tag — never `@main`, see
[`../../../update-check-versioning.md`](../../../update-check-versioning.md):

```
kvg-updater @ git+https://github.com/gerp93/KVG_Standards.git@v0.3.0#subdirectory=packages/python/kvg_updater
```

## Usage — single-file mode (PyInstaller)

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

## Usage — bundle mode (Flet)

```python
from pathlib import Path
from kvg_updater import (
    check_for_bundle_update, download_and_extract_bundle,
    apply_bundle_update_and_restart,
)

GITHUB_REPO = "gerp93/KVGenius"
APP_NAME = "KVGenius"
# The directory the running build lives in — one level above the
# executable found inside it. Verify this matches your `flet build`
# output layout; it can differ by Flet version and platform.
APP_DIR = Path(sys.executable).resolve().parent

def check_and_apply(current_version: str):
    info = check_for_bundle_update(GITHUB_REPO, APP_NAME, current_version)
    if not info:
        return False
    staged = download_and_extract_bundle(info["download_url"], APP_NAME)
    apply_bundle_update_and_restart(staged, APP_DIR, APP_NAME)  # never returns
    return True
```

Asset naming assumes a release built via `release-flet.yml`
(`{app_name}-{tag}-windows.zip` / `{app_name}-{tag}-macos.tar.gz` /
`{app_name}-{tag}-linux.tar.gz`, tag keeping its `v` prefix). Instead of
replacing a single file, `apply_bundle_update_and_restart` swaps the whole
build directory: the current `app_dir` is renamed aside, the freshly
extracted build moved into place, the old copy deleted, then the binary
inside the new build (`_find_bundle_binary`) is relaunched.

**Verified so far:** archive download/extraction and the directory swap
itself were smoke-tested against a synthetic tar.gz and a real directory
swap (see this package's tests in the KVG_Standards session history) —
the plumbing works. **Not yet verified:** against a real `flet build`
output. Before wiring this into KVGenius, confirm `_find_bundle_binary`'s
platform-specific lookup (`*.exe` on Windows, `*.app/Contents/MacOS/<name>`
on macOS, first file on Linux) actually matches what your Flet version
produces, and that `Path(sys.executable).resolve().parent` in a real Flet
build points at the bundle root rather than some nested subdirectory.
