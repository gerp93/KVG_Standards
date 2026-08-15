# Repo scope

A reference matrix of which KVG_Standards standards apply to each active
app repo. Cells reflect **scope** (does this standard apply to this repo,
based on its category — see the `app-standards` skill's "Release / CI
pipeline" table) not verified current compliance — this pass didn't
re-check every repo's actual state. Treat this as the map of what *should*
be true; a future session should periodically re-audit each repo against
it, note actual compliance/drift here (or back in a per-standard section
below), and keep it current as repos are added, retired, or reclassified.

Scope: the 13 active app repos (KVGrainy, KVGroove, gameshell-deploy,
Sweeper, KVG_Converter, KVGenius, KVGauge, gameshell-framework, card-judge,
timeline-trivia, TrackDraft, airport, KVG_RGB). VisualAssault is the theme
producer, not a consumer. kvgrep is excluded (no code yet).

## Scope matrix

| Repo | Category | Theming | Licensing | Update-check | Logo & branding | Release notes | VERSION_BUMP.md | DB location | TODO.md |
|---|---|---|---|---|---|---|---|---|---|
| KVGrainy | Python/PyInstaller GUI | Yes | Yes | Yes | Yes | Yes | Yes | N/A | Yes |
| KVGroove | Python/PyInstaller GUI | Yes | Yes | Yes | Yes | Yes | Yes | N/A | Yes |
| gameshell-deploy (`gui/`) | Go/Wails GUI | Yes | Yes | Yes | Yes | Yes | Yes | N/A | Yes |
| Sweeper | Electron GUI | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| KVG_Converter | Python/PyInstaller GUI | Yes | Yes | Yes | Yes | Yes | Yes | N/A | Yes |
| KVGenius | Flet GUI | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| KVGauge | Stream Deck plugin | TBD — needs a decision, see below | Yes | N/A by design | N/A-shaped — plugin uses its own `manifest.json` icon conventions, not the generic checklist; already populated | Yes | Yes | N/A | Yes |
| gameshell-framework | Go library | Yes (vendored CSS, covers card-judge + timeline-trivia) | Yes | N/A | N/A — library, no shipped app surface | N/A — tag-only release, no build | N/A | N/A | Yes |
| card-judge | Go web app | Yes (inherits from gameshell-framework) | Yes | N/A — deployed via DO push, no client binary | TBD — only a favicon, no `assets/logo.png`; low priority per web-app category | N/A — CI gate only, no release pipeline | N/A | N/A — uses MariaDB (server-side), not SQLite | Yes |
| timeline-trivia | Go web app | Yes (inherits from gameshell-framework) | Yes | N/A | TBD — no `assets/logo.png`/README hero image, only a `favicon.png`; low priority per web-app category | N/A | N/A | N/A — uses MariaDB (server-side, `go-sql-driver/mysql`), not SQLite | Yes |
| TrackDraft | Electron GUI | Yes | Yes | Yes | TBD — no `assets/logo.png` at all; `main.ts` references a nonexistent icon | Yes | Yes | Yes | Yes |
| airport | Godot game | Not yet covered (see `game-repos.md`) | Yes | Yes (`packages/godot/kvg_update`, vendored, notify-only) | Not yet covered (see `game-repos.md`) | Yes | Yes | N/A | Yes |
| KVG_RGB | Python CLI + Flask web app — no existing category match, see below | No — hand-rolled CSS palette, not VisualAssault | TBD — declares MIT in `pyproject.toml`, no `LICENSE` file; needs reconciliation against the AGPL-3.0 default | No — no update-check wired at all | No — no logo/icon assets anywhere | N/A — no CI/release pipeline exists (no `.github/workflows`) | No — missing | No — SQLite at a hardcoded path, no relocate/adopt/reset UI | Partial — has a `TODO.md`, predates and doesn't follow the KVG_Standards format |

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

Detailed findings/history, including the full 2026-08-07 sweep that
re-audited all 11 active repos (and discovered TrackDraft, previously
untracked) against every standard. Draft PRs are open per-repo for every
mechanical fix found; items still needing a human decision are marked
`[ ]` with an explicit note.

### KVGrainy
- [x] Migrate `updater.py` to a thin wrapper around `kvg_updater` — see
  [PR #19](https://github.com/gerp93/KVGrainy/pull/19). Pinned `@main`
  (KVG_Standards has no tagged releases yet, see
  `update-check-versioning.md`'s interim-exception note); switch to a tag
  once one exists.
- [x] **2026-08-07 re-audit**: full checklist re-verified, fully compliant.
  Theming pinned `@v0.2.0` (tag, not `@main`); logo & branding passes the
  entire placement checklist (source mark, generated icons via a checked-in
  script, README hero, in-app window icon, in-app UI usage, packaged-binary
  icon); `TODO.md`/`VERSION_BUMP.md` present; `CLAUDE.md` explicitly states
  it follows KVG_Standards. No PR needed — this repo is a clean reference
  implementation (cited by name in the `app-standards` skill for its
  icon-generation and window-icon patterns).

### KVGroove
- [x] Added `kvg-updater` (`@main`, no tag yet), an `updater.py` wrapper,
  and a "Check for Updates..." Help-menu entry + startup check — see
  [PR #5](https://github.com/gerp93/KVGroove/pull/5). Also fixed a missing
  `version_file: _version.py` on both release workflows in the same PR
  (without it, `CURRENT_VERSION` could never resolve past `"0.0.0-dev"`).
- **2026-08-07 re-audit** — [PR #6](https://github.com/gerp93/KVGroove/pull/6) (draft):
  - [x] Added missing `TODO.md` and `VERSION_BUMP.md`, added a README
    pointer stating the repo follows KVG_Standards (previously absent).
  - [ ] **Needs a human decision**: logo & branding fails the full
    placement checklist — no `assets/logo.png` anywhere;
    `ui/main_window.py:38` calls `self.root.iconbitmap("icon.ico")` on a
    file that doesn't exist (silently swallowed by `try/except`, so no
    window icon is actually set); no in-app logo usage; no `icon_path`
    passed to `release-python-gui.yml` in either workflow. Needs a real
    source mark designed before the KVGrainy-style icon plumbing can be
    wired in.

### gameshell-deploy (Wails GUI)
- [x] Added `github.com/gerp93/KVG_Standards/packages/go/kvgupdate` (pinned
  `@main`, interim exception) to `gui/go.mod`, wired via
  `App.CheckForUpdate`/`ApplyUpdate` + a header button — see
  [PR #13](https://github.com/gerp93/gameshell-deploy/pull/13) (draft).
  `go build`, `wails generate module`, and `tsc --noEmit` all verified
  clean.
- [ ] **Before relying on this**: verify it against a real tagged release —
  the package's extract/replace path has not been run end-to-end yet. Test
  on all three OSes if possible, Windows especially (the self-delete-batch
  trick is the fiddliest part).
- [ ] **New gap found (needs a design decision)**: `release-go-gui.yml` has
  no version-stamping mechanism (unlike Python's `version_file` input), so
  `CheckForUpdate` will report "up to date" forever until that shared
  workflow gets one — this is a KVG_Standards-side change, not something to
  patch locally in gameshell-deploy.
- [x] Added a version-pin comment + `gui/scripts/update-visual-assault-css.mjs`
  re-vendor script for `gui/frontend/src/themes.css` (values were already
  byte-identical to VisualAssault `@v0.2.0`, now formally vendored/pinned)
  — same PR #13.
- [ ] Add `LICENSE` (AGPL-3.0) — no license file exists yet. Deps (Wails, Go
  modules, npm frontend deps) checked, all MIT/BSD, no blocker. PR still
  open: [gameshell-deploy #12](https://github.com/gerp93/gameshell-deploy/pull/12)
  (confirmed open as of the 2026-08-07 re-audit; not duplicated).
- [x] **2026-08-07 re-audit**, same PR #13: added missing `TODO.md`/
  `VERSION_BUMP.md`; added a README "Standards" section (previously no
  mention of KVG_Standards anywhere); fixed stale docs (`CLAUDE.md`
  described releases as manual-only, predating `auto-release.yml`;
  `gui/README.md` referenced a since-removed `release.yml`).
- [ ] **Needs a human decision**: logo & branding — no `assets/logo.png` or
  any icon surface wired at all. Needs a real source mark, not fabricated.

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
- **2026-08-07 re-audit** — [PR #6](https://github.com/gerp93/KVG_Converter/pull/6) (draft):
  - [x] Statically re-verified PR #5's theming/updater wiring (theme keys
    resolve against `visual_assault_tkinter.THEMES`; `updater.py`'s calls
    match `kvg_updater`'s real API) — still not run against a real display,
    that verification remains outstanding.
  - [x] Added missing `TODO.md` and `VERSION_BUMP.md`; added a
    KVG_Standards pointer paragraph to README (previously absent).
  - [ ] **Needs a human decision**: logo & branding entirely absent — no
    `assets/logo.png`, no icon-generation script, no in-app window icon, no
    packaged-binary icon (`icon_path` unset in both release workflows).
    From-scratch design gap, not a mechanical fix.

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
- **2026-08-07 re-audit** — [PR #9](https://github.com/gerp93/KVGenius/pull/9) (draft):
  - [x] Wired `kvg_dblocation` into `src/database/chat_history.py` (pinned
    `@main`, interim exception), reusing `core.CACHE_DIR`'s parent as the
    data directory. Added a Database Location section to the Settings tab
    (choose existing file, choose new location, reset to default, restart
    prompt) — same shape as Sweeper's.
  - [x] **Found and fixed a real bug**: the update-check wiring claimed
    done in PR #7 only existed in `ui/tabs/settings.py`, which is dead code
    — `desktop_app.py` (the actual `release-flet.yml` entry point) never
    imported `updater.py` at all, and its own `SettingsTab` had no
    version/check-updates UI, so `main()`'s
    `settings_tab.check_for_updates_silently()` call raised `AttributeError`
    in a background thread on every launch. Ported the working
    implementation into `desktop_app.py`'s real `SettingsTab`.
  - [ ] **Still open**: live verification of update-check against a real
    `flet build` output (needs a display/build toolchain) — unchanged from
    before.
  - [x] Fixed README: added a KVG_Standards back-link (previously absent)
    and corrected the License section (said "Open source for educational
    purposes", contradicting the AGPL-3.0 `LICENSE` file).
  - [x] Added missing `VERSION_BUMP.md` and `TODO.md`.
  - [ ] **Needs a human decision**: no `assets/logo.png` or any icon
    anywhere in the repo (no README image, no window/taskbar icon, no
    packaged-binary icon) — needs real artwork, not fabricated by an
    automated pass.
  - Repo-health note (not a standards item, not fixed): `ui/tabs/chat.py`,
    `ui/tabs/settings.py`, `ui/tabs/prompts.py` are dead code — unused
    duplicate `ChatTab`/`SettingsTab`/`PromptLibraryTab` classes shadowed
    by `desktop_app.py`'s own local versions. This is how the update-check
    bug above went unnoticed. Worth deciding whether to delete or
    consolidate.

### KVGauge (Stream Deck plugin)
- [ ] **Needs a decision, not just an implementation** on theming: does a
  Stream Deck plugin's property inspector (`propertyinspector.html`) even
  want a VisualAssault theme, given Stream Deck has its own UI
  chrome/conventions? Update-check is already resolved as N/A (see gap
  matrix) — recommend treating theming the same way (out of scope) unless
  there's a specific reason to want it.
  **2026-08-07 detail**: `propertyinspector.html` currently uses a
  hand-rolled dark palette (`#2d2d2d` bg, `#d8d8d8` text, `#3a3a3a` inputs,
  `#0e7cff` focus blue) — it's styled, just not via VisualAssault. Decision
  needed: adopt VisualAssault, keep the hand-rolled palette deliberately, or
  formally mark theming out-of-scope like update-check.
- [x] **2026-08-07 re-audit** — [PR #5](https://github.com/gerp93/KVGauge/pull/5) (draft):
  licensing (AGPL-3.0, deps clean), release pipeline (`auto-release.yml` +
  `cut-release.yml` calling `release-streamdeck.yml`), and release notes
  were already compliant. `manifest.json`'s icon fields (CategoryIcon,
  Icon, per-action icons) are populated and valid — Stream Deck's own icon
  convention, not the generic desktop checklist. Fixed: `TODO.md` and
  `VERSION_BUMP.md` were both missing despite the matrix saying "Yes";
  README never mentioned KVG_Standards.

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

### card-judge
- Fork status checked: GitHub lists it as a fork of `GrantFBarnes/card-judge`
  (unrelated original author; module path confirms it) — legitimate
  history, not a stray fork. gerp93 forked a standalone game and grew it
  into the first gameshell-framework consumer before the framework was
  later extracted out.
- [x] **2026-08-07 audit** — [PR #14](https://github.com/gerp93/card-judge/pull/14)
  (draft, based on `f-framework-breakout`, the repo's actual default branch
  — `main` predates the in-flight framework migration in open PR #12). CI
  (`ci.yml` → `ci-go.yml@main`) compliant, no vestigial release-binary
  workflow to remove. Theming confirmed inherited from gameshell-framework's
  vendored CSS (no hex/rgb colors or `--color-*` tokens in card-judge's own
  CSS) — correct inheritance, not a duplicated palette. Licensing
  compliant. DB location resolved: MariaDB (server-side, `CARD_JUDGE_SQL_*`
  env vars), no SQLite anywhere — standard doesn't apply (matrix updated
  from TBD to N/A). Fixed: missing `TODO.md`; README/CLAUDE.md only
  mentioned `gameshell-framework` in passing, added explicit KVG_Standards
  pointers.
- [ ] Logo gap noted (only a favicon, no `assets/logo.png`) — low priority
  per web-app category, not fixed.
- [ ] Orphaned cruft flagged, not removed: `version_bump.sh` and a stale
  `CLAUDE.md` line both reference a `release.yml` that doesn't exist in
  this repo — didn't want to blind-delete something possibly still
  referenced externally; needs a human look.

### gameshell-framework
- [x] **2026-08-07 audit** — [PR #4](https://github.com/gerp93/gameshell-framework/pull/4)
  (draft). Theming: vendored `colors.css` diffed against VisualAssault's
  actual latest tag (`v0.2.0`) — content-identical (only block order
  differs), not stale; the framework-native "Classic" section correctly
  preserved untouched. Licensing compliant (AGPL-3.0, deps all
  MPL-2.0/BSD, no blocker). Release/CI was non-compliant: repo carried a
  hand-rolled `version_bump.sh` + `version-bump.yml` (reimplementing
  tag-bump logic, also mutating a `README.md` version line) plus a
  vestigial `release.yml` (build+vet+empty GitHub Release) that a Go
  library doesn't need per the standard. Replaced with `templates/cut-tag.yml`
  verbatim; `go build ./...`/`go vet ./...` verified clean. Also fixed:
  missing `TODO.md`; README/CLAUDE.md only mentioned KVG_Standards
  incidentally for theming, added explicit pointers.
- No items left needing a human decision — everything found had a clear
  mechanical fix, all landed in PR #4.

### TrackDraft
- **Not previously tracked in this file** — discovered during the
  2026-08-07 sweep. It's a real, mature Electron desktop app (React/Vite
  renderer, sql.js SQLite DB, Claude/Ollama-assisted lyric writing), not a
  stub like kvgrep — added to the scope matrix above as an Electron GUI
  app, same category as Sweeper.
- [x] Already compliant on: theming (VisualAssault CSS vendored & pinned
  `@v0.2.0`), licensing (AGPL-3.0, all deps MIT/BSD/Apache-2.0), release/CI
  (`auto-release.yml`+`cut-release.yml` → `release-electron.yml@main`),
  update-check (`electron-updater` directly), DB location
  (`src/main/dbLocation.ts` + `Settings.tsx` already implement the full
  relocate/adopt/reset UI, matching Sweeper's reference shape).
- [x] Fixed — [PR #1](https://github.com/gerp93/TrackDraft/pull/1) (draft):
  added a `CLAUDE.md` "Standards" section (repo had zero docs mentioning
  KVG_Standards); added missing `TODO.md` and `VERSION_BUMP.md`.
- [ ] **Needs a human decision**: logo & branding entirely absent — no
  `assets/logo.png` exists; `main.ts` references a nonexistent
  `assets/icon.png` for the window icon; no packaged-installer icon in
  `package.json`'s `build` config. Needs a real source mark before any
  icon plumbing can be added.

### airport (Godot game)
- [x] Release/CI: `auto-release.yml` + `cut-release.yml` both call
  `release-godot.yml@main` correctly. `VERSION_BUMP.md` present.
- [x] Update-check: `addons/kvg_update/kvg_update.gd` vendored via
  `scripts/update-kvg-update.sh`, pin comment present. `LICENSE`
  (AGPL-3.0), `TODO.md`, and docs linking back to KVG_Standards all
  present.
- [ ] Theming and icon generation are open gaps, not a violation — Godot
  isn't covered for either yet (see `game-repos.md`). Prototype has no art
  assets, so not currently blocking.
- Audited 2026-08-10 following the `release-godot.yml`/
  `packages/godot/kvg_update` addition on 2026-08-09.

### KVG_RGB
- **Not previously tracked in this file** — added to scope 2026-08-15 after
  the `app-standards` skill was found to mischaracterize it (see open
  question below). It's a real, separate app: an OpenRGB device controller
  (Python CLI + Flask web UI + Windows installer/exe), unrelated to
  VisualAssault/UI theming despite the name.
- Audited 2026-08-15 (repo inspection only, no fixes applied — none of this
  repo's gaps have a clean mechanical fix given the open category/pipeline
  question below):
  - Theming: `kvg_rgb/static/style.css` is a hand-rolled dark palette
    (`--primary-color: #6366f1` etc.), not VisualAssault.
  - Licensing: `pyproject.toml` declares `license = {text = "MIT"}` but
    there's no `LICENSE` file in the repo at all. Every other repo defaults
    to AGPL-3.0; reconciling this needs the dependency check `licensing.md`
    describes (starting with `openrgb-python`) before picking a license.
  - Update-check: none. Distribution is a hand-rolled `installer.py` /
    `build_installer.py` / `release.py`, not `kvg_updater` or a KVG_Standards
    release workflow.
  - Release/CI: no `.github/workflows` directory exists — no CI, no
    automated release, nothing to compare against `templates/`.
  - Logo & branding: no `assets/logo` or icon anywhere.
  - VERSION_BUMP.md: missing. Version is hardcoded in
    `kvg_rgb/__init__.py` (`__version__ = "0.1.2"`).
  - DB location: SQLite, but hardcoded to `~/.kvg_rgb/rgb_controller.db`
    (`kvg_rgb/paths.py`) — no relocate/adopt/reset UI like Sweeper's
    reference pattern.
  - TODO.md: exists, but predates this repo's addition to scope and doesn't
    follow the KVG_Standards TODO.md template.
  - Repo has had no commits since 2025-10-18 (~10 months) — worth
    confirming with the human whether this is active or dormant before
    investing in bringing it into compliance.

## Open questions (theming)

1. Should the CSS re-vendor script (`gameshell-framework/scripts/update-visual-assault-css.sh`)
   move into `KVG_Standards` as a shared, parameterized script (taking a
   target file path as an argument) instead of living per-repo? Sweeper and
   gameshell-deploy's `gui/frontend` would both want it too.
2. KVGauge theming scope decision (see above).

## Open questions (KVG_RGB)

1. **The `app-standards` skill mischaracterizes this repo.** It lists
   `KVG_RGB` alongside `KVG_Themes`/`KVG_Themes_Flet` as an old,
   superseded *theme* dependency to flag as a violation. That's wrong —
   KVG_RGB is an OpenRGB lighting-device controller with no relationship to
   UI theming; the name is a coincidence (RGB lighting hardware, not
   red/green/blue theme colors). This should be corrected so future audits
   don't misfile it.
2. **No pipeline category fits.** Existing categories are native GUI
   (Python/PyInstaller, Flet, Electron, Wails) or a Go web app inheriting
   gameshell-framework's CSS. KVG_RGB is a CLI + Flask web UI packaged as a
   Windows installer/exe — closest to the Python/PyInstaller shape for
   packaging, but has a web UI like the Go web apps for theming. Per
   `CLAUDE.md`'s "New tech stacks" process, this needs a designed standard
   (which release/CI template applies, whether the Flask UI adopts
   VisualAssault's CSS package the way card-judge/timeline-trivia do)
   before any of the gaps above get mechanically fixed.
3. Confirm repo is still active (no commits since 2025-10-18) before
   prioritizing compliance work here.
