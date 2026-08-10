---
name: app-standards
description: gerp93 app-repo conventions — theming (VisualAssault, pinned by tag), release/CI pipelines (KVG_Standards reusable workflows), self-update (kvg_updater/kvgupdate, pinned by tag), licensing (AGPL-3.0 by default), SQLite database location (kvg_dblocation, pinned by tag), logo & branding, release notes, VERSION_BUMP.md, per-repo TODO.md, and docs linking back to KVG_Standards. Use when scaffolding a new gerp93 app repo, or auditing/retrofitting an existing one for compliance with these standards.
---

# App standards

Source of truth: [gerp93/KVG_Standards](https://github.com/gerp93/KVG_Standards).
This skill is a checklist, not a copy of the standard — always defer to that
repo's current `README.md` / `themes-versioning.md` /
`update-check-versioning.md` / `licensing.md` / `db-location-versioning.md`
/ `game-repos.md` / `.github/workflows/` over anything cached here.

## Docs must point back here

Every consumer repo's `README.md` and/or `CLAUDE.md` must link to
[gerp93/KVG_Standards](https://github.com/gerp93/KVG_Standards) and state
that the repo follows it — not just scattered incidental links to one
specific doc (a `themes-versioning.md` link buried in a dependency note
doesn't count on its own). Someone reading the repo's own docs should be
able to tell it's a KVG_Standards consumer and know where to go for the
actual rules.
- **Violation to flag:** a consumer repo whose docs never mention
  KVG_Standards at all.
- **Violation to flag:** a consumer repo that only links to KVG_Standards
  in passing for a single topic (e.g. just the theming pin) without ever
  stating that it follows the standard as a whole.

## New tech stacks

Theming, release/CI, update-check, and licensing each cover a fixed list of
stacks today (Tkinter/Flet/Electron/Wails/CSS/Angular, PyInstaller/Wails/
Electron/Flet, etc.). If a new app needs a stack that isn't in one of these
checklists, **that's not something to solve locally in the app repo**:

1. Design the standard for that stack, following the shape of the existing
   pattern for its category (e.g. a new `packages/<lang>/<name>` for
   update-check, a new `release-*.yml` for release/CI, a new theming
   package alongside VisualAssault's existing ones).
2. **Ask the human to approve the design before implementing it.** This is
   a shared-API decision — every future repo on that stack inherits
   whatever gets decided here.
3. Once approved, add it to `gerp93/KVG_Standards` itself (the package/
   workflow/template, plus a doc like `themes-versioning.md`/
   `update-check-versioning.md`/`licensing.md`), and update this skill so
   future audits and new repos pick it up automatically.
4. Only then wire it into the app repo that needed it.

A one-off implementation living only in the consumer app repo is exactly
the drift this whole standard exists to prevent — don't let "we'll
generalize it later" become permanent.

## Licensing

- Default license is **AGPL-3.0** for every active repo — copy an existing
  repo's `LICENSE` file rather than hand-typing it (they're all identical
  boilerplate).
- **Before assuming AGPL-3.0 is fine, check the repo's dependencies.**
  Permissive licenses (MIT/BSD/Apache-2.0/etc.) and LGPL are always
  compatible. GPL-2.0-**or-later** is compatible; plain GPL-2.0-only is
  **not** and blocks AGPL-3.0 for that repo. See `licensing.md` for how to
  actually check a dependency's declared license instead of guessing from
  its name or reputation.
- **Violation to flag:** a repo with no `LICENSE` file at all.
- **Violation to flag:** a repo whose dependencies are incompatible with its
  declared license (e.g. AGPL-3.0 declared, but something GPL-2.0-only or
  source-available/non-commercial is a dependency) — this needs a human
  decision (swap the dependency, or use a different license for that one
  repo), not a silent fix.

## Theming

- Theme source is [VisualAssault](https://github.com/gerp93/VisualAssault).
  There should be exactly one theme dependency per repo, pinned to a tag.
- **Violation to flag:** a dependency on `@main` instead of `@vX.Y.Z`.
- **Violation to flag:** a dependency on anything other than VisualAssault
  for theming (e.g. the old `KVG_Themes`/`KVG_Themes_Flet`/`KVG_RGB` repos,
  or a hand-rolled theme file/struct that duplicates VisualAssault's
  palette instead of importing its package). Hand-copied palettes drift
  silently from the source of truth — flag even if the colors currently
  match.
- Packages exist for CSS, Tkinter, Flet, and Angular. If a repo's stack
  isn't one of those, "vibe install" (see VisualAssault's README) is
  acceptable for prototypes but should not be treated as a real dependency
  in anything that gets a release pipeline.
- Godot games are a deliberate exception, not a gap to flag yet: no
  VisualAssault package exists for GDScript, so placeholder/no-theme is
  expected for now — see `game-repos.md`.

## Logo & branding

Every new app repo gets a logo checked in and wired into every surface a
user can see it, not just dropped into the README and forgotten.

- Source mark lives at `assets/logo.png` — a square (or squarable), high-res
  master. Everything else is generated from it by a one-off
  `scripts/generate-icons.*` script (Node+`sharp` for Electron repos,
  Python+Pillow for PyInstaller repos) — never hand-export each size
  separately, that's exactly the kind of copy drift this repo exists to
  prevent. See Sweeper's `scripts/generate-icons.js` (Electron/sharp
  reference) and KVGrainy's `scripts/generate_icons.py` (PyInstaller/Pillow
  reference) for the pattern: pad to square, then emit each size/format
  below from that one padded source.
- **Placement checklist — every surface below should exist, not just
  whichever one is easiest:**
  - **README** — logo image near the top of the file (`assets/logo.png` or
    a purpose-made hero crop), before the H1 title.
  - **In-app window/taskbar icon** — set at runtime so it shows while the
    app is running, independent of the packaged binary's own icon:
    Electron `BrowserWindow({ icon: ... })`, Tkinter
    `root.iconphoto(True, ...)`, Flet `page.window.icon`, Wails
    `options.App{ Icon: ... }`. Sweeper's `src/main/main.ts` and KVGrainy's
    `gui.py` (`setup_icon`) are the reference implementations for
    Electron/Tkinter respectively.
  - **In-app usage** — the logo shown somewhere in the app's own UI, next to
    the app name (Sweeper's sidebar, KVGrainy's header row next to the
    title/subtitle). Skip only if the app genuinely has no chrome to put it
    in.
  - **Packaged binary/installer icon** — the icon Explorer/Finder/the
    taskbar shows for the built artifact itself, before the app even
    launches: electron-builder's `build.icon` (from `build/icon.png`,
    auto-converted per platform), PyInstaller's `--icon` flag (`.ico` on
    Windows, `.icns` on macOS, unsupported on Linux — KVG_Standards'
    `release-python-gui.yml` takes this as the `icon_path` input), Wails'
    `wails.json` icon config.
  - **GitHub repo social preview** (optional, manual) — Settings → General
    → Social preview. Not scriptable via git; a human uploads it once. Skip
    for repos with no public-facing purpose.
