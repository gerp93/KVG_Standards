# Repo scope

A reference matrix of which KVG_Standards standards apply to each active
app repo. Cells reflect **scope** (does this standard apply to this repo,
based on its category — see the `app-standards` skill's "Release / CI
pipeline" table) not verified current compliance — this pass didn't
re-check every repo's actual state. Treat this as the map of what *should*
be true; a future session should periodically re-audit each repo against
it, note actual compliance/drift here (or back in a per-standard section
below), and keep it current as repos are added, retired, or reclassified.

Scope: the 10 active app repos (KVGrainy, KVGroove, gameshell-deploy,
Sweeper, KVG_Converter, KVGenius, KVGauge, gameshell-framework, card-judge,
timeline-trivia). VisualAssault is the theme producer, not a consumer.
kvgrep is excluded (no code yet).

## Scope matrix

| Repo | Category | Theming | Licensing | Update-check | Logo & branding | Release notes | VERSION_BUMP.md | DB location | TODO.md |
|---|---|---|---|---|---|---|---|---|---|
| KVGrainy | Python/PyInstaller GUI | Yes | Yes | Yes | Yes | Yes | Yes | N/A | Yes |
| KVGroove | Python/PyInstaller GUI | Yes | Yes | Yes | Yes | Yes | Yes | N/A | Yes |
| gameshell-deploy (`gui/`) | Go/Wails GUI | Yes | Yes | Yes | Yes | Yes | Yes | N/A | Yes |
| Sweeper | Electron GUI | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| KVG_Converter | Python/PyInstaller GUI | Yes | Yes | Yes | Yes | Yes | Yes | N/A | Yes |
| KVGenius | Flet GUI | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| KVGauge | Stream Deck plugin | TBD — needs a decision, see below | Yes | N/A by design | TBD — plugin has its own icon conventions (manifest.json), see below | Yes | Yes | N/A | Yes |
| gameshell-framework | Go library | Yes (vendored CSS, covers card-judge + timeline-trivia) | Yes | N/A | N/A — library, no shipped app surface | N/A — tag-only release, no build | N/A | N/A | Yes |
| card-judge | Go web app | Yes (inherits from gameshell-framework) | Yes | N/A — deployed via DO push, no client binary | TBD — web app, desktop icon surfaces don't apply but a README/site logo might | N/A — CI gate only, no release pipeline | N/A | TBD — unknown if it uses SQLite | Yes |
| timeline-trivia | Go web app | Yes (inherits from gameshell-framework) | Yes | N/A | TBD — no `assets/logo.png`/README hero image, only a `favicon.png`; low priority per web-app category | N/A | N/A | N/A — uses MariaDB (server-side, `go-sql-driver/mysql`), not SQLite | Yes |

**Licensing standard now exists** — [`licensing.md`](licensing.md): AGPL-3.0
by default, checked against each repo's actual dependencies (a dependency
under a GPL-2.0-only, non-commercial, or otherwise incompatible license
would block it — none found anywhere in this audit). VisualAssault and
KVG_Standards itself are both AGPL-3.0 too.

**Update-check standard now exists** — [`packages/python/kvg_updater`](packages/python/kvg_updater)
and [`packages/go/kvgupdate`](packages/go/kvgupdate), documented in
`update-check-versioning.md` and enforced via the `app-standards` skill.
The rest of this doc's per-repo items reflect that; the old "needs design"
section is gone.

## Action items by repo

Detailed findings/history from the last real audit pass (theming,
update-check, licensing, DB location) — predates the scope matrix above and
hasn't been re-verified against the newer standards (logo & branding,
release notes, VERSION_BUMP.md, TODO.md). Useful context, not current truth
— re-check before trusting a ✅/❌ here.

