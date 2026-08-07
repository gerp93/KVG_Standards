# KVG_Standards

Source of truth for how gerp93 app repos build, release, and theme
themselves — so that "the standard" lives in one place and repos pull from
it, instead of each repo growing its own copy that quietly drifts.

See **[`ROLLOUT_TODO.md`](ROLLOUT_TODO.md)** for the current gap matrix and
per-repo checklist of what's not yet aligned (theming, auto-release,
update-check).

## What lives here

- **`.github/workflows/`** — reusable (`workflow_call`) build+release
  workflows. Repos don't copy these; they call them by tag
  (`uses: gerp93/KVG_Standards/.github/workflows/<name>.yml@main`).
- **`templates/`** — small per-repo entry-point workflows that *do* get
  copied in (GitHub requires `workflow_dispatch` triggers to live in the
  calling repo — see comments in each template for why). These are
  intentionally thin; all the real logic lives in `.github/workflows/`.
- **`.claude/skills/app-standards/`** — a Claude Code skill encoding these
  conventions, so a new app repo (or an audit of an existing one) picks
  them up automatically. See its `SKILL.md` for what it checks.

## Theming

Theme source of truth is [VisualAssault](https://github.com/gerp93/VisualAssault)
(CSS, Tkinter, Flet, and Angular packages, deterministically generated from
`themes/THEMES.md`). Consumers must pin to a released tag
(`@vX.Y.Z`), never `@main` — see `themes-versioning.md`.

## Licensing

Default license for every active repo is **AGPL-3.0**, checked against that
repo's actual dependencies case by case (permissive/LGPL/GPL-or-later
dependencies are fine; anything more restrictive is a real blocker) — see
`licensing.md`.

## Update-check

Self-update (check GitHub Releases, download, replace the running binary)
is a shared component too, not something each app reinvents:
[`packages/python/kvg_updater`](packages/python/kvg_updater) (PyInstaller
apps) and [`packages/go/kvgupdate`](packages/go/kvgupdate) (Wails/Go apps).
Electron apps use `electron-updater` directly (see Sweeper's
`src/main/main.ts`) — no KVG_Standards package needed there. Consumers pin
to a released tag, never `@main` — see `update-check-versioning.md`.

## SQLite database location

Any app storing its own data in SQLite should let the user relocate that
file (for backup/syncing), not hardcode a fixed path:
[`packages/python/kvg_dblocation`](packages/python/kvg_dblocation) for
Python apps. Electron apps follow Sweeper's `src/main/dbLocation.ts`
directly as the reference pattern — see `db-location-versioning.md`.

## Logo & branding

Every new app repo checks in a source logo (`assets/logo.png`) and generates
every other size/format from it via a one-off `scripts/generate-icons.*`
script — README header, in-app window/taskbar icon, in-app UI usage, and the
packaged binary/installer icon. See the `app-standards` skill's "Logo &
branding" checklist for the full per-surface breakdown. Sweeper
(`scripts/generate-icons.js`, Electron/sharp) and KVGrainy
(`scripts/generate_icons.py`, PyInstaller/Pillow) are the reference
implementations; `release-python-gui.yml`'s `icon_path` input embeds the
generated icon into PyInstaller-built executables.

## Release notes

Every `release-*.yml` build variant prepends install instructions to the
release body (`softprops/action-gh-release`'s `body:` +
`generate_release_notes: true` puts them ahead of the auto-generated
changelog; `release-electron.yml` patches them on afterward since
electron-builder self-publishes). Not retroactive — only releases cut after
a repo picks up the updated workflow get it. See the `app-standards`
skill's "Release notes" section.

## Release workflow catalog

| Workflow | For | Used by |
|---|---|---|
| `release-python-gui.yml` | PyInstaller-packaged Python GUI apps | KVGrainy, KVGroove, kvg_converter |
| `release-go-gui.yml` | Wails (Go) desktop apps | gameshell-deploy (gui/) |
| `release-electron.yml` | Electron desktop apps | sweeper |
| `release-flet.yml` | Flet desktop apps | kvgenius |
| `release-streamdeck.yml` | Elgato Stream Deck plugins (plain Node.js, no compiler) | kvgauge |
| `ci-go.yml` | Go build+vet gate (library or web app) | gameshell-framework, card-judge, timeline-trivia |

There's no `release-go-binary.yml`/similar for plain CLI-only Go apps in
this catalog on purpose: `card-judge` and `timeline-trivia` are Go *web
apps* deployed by [gameshell-deploy](https://github.com/gerp93/gameshell-deploy)
via DigitalOcean App Platform's own GitHub integration (it builds their
`Dockerfile` directly on push) — they have no GitHub-Release-binary release
step at all, just the CI gate above. `gameshell-framework` is a Go
*library*; its "release" is a bare semver tag for `go.mod` pinning
(`templates/cut-tag.yml`), no build artifact either.

## Release triggers: both, always

Every repo with a `release-*.yml` pipeline gets **both**:

- **`templates/auto-release.yml`** — fires on every push to `main`.
  Conventional-commit-driven version bump (`mathieudutour/github-tag-action`),
  no manual step. This is the default, always-on path.
- **`templates/cut-release.yml`** — `workflow_dispatch` with an explicit
  version, for when you want a specific number instead of whatever the
  auto-bump would produce.

Both call the same `release-*.yml` build variant; they just get the version
number differently. Don't ship a repo with only one of the two.

## Adding a new consumer repo

1. Pick the right release workflow from the table above (or note that none
   apply, like the Go-web-app case).
2. Copy **both** `templates/auto-release.yml` and `templates/cut-release.yml`
   into the repo's `.github/workflows/`, filling in the `TODO`s in each.
3. Copy `templates/VERSION_BUMP.md` to the repo root as `VERSION_BUMP.md` —
   the tracked way to force a release with no code change (edit + a dated
   entry) instead of an empty commit.
4. If it's an existing repo with a local release/build workflow already,
   remove that workflow — don't run both.