- **Violation to flag:** a desktop GUI app/plugin repo with no
  `assets/logo.png` (or equivalent) at all.
- **Violation to flag:** a logo present in only one surface (e.g. README
  image but nothing wired into the app itself or the packaged binary) —
  that's an incomplete rollout, not a stylistic choice.
- **Violation to flag:** icon files hand-exported/hand-copied per size
  instead of generated from the one source mark by a checked-in script —
  same drift risk as a hand-rolled theme palette.

## Release notes

Every `release-*.yml` build variant with a `softprops/action-gh-release` (or
equivalent) step prepends a short "## Installing" blurb to the release body
via `body:` + `generate_release_notes: true` (GitHub's API pre-pends `body`
to the auto-generated changelog, so both show up: install instructions on
top, changelog below). This isn't retroactive — it only applies to releases
cut after a repo's workflow is on the updated `release-*.yml`, existing
releases keep whatever notes they already had.
- **Violation to flag:** a `release-*.yml` variant whose publish step has
  `generate_release_notes: true` but no `body`.
- Electron is the odd one out: `electron-builder --publish always` uploads
  straight to the release with no `softprops/action-gh-release` step to
  hand a `body` to, so `release-electron.yml` patches the body onto the
  release electron-builder already created via a follow-up `gh api` PATCH
  job (`release-notes`, `needs: build`). Follow that pattern if a future
  stack's build tool similarly self-publishes instead of going through
  `softprops/action-gh-release`.

## Release / CI pipeline

First classify the repo — the shape of "release" differs by category:

