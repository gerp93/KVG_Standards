# Node service as a .deb (headless server)

A headless Node service (a server with no window, for example a hub and worker that run on a Debian/Ubuntu machine
and, optionally, on Windows) ships as **one self-contained program**, packed as a `.deb` with systemd units next to
the app's other release builds. The install is `sudo apt install ./app-server_1.2.3_amd64.deb`; there is no Node to
install first and no Docker. The workflow is
[`.github/workflows/release-node-deb.yml`](.github/workflows/release-node-deb.yml). First consumer, to be wired:
[FileShuttle](https://github.com/gerp93/FileShuttle)'s hub/worker server. This is the "new tech stack" design for
that category, approved 2026-11-27; it extends [`deb-packaging.md`](deb-packaging.md) (read that first; the shapes
and rules not repeated here are the same) rather than replacing it.

## The rule: one source, no drift

The package must never become a second copy of the app that can fall behind the desktop build:

1. **It is built from the repo's own code.** The app repo's build script makes the server bundle; the workflow only
   wraps that bundle. There is no `debian/` or `packaging/` folder holding a copy of the code, and no hand-built
   binary attached to a release.
2. **Same commit, same tag, same run.** The `node-deb` job is part of the app's `auto-release.yml` /
   `cut-release.yml`, `needs:` the build job, and gets the same tag (`v1.2.3` becomes `1.2.3`).
3. **Same version string.** The workflow exports `APP_VERSION` (the bare version, `1.2.3`) in the environment of
   `build_command`, so the app's build bakes in the tag's version (a `define`/replace in the bundler, never a second
   version file to keep in step).
4. **A smoke test enforces it.** After building, the workflow installs the `.deb` on the runner, runs
   `<command> --version`, and fails the release unless the output contains the tag's version, then removes and
   purges the package and checks the command is gone. The Windows program gets the same version check. A package that
   does not match the tag cannot ship.
5. **It goes on the same GitHub Release** as the other assets, with an install note appended to the release body.

## What the package is

- **One program** built with Node's single-executable application (SEA) feature. The app's server code is bundled
  into ONE CommonJS file by the app repo's own build script (the repo picks the bundler; for a Vite app, Vite's SSR or
  library build is enough). The workflow runs `build_command`, then `node --experimental-sea-config` to make the blob,
  copies the runner's `node` binary and injects the blob with `postject` (sentinel fuse
  `NODE_SEA_FUSE_fce680ab2cc467b6e072b8b5df1996b2`; a Linux binary is unsigned, so nothing is removed first).
- **It carries its own Node runtime.** Debian's Node is too old for `node:sqlite`, so the target machine needs
  nothing from apt but the C libraries (`Depends: libc6, libstdc++6` by default). The Node major is the
  `node_version` input (default 24); upgrading it is a one-line change in the app's workflow call.
- **The bundle must be self-contained**: every dependency inlined, only Node built-ins (`node:sqlite`, `node:fs`...)
  left external, no native addons (a SEA cannot load them). Static assets, such as a built web UI folder, either go
  inside the program through `sea_assets` (`name=path` lines, read with `sea.getAsset`) or are installed beside it
  with `install_map` under `/usr/lib/<package_name>/`.
- **`install_map`** takes `<path> <absolute install path> [mode]` lines. Unlike `release-deb.yml`, the path may be a
  **build output** (the build has already run) and may be a **directory**, copied recursively (a mode, if given,
  applies to its files; symlinks inside are refused). Only the repo's own files and the build's output go in.
- **Layout** (Filesystem Hierarchy, nothing in `/usr/local`):

  | What | Where |
  |---|---|
  | The program | `/usr/lib/<package_name>/<command_name>` (0755), always installed by the workflow |
  | The command | `/usr/bin/<command_name>`, a symlink to it (a `symlinks` line can replace it) |
  | Static assets, if installed beside | `/usr/lib/<package_name>/...` |
  | systemd units | `/usr/lib/systemd/system/` |
  | Settings | `/etc/<package_name>/...`, listed in `conffiles` so dpkg keeps the user's edits |
  | Data | `/var/lib/<package_name>/`, created by the maintainer scripts, never by the package payload |

- **Maintainer scripts** come from `scripts_dir` in the app repo, exactly as in the system-package shape of
  `deb-packaging.md`: create the system user, enable the units, **keep the data on `remove` and delete it only on
  `purge`**, be re-runnable, and **not fail when systemd is not running** (`[ -d /run/systemd/system ]`). They hold
  no application code.
- **`Architecture: amd64`.** The Node binary inside is native. arm64 (a Raspberry Pi) is not covered yet, see below.
- No apt repository and no signing. Control scripts are syntax-checked at build time.

## Memory caps

Every service unit sets a memory cap so a runaway process cannot take the machine down (the house server shares its
RAM with other services): `MemoryMax=` (a hard limit) and, where it helps, `MemoryHigh=` a little below it, sized to
the app's real use plus headroom, for example `MemoryMax=512M`. Also recommended: `Restart=on-failure`,
`NoNewPrivileges=yes`, `ProtectSystem=strict` with `ReadWritePaths=/var/lib/<package_name>`, and `User=` the system
user the maintainer script creates. The workflow prints a warning (not a failure) for any packaged `.service` file
with no `MemoryMax=`.

