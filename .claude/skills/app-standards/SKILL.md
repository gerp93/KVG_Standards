---
name: app-standards
description: gerp93 app-repo conventions — theming (VisualAssault, pinned by tag), release/CI pipelines (KVG_Standards reusable workflows), and self-update (kvg_updater/kvgupdate, pinned by tag). Use when scaffolding a new gerp93 app repo, or auditing/retrofitting an existing one for compliance with these standards.
---

# App standards

Source of truth: [gerp93/KVG_Standards](https://github.com/gerp93/KVG_Standards).
This skill is a checklist, not a copy of the standard — always defer to that
repo's current `README.md` / `themes-versioning.md` /
`update-check-versioning.md` / `.github/workflows/` over anything cached
here.

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

## Release / CI pipeline

First classify the repo — the shape of "release" differs by category:

| Category | Signal | What it needs |
|---|---|---|
| Go library | `go.mod` at root, no `main` package meant to run standalone, other repos import it | `templates/cut-tag.yml` only — bare semver tag, no build |
| Go web app | Has a `Dockerfile`, deployed via [gameshell-deploy](https://github.com/gerp93/gameshell-deploy) / DigitalOcean App Platform | `templates/ci.yml` (build+vet) only. **No** GitHub-Release-binary workflow — deploy happens on push via DO's own GitHub integration, not a release artifact. If one exists, it's vestigial; remove it. |
| Desktop GUI app / plugin | Ships a binary/installer/plugin package end users download | **Both** `templates/auto-release.yml` (fires on every push to `main`) and `templates/cut-release.yml` (manual, explicit version) — see below. Calling the matching `release-*.yml` build variant (`release-python-gui.yml` for PyInstaller, `release-go-gui.yml` for Wails, `release-electron.yml` for Electron, `release-flet.yml` for Flet, `release-streamdeck.yml` for a Stream Deck plugin) |
| Anything else (CLI utility, plugin with its own distribution model, no code yet) | — | Don't force it into one of the above. Flag it for a human decision instead of guessing. |

Desktop GUI apps/plugins get **both** release triggers, not one or the
other: `auto-release.yml` ships a release on every commit to `main` by
default (this is the org's actual expectation — don't default to
manual-only), and `cut-release.yml` stays available for a deliberately
chosen version number when you want one instead of the auto-bump.

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

## Update-check

Applies to any repo in the "Desktop GUI app / plugin" category above that
ships a binary end users run directly (not a web app, not a library, not a
Stream Deck plugin — see below).

- One implementation per stack, shared and pinned — never copy-pasted:
  - PyInstaller (Python) apps: [`packages/python/kvg_updater`](https://github.com/gerp93/KVG_Standards/tree/main/packages/python/kvg_updater), pinned in `requirements.txt` to a tag (`@vX.Y.Z`, never `@main`).
  - Wails/Go apps: [`packages/go/kvgupdate`](https://github.com/gerp93/KVG_Standards/tree/main/packages/go/kvgupdate), pinned in `go.mod` to a tag.
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

## Audit workflow

When asked to check a repo against these standards:
1. Identify its category from the table above.
2. Check theming (if it has a UI), release/CI pipeline, and update-check
   (if it ships a binary end users run directly) against the checklists.
3. List every deviation found — don't silently fix anything in an audit-only
   pass.
4. When asked to bring it into compliance, land it as its own PR per repo
   so the diff is reviewable, not a blind mass-apply.