| Category | Signal | What it needs |
|---|---|---|
| Go library | `go.mod` at root, no `main` package meant to run standalone, other repos import it | `templates/cut-tag.yml` only — bare semver tag, no build |
| Go web app | Has a `Dockerfile`, deployed via [gameshell-deploy](https://github.com/gerp93/gameshell-deploy) / DigitalOcean App Platform | `templates/ci.yml` (build+vet) only. **No** GitHub-Release-binary workflow — deploy happens on push via DO's own GitHub integration, not a release artifact. If one exists, it's vestigial; remove it. |
| Desktop GUI app / plugin | Ships a binary/installer/plugin package end users download | **Both** `templates/auto-release.yml` (fires on every push to `main`) and `templates/cut-release.yml` (manual, explicit version) — see below. Calling the matching `release-*.yml` build variant (`release-python-gui.yml` for PyInstaller, `release-go-gui.yml` for Wails, `release-electron.yml` for Electron, `release-flet.yml` for Flet, `release-streamdeck.yml` for a Stream Deck plugin) |
| Godot game | GDScript project (no C#/.NET), ships a native desktop export end users download | Same as Desktop GUI app/plugin, calling `release-godot.yml` — see `game-repos.md` for the full breakdown (theming and icon generation are not yet covered for this category). |
| Anything else (CLI utility, plugin with its own distribution model, no code yet) | — | Don't force it into one of the above. This is the "New tech stacks" case above — ask the human before designing a new pattern. |

Desktop GUI apps/plugins get **both** release triggers, not one or the
other: `auto-release.yml` ships a release on every commit to `main` by
default (this is the org's actual expectation — don't default to
manual-only), and `cut-release.yml` stays available for a deliberately
chosen version number when you want one instead of the auto-bump.

Every repo with `auto-release.yml` also gets `templates/VERSION_BUMP.md`
copied in as `VERSION_BUMP.md` at the repo root. `auto-release.yml` bumps
on *every* push to `main` regardless of what changed, so when you need a
release with no real code change (e.g. to pick up an updated KVG_Standards
reusable workflow), editing this file and adding a dated one-line entry
gives a real, reviewable diff instead of an empty commit — see KVGrainy's
`VERSION_BUMP.md` for the reference implementation.

**Violations to flag:**
- A local copy of build/release logic that duplicates a `KVG_Standards`
  reusable workflow instead of calling it via `uses:`.
- A desktop GUI app/plugin repo with only `cut-release.yml` and no
  `auto-release.yml` (or vice versa) — it needs both.
- A hand-maintained `version_bump.sh` or other bespoke versioning script
  duplicating what `auto-release.yml`/`cut-release.yml` already do.
- Two repos independently reinventing the same script (e.g. a copy-pasted
  `version_bump.sh`) — that's exactly the drift this repo exists to stop;
  it belongs in `KVG_Standards` instead.
- A repo with `auto-release.yml` but no `VERSION_BUMP.md`, or empty
  `git commit --allow-empty` commits used to force a release instead of it.

## Update-check

Applies to any repo in the "Desktop GUI app / plugin" category above that
ships a binary end users run directly (not a web app, not a library, not a
Stream Deck plugin — see below).

- One implementation per stack, shared and pinned — never copy-pasted:
  - PyInstaller (Python) apps: [`packages/python/kvg_updater`](https://github.com/gerp93/KVG_Standards/tree/main/packages/python/kvg_updater), pinned in `requirements.txt` to a tag (`@vX.Y.Z`).
  - Wails/Go apps: [`packages/go/kvgupdate`](https://github.com/gerp93/KVG_Standards/tree/main/packages/go/kvgupdate), pinned in `go.mod` to a tag.
  - **Current interim exception:** KVG_Standards has no tagged releases yet,
    so every consumer above is currently pinned to `@main` instead (see
    `update-check-versioning.md`'s documented exception) — don't flag this
    as a violation right now. Once KVG_Standards cuts a first tag, pins
    should move to it; flag a repo still on `@main` *after* that point.
  - Electron apps: `electron-updater` directly — this is already a real,
    maintained library, not something KVG_Standards needs to wrap. See
    Sweeper's `src/main/main.ts` for the reference wiring.
  - Flet apps: `kvg_updater`'s **bundle mode**
    (`check_for_bundle_update`/`download_and_extract_bundle`/
    `apply_bundle_update_and_restart`), pinned the same way as its
    single-file mode. Swaps the whole build directory instead of one
    binary, matching `release-flet.yml`'s archive shape. The extraction
    and directory-swap logic is smoke-tested but not yet run against a
    real `flet build` output — verify `_find_bundle_binary`'s layout
    assumptions before trusting it silently in a given app (see the
    package's README).
  - Godot games: [`packages/godot/kvg_update`](https://github.com/gerp93/KVG_Standards/tree/main/packages/godot/kvg_update)
    — **notify-only** (opens the release page, no self-replace; see the
    package's doc comment for why). Godot has no dependency manager that
    can pin a git ref, so unlike the packages above this one is
    **vendored (copied)** into `addons/kvg_update/`, not declared as a
    pinned dependency — refreshed via a per-repo
    `scripts/update-kvg-update.sh` that stamps the source commit into a
    header comment. See `game-repos.md` and `gerp93/airport`'s copy for
    the reference version.
- **Violation to flag:** a hand-rolled update-check/self-replace
  implementation instead of the shared package for that stack — this is
  exactly the kind of logic (GitHub Releases API polling, platform-specific
  replace-while-running) that's easy to get subtly wrong three different
  ways across three repos.
- **Violation to flag:** a desktop GUI app/plugin with a release pipeline
  but no update-check at all — not necessarily wrong (KVGauge's Stream Deck
  plugin is a deliberate exception, see below), but worth surfacing as a
  gap rather than silently skipping it.
- **KVGauge (Stream Deck plugin) is a deliberate exception**, not a gap:
  Stream Deck plugins are normally reinstalled via a new `.streamDeckPlugin`
  file or the Elgato Marketplace, not self-updated. Don't add update-check
  here without a specific reason to override that.

## SQLite database location

Applies to any app that stores its own data in a local SQLite file (not a
server-side database like MariaDB — card-judge/timeline-trivia don't need
this).

- Don't hardcode a fixed relative/absolute path for the database file. The
  user should be able to relocate it — e.g. into a cloud-synced folder —
  for backup/syncing, without losing data.
- One implementation per stack, shared and pinned:
  - Python apps: [`packages/python/kvg_dblocation`](https://github.com/gerp93/KVG_Standards/tree/main/packages/python/kvg_dblocation), pinned in `requirements.txt` to a tag (currently `@main`, see the interim exception in `db-location-versioning.md`).
  - Electron apps: follow Sweeper's `src/main/dbLocation.ts` as the
    reference pattern directly — same default/effective/set/reset shape,
    same copy-on-relocate behavior, parameterized for the new app's name.
- A Settings UI should expose: the current path, "choose an existing
  file" (adopt as-is), "choose a new location" (copies the current
  database there), and "reset to default" — then restart the app, since
  an already-open database connection can't be pointed at a new path.
- **Violation to flag:** a SQLite-backed app with a hardcoded db path and
  no way for the user to relocate it (e.g. KVGenius's
  `chat_history.py: db_path: str = "./chat_history.db"` before this was
  fixed).

## Per-repo TODO.md

Every active app repo gets a `TODO.md` at its root (copy
`templates/TODO.md`) — that app's own backlog of future features and
fixes. This is **not** a KVG_Standards compliance list (that's
`REPO_SCOPE.md`'s job) — it's product/feature backlog specific to that one
app, maintained by whoever works on it.
- **Violation to flag:** an active app repo with no `TODO.md` at all.

## Repo scope tracking

[`REPO_SCOPE.md`](https://github.com/gerp93/KVG_Standards/blob/main/REPO_SCOPE.md)
is the map of which standards apply to which active app repo. It's a scope
reference (what should apply, by category), not a live compliance
snapshot — when an audit pass finds real drift, note it there (or in that
file's per-repo detail section) so the next session doesn't have to
re-derive it from scratch. Add new repos to it as they're created; remove
retired ones.

## Audit workflow

When asked to check a repo against these standards:
1. Identify its category from the table above (cross-check against
   `REPO_SCOPE.md` — add the repo there if it's missing).
2. Check theming (if it has a UI), release/CI pipeline, update-check
   (if it ships a binary end users run directly), licensing, logo &
   branding, release notes, `VERSION_BUMP.md`, database location (if it
   stores data in SQLite), and `TODO.md` against the checklists above.
3. List every deviation found — don't silently fix anything in an audit-only
   pass.
4. When asked to bring it into compliance, land it as its own PR per repo
   so the diff is reviewable, not a blind mass-apply. Update `REPO_SCOPE.md`
   with what you found.
