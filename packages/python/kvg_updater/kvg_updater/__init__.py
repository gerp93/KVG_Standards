"""Generic GitHub-Releases self-updater for Python desktop apps.

Extracted from KVGrainy's original updater.py — same logic, parameterized by
repo/app_name/current_version instead of hardcoding KVGrainy's. Consumers
pin this package to a released tag (see ../../update-check-versioning.md
in the KVG_Standards repo), never @main.

Two modes, because "the app" isn't always one file:

- **Single-file mode** (`check_for_update` / `download_update` /
  `apply_update_and_restart`) — for PyInstaller `--onefile` builds via
  `release-python-gui.yml`, which names artifacts
  "{app_name}-{platform}[.exe]" (e.g. "KVGrainy-windows.exe"). This is the
  original KVGrainy shape.
- **Bundle mode** (`check_for_bundle_update` / `download_and_extract_bundle`
  / `apply_bundle_update_and_restart`) — for Flet apps via
  `release-flet.yml`, which packages a whole build *directory* (Flet's
  `flet build` output is a Flutter-engine binary plus supporting files, not
  a single self-contained executable — closer in shape to `kvgupdate`'s Go
  packages than to a PyInstaller onefile binary) as
  "{app_name}-{version}-{platform}.{zip|tar.gz}". Genuinely required for
  Flet; don't try to force single-file mode onto a Flet app.

Usage — single-file mode (each consumer app writes a small wrapper like
this, e.g. updater.py):

    from kvg_updater import check_for_update, download_update, apply_update_and_restart

    try:
        from _version import __version__ as CURRENT_VERSION
    except ImportError:
        CURRENT_VERSION = "0.0.0-dev"

    GITHUB_REPO = "gerp93/KVGrainy"
    APP_NAME = "KVGrainy"

    def check():
        return check_for_update(GITHUB_REPO, APP_NAME, CURRENT_VERSION)

Usage — bundle mode (Flet):

    from pathlib import Path
    from kvg_updater import (
        check_for_bundle_update, download_and_extract_bundle,
        apply_bundle_update_and_restart,
    )

    GITHUB_REPO = "gerp93/KVGenius"
    APP_NAME = "KVGenius"
    # The directory the running build lives in — one level above the
    # executable found inside it. For a Flet build this is normally the
    # directory containing the platform bundle (the .app on macOS, the
    # folder with the .exe + DLLs on Windows, the folder with the ELF +
    # shared libs on Linux).
    APP_DIR = Path(sys.executable).resolve().parent  # verify for your build layout

    def check_and_apply(current_version: str):
        info = check_for_bundle_update(GITHUB_REPO, APP_NAME, current_version)
        if not info:
            return False
        staged = download_and_extract_bundle(info["download_url"], APP_NAME)
        apply_bundle_update_and_restart(staged, APP_DIR, APP_NAME)  # never returns
        return True

The wrapper stays app-specific (repo, app name, where CURRENT_VERSION comes
from, and — in bundle mode — where the running build's directory actually
is); everything else lives here so it's fixed once instead of per-app.

**Bundle mode has not been exercised against a real Flet build yet** —
confirm `APP_DIR`/the relaunch-binary lookup actually match your build's
layout (see `_find_bundle_binary`) before relying on it silently. Flet
build layouts can differ by Flet version.
"""
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable, Optional


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _parse_version(text: str) -> tuple[int, int, int]:
    core = text.strip().lstrip("v").split("-")[0]
    parts = []
    for piece in core.split("."):
        digits = "".join(ch for ch in piece if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def _asset_name_for_platform(app_name: str) -> str:
    system = platform.system()
    if system == "Windows":
        return f"{app_name}-windows.exe"
    if system == "Darwin":
        return f"{app_name}-macos"
    return f"{app_name}-linux"


def check_for_update(repo: str, app_name: str, current_version: str) -> Optional[dict]:
    """Return {"version": str, "download_url": str} if a newer release is
    available on `repo` (e.g. "gerp93/KVGrainy") for this platform's asset,
    else None. Only ever returns non-None for a packaged (frozen) build."""
    if not is_frozen() or current_version == "0.0.0-dev":
        return None
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.load(response)
    except Exception:
        return None

    latest_tag = data.get("tag_name", "")
    if _parse_version(latest_tag) <= _parse_version(current_version):
        return None

    asset_name = _asset_name_for_platform(app_name)
    for asset in data.get("assets", []):
        if asset.get("name") == asset_name:
            return {"version": latest_tag.lstrip("v"), "download_url": asset["browser_download_url"]}
    return None


def download_update(download_url: str, app_name: str, progress_callback: Optional[Callable[[float], None]] = None) -> Path:
    dest = Path(tempfile.mkdtemp(prefix=f"{app_name.lower()}_update_")) / _asset_name_for_platform(app_name)
    request = urllib.request.Request(download_url, headers={"Accept": "application/octet-stream"})
    with urllib.request.urlopen(request, timeout=30) as response, open(dest, "wb") as out_file:
        total = int(response.headers.get("Content-Length", 0))
        read = 0
        while True:
            chunk = response.read(65536)
            if not chunk:
                break
            out_file.write(chunk)
            read += len(chunk)
            if progress_callback and total:
                progress_callback(read / total)

    if platform.system() != "Windows":
        current_mode = os.stat(dest).st_mode
        os.chmod(dest, current_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return dest


def apply_update_and_restart(new_binary_path: Path, app_name: str) -> None:
    """Replace the running executable with new_binary_path and relaunch.
    Never returns: exits (Windows) or execv's (macOS/Linux) the process.

    Call this from your own code path, not from a GUI-framework callback
    (e.g. Tkinter's root.after) without checking your framework's exception
    handling first — see the Windows branch's comment below. KVGrainy hit
    this exact issue via Tkinter; it likely generalizes to any GUI
    framework whose callback dispatcher swallows SystemExit.
    """
    current_exe = Path(sys.executable).resolve()
    slug = app_name.lower().replace(" ", "_")

    if platform.system() == "Windows":
        script_path = new_binary_path.parent / f"{slug}_update.bat"
        script_contents = (
            "@echo off\r\n"
            ":retry\r\n"
            f'del "{current_exe}" >nul 2>&1\r\n'
            f'if exist "{current_exe}" (\r\n'
            "  timeout /t 1 /nobreak >nul 2>&1\r\n"
            "  goto retry\r\n"
            ")\r\n"
            f'move /y "{new_binary_path}" "{current_exe}" >nul 2>&1\r\n'
            "timeout /t 2 /nobreak >nul 2>&1\r\n"
            f'explorer.exe "{current_exe}"\r\n'
            'del "%~f0"\r\n'
        )
        # write_bytes, not write_text: text mode would additionally
        # translate the \n in these \r\n literals into \r\n itself,
        # doubling every carriage return.
        script_path.write_bytes(script_contents.encode("ascii"))
        # del/move/timeout all work fine from a plain batch script, but
        # launching via `start` (CreateProcess, through cmd's builtin)
        # reliably failed to load python311.dll in KVGrainy's testing,
        # while a manual double-click of that exact file (ShellExecute,
        # through Explorer) always worked. explorer.exe here routes the
        # relaunch through the same shell code path the working manual
        # case uses.
        subprocess.Popen(
            ["cmd", "/c", str(script_path)],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        # sys.exit() raises SystemExit, which some GUI frameworks' callback
        # dispatchers (confirmed for Tkinter's root.after) silently swallow
        # instead of letting it terminate the process — the batch script's
        # wait-for-exit loop would then spin forever. os._exit() kills the
        # process outright, bypassing any such handler.
        os._exit(0)
    else:
        shutil.move(str(new_binary_path), str(current_exe))
        os.execv(str(current_exe), [str(current_exe)] + sys.argv[1:])


# --- Bundle mode (Flet) -----------------------------------------------------


def _bundle_asset_name(app_name: str, tag: str) -> Optional[str]:
    """Match release-flet.yml's/release-go-gui.yml's archive naming:
    "{app_name}-{tag}-{platform}.{zip|tar.gz}", tag keeping its "v" prefix.
    Returns None for an unrecognized platform.system() value."""
    system = platform.system()
    if system == "Windows":
        return f"{app_name}-{tag}-windows.zip"
    if system == "Darwin":
        return f"{app_name}-{tag}-macos.tar.gz"
    if system == "Linux":
        return f"{app_name}-{tag}-linux.tar.gz"
    return None


def check_for_bundle_update(repo: str, app_name: str, current_version: str) -> Optional[dict]:
    """Same contract as check_for_update, for the bundle-archive naming
    scheme instead of the single-file one."""
    if not is_frozen() or current_version == "0.0.0-dev":
        return None
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.load(response)
    except Exception:
        return None

    latest_tag = data.get("tag_name", "")
    if _parse_version(latest_tag) <= _parse_version(current_version):
        return None

    asset_name = _bundle_asset_name(app_name, latest_tag)
    if asset_name is None:
        return None
    for asset in data.get("assets", []):
        if asset.get("name") == asset_name:
            return {"version": latest_tag.lstrip("v"), "download_url": asset["browser_download_url"]}
    return None


def download_and_extract_bundle(download_url: str, app_name: str) -> Path:
    """Download the release archive and extract it to a fresh temp dir.
    Returns the path to the extracted build (descending into the single
    top-level directory the archive contains, if there is one, so callers
    get the actual build root rather than a wrapper folder)."""
    workdir = Path(tempfile.mkdtemp(prefix=f"{app_name.lower()}_update_"))
    is_zip = download_url.endswith(".zip") or platform.system() == "Windows"
    archive_path = workdir / ("bundle.zip" if is_zip else "bundle.tar.gz")

    request = urllib.request.Request(download_url, headers={"Accept": "application/octet-stream"})
    with urllib.request.urlopen(request, timeout=60) as response, open(archive_path, "wb") as out_file:
        shutil.copyfileobj(response, out_file)

    extract_dir = workdir / "extracted"
    extract_dir.mkdir()
    if is_zip:
        with zipfile.ZipFile(archive_path) as zf:
            zf.extractall(extract_dir)
    else:
        with tarfile.open(archive_path) as tf:
            tf.extractall(extract_dir)
    archive_path.unlink()

    entries = list(extract_dir.iterdir())
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    return extract_dir


def _find_bundle_binary(bundle_dir: Path, app_name: str) -> Path:
    """Locate the executable to relaunch inside an extracted bundle.
    Layout assumptions per platform mirror kvgupdate.go's findNewBinary;
    unconfirmed against a real `flet build` output, see this package's
    README before relying on it silently."""
    system = platform.system()
    if system == "Windows":
        matches = list(bundle_dir.glob("*.exe"))
        if matches:
            return matches[0]
        raise FileNotFoundError(f"no .exe found in {bundle_dir}")
    if system == "Darwin":
        app_bundles = list(bundle_dir.glob("*.app"))
        if app_bundles:
            macos_dir = app_bundles[0] / "Contents" / "MacOS"
            candidates = [p for p in macos_dir.iterdir() if p.is_file()] if macos_dir.is_dir() else []
            if candidates:
                return candidates[0]
        raise FileNotFoundError(f"no .app bundle found in {bundle_dir}")
    for path in sorted(bundle_dir.iterdir()):
        if path.is_file():
            return path
    raise FileNotFoundError(f"no executable found in {bundle_dir}")


def apply_bundle_update_and_restart(staged_dir: Path, app_dir: Path, app_name: str) -> None:
    """Swap the running build's directory (app_dir) for staged_dir and
    relaunch. Never returns: exits (Windows) or execv's (macOS/Linux).

    Same Tkinter/GUI-callback caveat as apply_update_and_restart applies
    here too — call from a code path whose exception handling you trust,
    not blindly from a framework callback dispatcher.
    """
    app_dir = app_dir.resolve()
    backup_dir = app_dir.parent / f"{app_dir.name}.old"

    if platform.system() == "Windows":
        new_binary = _find_bundle_binary(staged_dir, app_name)
        script_path = staged_dir.parent / f"{app_name.lower()}_update.bat"
        script_contents = (
            "@echo off\r\n"
            ":retry\r\n"
            f'rmdir /s /q "{backup_dir}" >nul 2>&1\r\n'
            f'move /y "{app_dir}" "{backup_dir}" >nul 2>&1\r\n'
            f'if exist "{app_dir}" (\r\n'
            "  timeout /t 1 /nobreak >nul 2>&1\r\n"
            "  goto retry\r\n"
            ")\r\n"
            f'move /y "{staged_dir}" "{app_dir}" >nul 2>&1\r\n'
            f'rmdir /s /q "{backup_dir}" >nul 2>&1\r\n'
            "timeout /t 2 /nobreak >nul 2>&1\r\n"
            f'explorer.exe "{app_dir / new_binary.name}"\r\n'
            'del "%~f0"\r\n'
        )
        script_path.write_bytes(script_contents.encode("ascii"))
        subprocess.Popen(
            ["cmd", "/c", str(script_path)],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        os._exit(0)
    else:
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        shutil.move(str(app_dir), str(backup_dir))
        shutil.move(str(staged_dir), str(app_dir))
        shutil.rmtree(backup_dir, ignore_errors=True)
        new_binary = _find_bundle_binary(app_dir, app_name)
        os.execv(str(new_binary), [str(new_binary)] + sys.argv[1:])
