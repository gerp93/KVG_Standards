# Rollout TODO

Tracks bringing every in-scope app repo into full alignment on four
things: **theming**, **auto-release-on-push**, **update-check**, and
**licensing**. This is a living checklist — update it as items land, don't
let it go stale.

Scope: the 10 active app repos (KVGrainy, KVGroove, gameshell-deploy,
Sweeper, KVG_Converter, KVGenius, KVGauge, gameshell-framework, card-judge,
timeline-trivia). VisualAssault is the theme producer, not a consumer.
kvgrep is excluded (no code yet).

## Gap matrix

| Repo | Theming | Auto-release-on-push | Update-check | Licensing |
|---|---|---|---|---|
| KVGrainy | ✅ VisualAssault v0.2.0, pinned | ✅ | ✅ migrated to `kvg_updater` (pinned `@main`, no tag yet — see [PR #19](https://github.com/gerp93/KVGrainy/pull/19)) | ✅ AGPL-3.0 |
| KVGroove | ✅ VisualAssault v0.2.0, pinned | ✅ | ✅ `kvg_updater` wired in (pinned `@main`, no tag yet — see [PR #5](https://github.com/gerp93/KVGroove/pull/5)) | ✅ AGPL-3.0 (deps checked: `pygame` LGPL, `mutagen` GPL-2.0-or-later — both fine, see `licensing.md`) |
| gameshell-deploy (Wails GUI) | ✅ VisualAssault, hand-transcribed, tokens current | ✅ | ❌ **gap** — add `kvgupdate` (new, unverified against a real build — see its README) | ❌ **gap** — no `LICENSE` file, see [PR TODO below](#gameshell-deploy-wails-gui) |
| Sweeper (Electron) | ⚠️ **stale vendor** — byte-copy of VisualAssault CSS missing `surface`/`border`/`textMuted`/`accentMuted` (pre-v0.2.0 snapshot, same drift class already fixed in gameshell-framework) | ✅ | ✅ already best-in-class (`electron-updater`, wired up) — reference implementation for future Electron apps | ❌ **gap** — no `LICENSE` file |
| KVG_Converter | ✅ VisualAssault v0.2.0, pinned — see [PR #5](https://github.com/gerp93/KVG_Converter/pull/5) | ✅ | ✅ `kvg_updater` wired in (pinned `@main`, no tag yet — see [PR #5](https://github.com/gerp93/KVG_Converter/pull/5)) | ✅ AGPL-3.0 |
| KVGenius (Flet) | ✅ VisualAssault v0.2.0, pinned — see [PR #7](https://github.com/gerp93/KVGenius/pull/7) | ✅ | ✅ `kvg_updater` bundle mode wired in (pinned `@main`, no tag yet — see [PR #7](https://github.com/gerp93/KVGenius/pull/7)); **not yet verified against a real `flet build` output** | ❌ **gap** — no `LICENSE` file (deps checked: torch/transformers/diffusers/accelerate/safetensors/peft are BSD/Apache-2.0, bitsandbytes/flask MIT/BSD, flet Apache-2.0 — all fine) |
| KVGauge (Stream Deck plugin) | N/A? — needs a decision, see below | ✅ | **N/A by design** — Stream Deck plugins reinstall via `.streamDeckPlugin`/Marketplace, not self-update | ✅ AGPL-3.0 |
| gameshell-framework (Go library) | ✅ fixed this session (vendored VisualAssault CSS, re-vendor script) — covers card-judge + timeline-trivia too | N/A by design (tag-only release for `go.mod` pinning) | N/A (server-side, no client to update) | ✅ AGPL-3.0 |
| card-judge | ✅ (inherits from gameshell-framework) | N/A by design (deployed via gameshell-deploy/DO, not a release binary) | N/A | ✅ AGPL-3.0 |
| timeline-trivia | ✅ (inherits from gameshell-framework) | N/A by design | N/A | ✅ AGPL-3.0 |

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
  modules, npm frontend deps) checked, all MIT/BSD, no blocker.

### Sweeper
- [ ] Re-vendor `src/renderer/themes.css` from VisualAssault
  `packages/css/themes.css` @ `v0.2.0` (same fix already applied to
  gameshell-framework's `colors.css`). Simpler here than
  gameshell-framework's case: no "Classic" section to preserve — the whole
  file is VisualAssault content, so this can be a straight overwrite.
- [ ] Add a header comment noting the source tag.
- [ ] Update-check: nothing to do, already best-in-class.
- [ ] Add `LICENSE` (AGPL-3.0) — no license file exists. Deps (Electron,
  React, sql.js, etc.) checked, all MIT, no blocker.

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
- [ ] Add `LICENSE` (AGPL-3.0) — no license file exists. ML deps checked
  (torch, transformers, diffusers, accelerate, safetensors, peft are
  BSD/Apache-2.0; bitsandbytes/flask MIT/BSD; flet Apache-2.0), no blocker.

### KVGauge (Stream Deck plugin)
- [ ] **Needs a decision, not just an implementation** on theming: does a
  Stream Deck plugin's property inspector (`propertyinspector.html`) even
  want a VisualAssault theme, given Stream Deck has its own UI
  chrome/conventions? Update-check is already resolved as N/A (see gap
  matrix) — recommend treating theming the same way (out of scope) unless
  there's a specific reason to want it.

## Open questions (theming)

1. Should the CSS re-vendor script (`gameshell-framework/scripts/update-visual-assault-css.sh`)
   move into `KVG_Standards` as a shared, parameterized script (taking a
   target file path as an argument) instead of living per-repo? Sweeper and
   gameshell-deploy's `gui/frontend` would both want it too.
2. KVGauge theming scope decision (see above).
