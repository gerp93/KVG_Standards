---
name: app-standards
description: gerp93 app-repo conventions — theming (VisualAssault, pinned by tag) and release/CI pipelines (KVG_Standards reusable workflows). Use when scaffolding a new gerp93 app repo, or auditing/retrofitting an existing one for compliance with these standards.
---

# App standards

Source of truth: [gerp93/KVG_Standards](https://github.com/gerp93/KVG_Standards).
This skill is a checklist, not a copy of the standard — always defer to that
repo's current `README.md` / `themes-versioning.md` / `.github/workflows/`
over anything cached here.

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
| Desktop GUI app | Ships a binary/installer end users download | Tag via `templates/cut-release.yml`, calling the matching `release-*.yml` build variant (`release-python-gui.yml` for PyInstaller, `release-go-gui.yml` for Wails, `release-electron.yml` for Electron, `release-flet.yml` for Flet) |
| Anything else (CLI utility, plugin with its own distribution model, no code yet) | — | Don't force it into one of the above. Flag it for a human decision instead of guessing. |

**Violations to flag:**
- A local copy of build/release logic that duplicates a `KVG_Standards`
  reusable workflow instead of calling it via `uses:`.
- A release workflow whose trigger/versioning scheme differs from
  `templates/cut-release.yml`'s (explicit `workflow_dispatch` version input,
  not auto-bump-on-push or a hand-maintained `version_bump.sh`).
- Two repos independently reinventing the same script (e.g. a copy-pasted
  `version_bump.sh`) — that's exactly the drift this repo exists to stop;
  it belongs in `KVG_Standards` instead.

## Audit workflow

When asked to check a repo against these standards:
1. Identify its category from the table above.
2. Check theming (if it has a UI) and release/CI pipeline against the
   checklists.
3. List every deviation found — don't silently fix anything in an audit-only
   pass.
4. When asked to bring it into compliance, land it as its own PR per repo
   so the diff is reviewable, not a blind mass-apply.
