# .NET / Avalonia desktop apps

The source of truth for how the standards apply to a **.NET desktop app built with
[Avalonia](https://avaloniaui.net/)** - same role as `game-repos.md` for Godot. First
consumer: [gerp93/KVGuzzler](https://github.com/gerp93/KVGuzzler) (a PC power and
electricity-cost monitor).

**Scope: Windows (`win-x64`) and Linux (`linux-x64`).** macOS is deliberately not built.
Nothing here prevents adding it later; it just isn't supported or tested.

| Category | What an Avalonia app does | Where it lives |
|---|---|---|
| Theming | VisualAssault's Avalonia package, **vendored from a release tag** | VisualAssault `packages/avalonia` + `templates/update-visual-assault-avalonia.sh` |
| Release/CI | `release-avalonia.yml` (Velopack: Windows `Setup.exe`, Linux AppImage) + `ci-dotnet.yml` | `.github/workflows/` |
| Update-check | **Velopack, used directly** (like `electron-updater`) - no KVG_Standards package | this doc, "Update-check" |
| SQLite location | `KvgDbLocation.cs`, **vendored from a tag** | `packages/dotnet/KvgDbLocation` + `templates/update-kvg-dblocation.sh` |
| Application menu | No menu bar; Help/About inside the window | this doc |
| Logo & branding | Same checklist, Avalonia/Velopack equivalents | this doc |
| Licensing | AGPL-3.0, dependencies checked | `licensing.md` |

Also required as for any desktop app: `auto-release.yml` **and** `cut-release.yml`,
`VERSION_BUMP.md`, `TODO.md`, an AGPL-3.0 `LICENSE`, and docs that state the repo follows
KVG_Standards.

## Versions

Target the **current .NET LTS** and the **current Avalonia major**, checked at creation or
audit time (`dotnet --list-sdks`, the Avalonia NuGet page) - never copied from a sibling
repo's `.csproj`, which is how `electron-versioning.md`'s drift happened. Verified together
when this was written: **.NET 10, Avalonia 12.1.4, Velopack 1.2.161**. The SDK matters:
Avalonia 12's analyzers need a newer compiler than the .NET 8 SDK ships.

- **Violation to flag:** more than one major behind current, or an app that skipped the check.
- Avalonia, Velopack and the other NuGet packages may float within a major, but commit a
  lock file (`RestorePackagesWithLockFile`) so a build is reproducible.

## Theming

VisualAssault is the only theme source; there is exactly one theme dependency per repo, pinned
to a tag. Avalonia has no git-subdirectory dependency mechanism and VisualAssault is not
published to NuGet, so consumers use the **vendoring pattern** already written up for Go/static
consumers in `themes-versioning.md`:

- The three files from VisualAssault's `packages/avalonia/VisualAssault/` (`Themes.cs`,
  `FluentMapping.cs`, `ThemeManager.cs`) live in `src/<App>/Themes/VisualAssault/`, each with a
  `// Vendored-from: ... <tag> (<sha>)` first line.
- Refreshed by `scripts/update-visual-assault-avalonia.sh <tag>` (copy
  `templates/update-visual-assault-avalonia.sh`). It refuses `main`.
- Usage: add `<FluentTheme />`, call `ThemeManager.Apply(id)` after Avalonia initializes, bind
  your own XAML to `{DynamicResource VaSurfaceBrush}` etc. Details in VisualAssault's
  `packages/avalonia/README.md`. `<Button Classes="accent">` is the primary-action button.