### KVGrainy
- [x] Migrate `updater.py` to a thin wrapper around `kvg_updater` — see
  [PR #19](https://github.com/gerp93/KVGrainy/pull/19). Pinned `@main`
  (KVG_Standards has no tagged releases yet, see
  `update-check-versioning.md`'s interim-exception note); switch to a tag
  once one exists.

### KVGroove
- [x] Added `kvg-updater` (`@main`, no tag yet), an `updater.py` wrapper,
  and a "Check for Updates..." Help-menu entry + startup check — see
  [PR #5](https://github.com/gerp93/KVGroove/pull/5). Also fixed a missing
  `version_file: _version.py` on both release workflows in the same PR
  (without it, `CURRENT_VERSION` could never resolve past `"0.0.0-dev"`).

### gameshell-deploy (Wails GUI)
- [ ] Add `github.com/gerp93/KVG_Standards/packages/go/kvgupdate` (pinned
  tag) to `gui/go.mod`.
- [ ] Wire `kvgupdate.CheckForUpdate` / `DownloadAndExtract` /
  `ApplyUpdateAndRestart` into the app (see that package's README).
- [ ] **Before relying on this**: verify it against a real tagged release —
  the package's extract/replace path has not been run end-to-end yet. Test
  on all three OSes if possible, Windows especially (the self-delete-batch
  trick is the fiddliest part).
- [ ] Optional polish: add a version-pin comment + re-vendor script for
  `gui/frontend/src/themes.css`, matching the gameshell-framework/Sweeper
  convention, even though it isn't currently stale.
- [ ] Add `LICENSE` (AGPL-3.0) — no license file exists. Deps (Wails, Go
  modules, npm frontend deps) checked, all MIT/BSD, no blocker. PR open:
  [gameshell-deploy #12](https://github.com/gerp93/gameshell-deploy/pull/12).

### Sweeper
- [x] Re-vendored `src/renderer/themes.css` from VisualAssault
  `packages/css/themes.css` @ `v0.2.0` — see
  [PR #18](https://github.com/gerp93/Sweeper/pull/18) (draft). The old copy
  was confirmed stale: missing `--color-surface`/`--color-border`/
  `--color-text-muted`/`--color-accent-muted` on all 14 theme blocks, and
  had no header comment. Straight overwrite (no "Classic" section here,
  unlike gameshell-framework's `colors.css`); header comment now cites the
  source tag.
- [x] Update-check: confirmed already best-in-class (`electron-updater` in
  `src/main/main.ts`) — nothing to do.
- [x] Added `LICENSE` (AGPL-3.0) — see [PR #17](https://github.com/gerp93/Sweeper/pull/17), merged.
- [x] Already has a working SQLite relocate feature (`src/main/dbLocation.ts`)
  — this became the reference pattern written up in
  `db-location-versioning.md`. Nothing to do here.
- [x] Re-checked newer standards (2026-08-07 audit), all now fixed in
  [PR #18](https://github.com/gerp93/Sweeper/pull/18) (draft):
  neither `README.md` nor a `CLAUDE.md` mentioned KVG_Standards at all
  (violation of "docs must point back here"); README was missing the logo
  image and described a removed `.github/workflows/build.yml` instead of
  the current `auto-release.yml`/`cut-release.yml`; `TODO.md` and
  `VERSION_BUMP.md` were both missing despite `auto-release.yml` being
  present; `package.json` still declared `"license": "MIT"` despite the
  AGPL-3.0 `LICENSE` file. Logo & branding and release-notes patch job were
  otherwise already fully wired (window icon, sidebar, packaged-binary
  icon, `release-electron.yml`'s `release-notes` job) — no gap there.

### KVG_Converter
- [x] Added `visual-assault-tkinter` + a theme picker (`theming.py`,
  adapted for plain `tk` widgets rather than `ttk` since this UI doesn't
  use `ttk`), plus `kvg-updater` + an `updater.py` wrapper and a Help
  menu — see [PR #5](https://github.com/gerp93/KVG_Converter/pull/5).
  Not exercised live (no `tkinter`/display in the dev environment used);
  verify the theme picker and update flow manually before merging.

### KVGenius
- [x] Removed the dead `flet_kvg_themes` import, added VisualAssault's
  `packages/flet` (pinned `@v0.2.0`), and wired `kvg_updater`'s bundle mode
  in — see [PR #7](https://github.com/gerp93/KVGenius/pull/7). Also fixed
  a real bug found along the way: `ft.ColorScheme(background=...)` isn't
  valid on flet 0.86.x (filed upstream: [VisualAssault#8](https://github.com/gerp93/VisualAssault/pull/8)),
  and added `release-flet.yml`'s missing `version_file` input (this repo).
- [ ] **Still open**: verify the update-check against a real `flet build`
  output. Confirm `Path(sys.executable).resolve().parent` actually points
  at the bundle root, and that `_find_bundle_binary`'s per-platform lookup
  finds the right executable for the Flet version in use, before relying
  on this in production.
- [x] Added `LICENSE` (AGPL-3.0) — see [PR #8](https://github.com/gerp93/KVGenius/pull/8), merged.
- [ ] Wire `kvg_dblocation` into `src/database/chat_history.py`, which
  currently hardcodes `db_path: str = "./chat_history.db"` — a relative
  path with no way for the user to relocate it. Reuse `core.CACHE_DIR`'s
  parent as the data directory (don't invent a second convention). Add a
  Database Location section to the Settings tab (existing-file picker,
  new-location picker, reset-to-default), same shape as Sweeper's. See
  `db-location-versioning.md`.

### KVGauge (Stream Deck plugin)
- [ ] **Needs a decision, not just an implementation** on theming: does a
  Stream Deck plugin's property inspector (`propertyinspector.html`) even
  want a VisualAssault theme, given Stream Deck has its own UI
  chrome/conventions? Update-check is already resolved as N/A (see gap
  matrix) — recommend treating theming the same way (out of scope) unless
  there's a specific reason to want it.

### timeline-trivia
- [x] Compliance audit (2026-08-07): CI (`ci-go.yml@main`, `working_directory: src`)
  matches `templates/ci.yml` exactly, no vestigial release-binary workflow
  present — deploy confirmed via `gameshell-deploy`/DO App Platform push
  (README's own "Deployment" section). Theming confirmed inherited from
  `gameshell-framework`'s vendored CSS (`/gs/` mount via
  `gsBootstrap.MountStaticAssets`) — no local `colors.css`/hand-rolled
  palette. Licensing: `LICENSE` present (AGPL-3.0, matches boilerplate),
  dependencies (`gameshell-framework`, `google/uuid`, `gorilla/websocket`,
  `go-sql-driver/mysql`, `golang.org/x/crypto`) all permissive/MPL-2.0, no
  blocker. DB location: confirmed MariaDB (server-side), standard doesn't
  apply. Found and fixed missing `TODO.md` and docs never mentioning
  KVG_Standards — see
  [PR #3](https://github.com/gerp93/timeline-trivia/pull/3) (draft).
  Logo/branding gap noted in the matrix above but left as-is (low
  priority per web-app category, no fix implemented).

## Open questions (theming)

1. Should the CSS re-vendor script (`gameshell-framework/scripts/update-visual-assault-css.sh`)
   move into `KVG_Standards` as a shared, parameterized script (taking a
   target file path as an argument) instead of living per-repo? Sweeper and
   gameshell-deploy's `gui/frontend` would both want it too.
2. KVGauge theming scope decision (see above).
