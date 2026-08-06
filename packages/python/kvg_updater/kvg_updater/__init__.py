"""Generic GitHub-Releases self-updater for PyInstaller-built desktop apps.

Extracted from KVGrainy's original updater.py — same logic, parameterized by
repo/app_name/current_version instead of hardcoding KVGrainy's. Consumers
pin this package to a released tag (see ../../update-check-versioning.md
in the KVG_Standards repo), never @main.

Asset naming assumes the app was released via KVG_Standards'
release-python-gui.yml, which names artifacts "{app_name}-{platform}[.exe]"
(e.g. "KVGrainy-windows.exe", "KVGrainy-linux", "KVGrainy-macos") — this
module's platform lookup matches that convention exactly, so no
per-app configuration is needed beyond the app's own name.

Usage (each consumer app writes a small wrapper like this, e.g. updater.py):

    from kvg_updater import check_for_update, download_update, apply_update_and_restart

    try:
        from _version import __version__ as CURRENT_VERSION
    except ImportError:
        CURRENT_VERSION = "0.0.0-dev"

    GITHUB_REPO = "gerp93/KVGrainy"
    APP_NAME = "KVGrainy"

    def check():
        return check_for_update(GITHUB_REPO, APP_NAME, CURRENT_VERSION)

The wrapper stays app-specific (repo, app name, where CURRENT_VERSION comes
from); everything else — the GitHub API call, download, and the
platform-specific replace-while-running dance — lives here so it's fixed
once instead of three times.
"""
import json
import os
import platform
import stat
import subprocess
import sys
import tempfile
import urllib.request
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
        import shutil

        shutil.move(str(new_binary_path), str(current_exe))
        os.execv(str(current_exe), [str(current_exe)] + sys.argv[1:])