- A control that renders unthemed is fixed **upstream in VisualAssault** (add its keys to the
  generator's mapping table and release), never by patching the vendored copy or hand-coloring
  it in the app.
- **Violations to flag:** theme files without the tag header, hand-edited theme files, a pin to
  `main`, a hand-rolled palette, or any theme dependency other than VisualAssault.

## Release / CI

An Avalonia app has `auto-release.yml` and `cut-release.yml` calling
[`release-avalonia.yml`](.github/workflows/release-avalonia.yml), plus a `ci.yml` calling
[`ci-dotnet.yml`](.github/workflows/ci-dotnet.yml) on PRs and pushes.

`release-avalonia.yml` follows `release-electron.yml`'s model: the stack's packaging tool
(Velopack's `vpk`, like `electron-builder`) does the packaging and publishes to the release
itself, then the workflow patches the install instructions onto the release body. **The
Inno `windows-installer` action is not used.**

Inputs: `version`, `app_name` (the Velopack package id - never change it after the first
release, installed copies find their updates by it), `project_path` (the `.csproj`),
`exe_name` (the AssemblyName, no extension), and optionally `app_title`, `icon_ico`,
`icon_png`, `publisher`, `dotnet_version`, `test_path`.

What it does, per OS (`windows-latest` → `win-x64`, `ubuntu-latest` → `linux-x64`):

1. Installs `squashfs-tools` and `zstd` on Linux (vpk fails outright without them).
2. Optionally runs `dotnet test`.
3. Reads the Velopack version the project resolves and installs the **same version of `vpk`**
   (Velopack requires the packager and the in-app library to match). **The app must have a
   direct `Velopack` package reference** or the workflow stops with an error.
4. `dotnet publish -c Release -r <rid> --self-contained -p:Version=<tag>` (trimming off:
   Avalonia/XAML bindings and reflection make it fragile).
5. Downloads the previous release's packages (so deltas can be built; the first release has
   none, which is fine), then `vpk pack` with the tag as `--packVersion`.
6. A single final job uploads both platforms with `vpk upload github` **in sequence**, so two
   runners never race to create one release; the release stays a draft until the last upload.

**Produced per platform:** Windows - `Setup.exe`, a portable package, update packages; Linux -
`<app_name>.AppImage` plus update packages (Velopack makes **no** Linux installer or tar.gz).
Update files appear in the release too (`*.nupkg`, `RELEASES-*`, `*.json`); the install
instructions tell users to ignore them. Windows apps install per-user with no admin prompt
(Velopack's default) - except KVGuzzler, see "Exception: per-machine install" below.

**Version stamping is not optional.** `release-go-gui.yml` once shipped without it and every
build reported "update available" forever (see `REPO_SCOPE.md`). Here the tag always becomes
both `-p:Version` and `--packVersion`, and the app reads its version only from Velopack
(`UpdateManager.CurrentVersion`), never from its own constant.

Updates only work for installed builds, from a repo the updater can read **without a token**:
a private repo's releases need a token, which would have to ship inside the app. **Make the
repo public before its first release.**

Not built: macOS. Unsigned builds: SmartScreen warns on Windows; the release notes say so.

## Update-check - Velopack, used directly

Same position as Electron: a real, maintained library (MIT) already solves self-update, so
there is **no KVG_Standards package** (an earlier plan to port `kvgupdate` to C# was dropped).
The standard fixes the wiring so apps don't invent variants; KVGuzzler is the reference
implementation, as Sweeper's `main.ts` is for Electron.

```csharp
// Program.Main - the very first statement. It handles install/uninstall/update hooks and
// may exit the process.
VelopackApp.Build().Run();

// Later (startup, silently; plus a "Check for updates" button in Help/About):
var updates = new UpdateManager(new GithubSource("https://github.com/gerp93/<repo>", accessToken: null, prerelease: false));
if (!updates.IsInstalled) return;                  // a dev run: skip, do not call the other methods
var update = await updates.CheckForUpdatesAsync();
if (update is null) return;                         // already current
await updates.DownloadUpdatesAsync(update);
updates.ApplyUpdatesAndRestart(update);             // does not return on success
```

`CheckForUpdatesAsync` **throws** `NotInstalledException` outside an installed build, so the
`IsInstalled` guard is required. Version shown in the UI: `updates.CurrentVersion`.

- Linux: updates apply to the AppImage. There is no non-updating Linux variant.
- **Violation to flag:** a hand-rolled updater, a missing `VelopackApp.Build().Run()`, a version
  taken from anywhere but Velopack, or a desktop Avalonia app with a release pipeline and no
  update check at all.

## SQLite database location

Applies to an Avalonia app that stores its own data in SQLite. Use
[`packages/dotnet/KvgDbLocation`](packages/dotnet/KvgDbLocation) - one dependency-free source
file **vendored from a tag** with `scripts/update-kvg-dblocation.sh <tag>` (template in
`templates/`). It provides the relocate/adopt/reset bookkeeping and the three instance-isolation
requirements of `db-location-versioning.md`:

1. **Dev and packaged never share a data folder** - `DbLocation.ResolveDataDirectory(app, isDevelopment)`
   gives `<app>-dev` for any non-installed run (`!UpdateManager.IsInstalled`).
2. **Single instance** - `InstanceLock.TryAcquire` (an exclusive file lock; works the same on
   Windows and Linux and frees itself if the process crashes). Exit if it returns null, before
   opening a window or the database.
3. **Never silently create an empty database when a configured path is missing** -
   `IsConfiguredPathMissing()`, then a Quit / use-default choice.

Engine: **`Microsoft.Data.Sqlite` in WAL mode** (real incremental writes; the `sql.js`
whole-file-clobber failure does not apply - items 1-3 are still required). Before relocating,
close connections **and call `SqliteConnection.ClearAllPools()`** - otherwise recent writes sit
in the `-wal` file and the copy is unreadable (measured in the package's smoke tests).

The Settings UI shows the current path **and file size** (`FileSize.Format`: `842 KB`, `4.1 MB`,
`1.3 GB`), choose-existing, choose-new (copies), reset-to-default, then restarts the app.

- **Violations to flag:** a hardcoded database path with no relocation; no file-size display; no
  instance lock; dev and packaged builds resolving to the same folder; a patched vendored copy.

## Application menu

Avalonia has no stock File/Edit/Window bar to strip, and `TextBox` ships its own
cut/copy/paste context menu, so the rules in `electron-menu.md` have nothing to fix here.
Standard: **no menu bar**; an in-window Help/About section with the repo link, issues link,
version and "Check for updates". Native menus (`NativeMenu`) are not used: Linux global menus
depend on the desktop environment.

- **Violations to flag:** a File/Edit/Window-style menu bar with no stated reason, or developer
  tools (Avalonia DevTools) enabled in release builds.

## Logo & branding

Same checklist as `app-standards`' "Logo & branding", Avalonia equivalents:

- README hero image - unchanged.
- Window/taskbar icon - `Window.Icon` from an `AvaloniaResource`.
- In-app usage - logo next to the app name.
- Packaged icon - `<ApplicationIcon>` (`.ico`) in the `.csproj`, and the same icons passed to
  the workflow as `icon_ico` / `icon_png` (the Linux AppImage needs a PNG).
- Generation - `scripts/generate-icons.py` (Python + Pillow, KVGrainy's pattern) emits a multi-size
  `.ico` and PNGs from `assets/logo.png`; the outputs are committed. Not ImageSharp (Six Labors'
  license needs checking before it goes near an AGPL repo).

## Licensing

AGPL-3.0 default; check dependencies per `licensing.md`, whose .NET recipe is
`dotnet list <project> package --include-transitive`, then each package's license in its
`.nuspec`. Baseline: the .NET runtime, Avalonia, SkiaSharp, HarfBuzzSharp, Microsoft.Data.Sqlite
and Velopack are MIT. App-specific dependencies (a sensor library, a chart library) are checked
per app.

## Exception: per-machine install with a background collector (KVGuzzler only)

**Approved by the owner, 2026-10-18.** The standard above is per-user and no-admin. KVGuzzler is
exempt from that part, for one reason: its job is to record power use *continuously*, and a
per-user app only records while its user is logged in and the app is running. A PC that is logged
out, or whose user quit the app, was still drawing power. Other Avalonia apps stay per-user; this
is not a general option.

What changes for KVGuzzler (and only this):

- **Installed per-machine on Windows, with an admin (UAC) prompt at install and at update.**
  `vpk pack` takes `--instLocation` (default `Either`) and `--msi` (a machine-wide bootstrap),
  confirmed against the `vpk` 1.2.161 help; the exact per-machine value and what the Velopack
  update flow does under it are checked at the first Windows release (see "Not yet verified").
- **A headless collector Windows service** (auto-start at boot, runs without anyone logged in)
  ships in the same package. It samples the sensors, writes history, and records why it was not
  sampling (sleep, resume, shutdown) from the service power events. Running with system rights is
  also what lets it use a hardware-monitoring driver for CPUs and GPUs that expose no unprivileged
  counters. The Avalonia window is a per-user viewer of that history; it does not need rights.
- **History lives in `%ProgramData%\<App>`**, written by the service and readable by users, not in
  the per-user data folder. `KvgDbLocation`'s choose-a-folder feature then applies only to the
  per-user settings database, not to collected history (a service cannot write into a folder in a
  user's profile). The three instance-isolation rules above still hold: a development run uses
  `<app>-dev` under `%ProgramData%`, never the installed service's folder; one collector per data
  folder; a missing configured path is never silently replaced by an empty database.
- **Updating a service.** The service has to be stopped before its files are replaced and started
  again afterwards, from Velopack's update hooks. This is the part most likely to need rework, so it
  is tested before the first release.
- **Linux is not covered by this exception.** An AppImage cannot install a system service. The Linux
  equivalent (a systemd unit, or a user unit) is decided when it is built.
- **Audit note:** a per-machine install with an admin prompt is *not* a violation for KVGuzzler. It
  would be for any other Avalonia app.

## Verified, and not yet

Verified when this was written, by running the real tools (Linux, .NET 10, Avalonia 12.1.4,
Velopack 1.2.161):
- VisualAssault's Avalonia package renders the right token colors on real controls under all 14
  themes, and every mapped Fluent key exists with the right kind (its `verify` project).
- `KvgDbLocation`'s smoke tests, including a real second process and a real WAL database.
- `vpk pack` on Linux with the exact arguments the workflow uses, and a second version producing
  a delta package (60 KB against a 39.7 MB full package). The workflow passes `actionlint`.
- The updater calls above compile, and a dev run reports `IsInstalled = false`.

**Not yet verified - check at the first real release:**
- KVGuzzler's per-machine install: which `--instLocation` value and installer to use, that `Setup.exe`
  elevates, that a self-update of a per-machine install works (and asks for UAC), and that the
  collector service is stopped and restarted correctly around it.
- The Windows leg: `vpk pack` for Windows, `Setup.exe` behavior, the install location. Only Linux
  was run.
- `vpk upload github` with `--merge` for the second platform, and that the update feed then
  resolves from the published release.
- Self-update end to end (install version N, publish N+1, watch the update apply) on both OSes.
- Whether the first release (no previous release to base deltas on) behaves as the workflow
  assumes.