## Security: a service that can change files

A service that can create, move or delete files (FileShuttle's does) is the most dangerous thing a user runs on a
machine, so:

- **It listens on localhost only** (`127.0.0.1`/`::1`) unless the app documents otherwise and says why. The default
  in the packaged unit and settings file is a loopback address.
- **Reaching it from another machine is the app's job, over the tailnet only**: the app documents
  `tailscale serve` (never `tailscale funnel`) to publish it to the user's own tailnet. A service that can change
  files is **never reachable from the public internet**: no Funnel, no port-forward, no `0.0.0.0` default.
- It runs as its own unprivileged system user, not root, with the access it needs to its own data folder and nothing
  else. Secrets follow [`secrets.md`](secrets.md): never in the package, never in a conffile default; the settings
  file names where a secret comes from, or is created mode 0640 owned by the service user by the maintainer script.

## The Windows build (optional)

`windows: true` adds a job on `windows-latest`, after the `.deb` job, that builds the same bundle with the same
`build_command` and `APP_VERSION`, makes a SEA `.exe` the same way (`signtool remove /s` is run when signtool is on
the runner and is optional; **unsigned is acceptable for now**, so SmartScreen may warn), checks that it reports the
tag's version, zips it with a README (`windows_readme`, or a short generated one) and any extra files
(`windows_files`, for example the web UI folder) and attaches `<package_name>_<version>_windows-x64.zip` to the same
Release. It only runs when asked.

**The workflow does not install anything on Windows.** The app decides how its program runs there, and does it with
its own `install` subcommand, never from the workflow. In particular it is **not a Windows service when it needs the
user's own session**, for example to send files to the user's Recycle Bin (a service runs as another account, with
another bin). Then the app starts at logon as the user: its `install` creates a Scheduled Task "At log on" (or a
shortcut in the user's Startup folder) and `uninstall` removes it. A Windows service is fine for a program that needs
nothing of the user's session.

## Updates

Manual at first: `sudo apt install ./new.deb` (the service is restarted by the maintainer scripts, data and
conffile edits are kept), and unzip the new Windows zip over the old one. Keep the packaged default of a conffile
unchanged between releases, as in `deb-packaging.md`, or an unattended upgrade stops to ask.

## Wiring a repo

`auto-release.yml` and `cut-release.yml` each get a job after the build job (keep the inputs identical in both):

```yaml
  node-deb:
    needs: release          # the GitHub Release already exists by then
    uses: gerp93/KVG_Standards/.github/workflows/release-node-deb.yml@main
    with:
      version: ${{ needs.version.outputs.new_tag }}    # cut-release.yml: needs.tag.outputs.version
      package_name: fileshuttle-server
      command_name: fileshuttle-server
      description: FileShuttle hub and worker server
      build_command: npm ci && npm run build:server
      bundle: dist/server/fileshuttle-server.cjs
      install_map: |
        dist/web /usr/lib/fileshuttle-server/web
        deploy/fileshuttle-server.service /usr/lib/systemd/system/fileshuttle-server.service
        deploy/server.env /etc/fileshuttle-server/server.env 0640
      conffiles: /etc/fileshuttle-server/server.env
      scripts_dir: deploy/debian
      windows: true
      windows_files: |
        dist/web web
    permissions:
      contents: write
```

`ci.yml` calls the same workflow on pull requests with `publish: false`, so the package is built and installed on
the runner (and the Windows program built and checked) on every PR, and a packaging break shows up before a release:

```yaml
  node-deb:
    uses: gerp93/KVG_Standards/.github/workflows/release-node-deb.yml@main
    with:
      version: v0.0.0
      package_name: fileshuttle-server
      command_name: fileshuttle-server
      description: FileShuttle hub and worker server
      build_command: npm ci && npm run build:server
      bundle: dist/server/fileshuttle-server.cjs
      install_map: |
        dist/web /usr/lib/fileshuttle-server/web
        deploy/fileshuttle-server.service /usr/lib/systemd/system/fileshuttle-server.service
        deploy/server.env /etc/fileshuttle-server/server.env 0640
      conffiles: /etc/fileshuttle-server/server.env
      scripts_dir: deploy/debian
      publish: false
    permissions:
      contents: read
```

The app's `--version` must print the baked-in `APP_VERSION`, so the PR run with `v0.0.0` checks the same path a
release does. Inputs: see the comments in the workflow. FileShuttle is the first consumer; it is not wired yet.

## Not covered (yet)

- **arm64** (a Raspberry Pi): the package is `amd64` only. It would need an arm64 runner or a cross-built Node
  binary; bring the design back here first.
- Signing (`.deb`, apt repository, Windows Authenticode) and an apt repository, so installs and upgrades are by
  hand. The Windows program is unsigned.
- Other formats (`.rpm`, macOS, Docker image) and a Windows service installer made by the workflow.
- Native addons in the bundle (a SEA cannot load them).
