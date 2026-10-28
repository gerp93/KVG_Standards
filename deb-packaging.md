# Debian package (.deb)

A Python app that is also meant to run on a Debian/Ubuntu machine (a server, a Raspberry Pi) ships a
`.deb` next to its other release builds, so the install is `sudo apt install ./app_1.2.3_all.deb`
instead of cloning a repo or copying a file by hand. The workflow is
[`.github/workflows/release-deb.yml`](.github/workflows/release-deb.yml). First user:
[SoSmartButNeverPunctual](https://github.com/gerp93/SoSmartButNeverPunctual).

## The rule: one source, no drift

The `.deb` must never become a second copy of the app that can fall behind the desktop build:

1. **It packages the repo's own files.** `install_files` lists files that already live in the app repo
   (the same ones the PyInstaller build bundles). There is no `debian/` or `packaging/` folder holding a
   duplicate of the code.
2. **Same commit, same tag, same run.** The `deb` job is part of the app's `auto-release.yml` /
   `cut-release.yml`, `needs:` the build job, and gets the same tag. The package version is the tag
   (`v1.2.3` becomes `1.2.3`).
3. **Same version string.** `version_file` writes the same `_version.py` the desktop build uses, so the
   installed app reports the tag's version.
4. **A smoke test enforces it.** After building, the workflow installs the `.deb` on the runner, runs
   `<command> --version`, and fails the release unless the output contains the tag's version, then removes
   the package and checks the command is gone. A package that does not match the tag cannot ship.
5. **It goes on the same GitHub Release** as the other assets, with an install note appended to the
   release body.

## What the package is

- `Architecture: all`, a few tens of KB: the listed source files in `/usr/lib/<package_name>/`, a launcher
  `/usr/bin/<command_name>` (`exec python3 /usr/lib/<package_name>/<entry_point> "$@"`), and the license as
  `/usr/share/doc/<package_name>/copyright`.
- `Depends: python3 (>= 3.9)` by default. It uses the **system Python**; nothing is bundled or compiled.
- No maintainer scripts, no services, no files outside those paths. The app keeps its settings and logins in
  the user's home, so installing, upgrading or removing the package never touches them.
- Upgrade: `sudo apt install ./newer.deb`. Remove: `sudo apt remove <package_name>`.

## Scope

For apps whose runtime is **standard-library-only Python** (a script, or a script plus a Tkinter window).
An app with pip dependencies needs a different design (vendoring or a venv-based package); do not stretch
this workflow to cover it, bring it back here first. A GUI that needs a toolkit can list it under
`recommends` (for example `python3-tk`); there is no separate GUI package yet.

## Wiring a repo

Add a job to **both** `auto-release.yml` and `cut-release.yml`, after the build job:

```yaml
  deb:
    needs: release          # the GitHub Release already exists by then
    uses: gerp93/KVG_Standards/.github/workflows/release-deb.yml@main
    with:
      version: ${{ needs.version.outputs.new_tag }}    # cut-release.yml: needs.tag.outputs.version
      package_name: sosmartbutneverpunctual
      command_name: punctual
      entry_point: punctual.py
      install_files: punctual.py
      description: Keep Samsung appliance clocks in sync through SmartThings
      version_file: _version.py
    permissions:
      contents: write
```

Inputs: see the comments in the workflow. `publish: false` builds and tests the package and uploads it
only as a workflow artifact, which is how to try a change without touching a release.

## Not covered (yet)

- Signing and an apt repository (`apt install myapp` without downloading a file). A `.deb` attached to a
  GitHub Release is installed and upgraded by hand.
- arm64-specific or compiled packages (the package is architecture-independent).
- Other formats (`.rpm`, Flatpak). The Linux PyInstaller binary from `release-python-gui.yml` remains the
  option for machines without a suitable Python.
