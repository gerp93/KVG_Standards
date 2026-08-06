# Rollout TODO

Tracks bringing every in-scope app repo into full alignment on three
things: **theming**, **auto-release-on-push**, and **update-check**. This
is a living checklist — update it as items land, don't let it go stale.

Scope: the 10 active app repos (KVGrainy, KVGroove, gameshell-deploy,
Sweeper, KVG_Converter, KVGenius, KVGauge, gameshell-framework, card-judge,
timeline-trivia). VisualAssault is the theme producer, not a consumer.
kvgrep is excluded (no code yet).

## Gap matrix

| Repo | Theming | Auto-release-on-push | Update-check |
|---|---|---|---|
| KVGrainy | ✅ VisualAssault v0.2.0, pinned | ✅ | ✅ migrated to `kvg_updater` (pinned `@main`, no tag yet — see [PR #19](https://github.com/gerp93/KVGrainy/pull/19)) |
| KVGroove | ✅ VisualAssault v0.2.0, pinned | ✅ | ✅ `kvg_updater` wired in (pinned `@main`, no tag yet — see [PR #5](https://github.com/gerp93/KVGroove/pull/5)) |
| gameshell-deploy (Wails GUI) | ✅ VisualAssault, hand-transcribed, tokens current | ✅ | ❌ **gap** — add `kvgupdate` (new, unverified against a real build — see its README) |
| Sweeper (Electron) | ⚠️ **stale vendor** — byte-copy of VisualAssault CSS missing `surface`/`border`/`textMuted`/`accentMuted` (pre-v0.2.0 snapshot, same drift class already fixed in gameshell-framework) | ✅ | ✅ already best-in-class (`electron-updater`, wired up) — reference implementation for future Electron apps |
| KVG_Converter | ❌ **gap** — plain Tkinter GUI, no theming at all | ✅ | ❌ **gap** — add `kvg_updater` |
| KVGenius (Flet) | ⚠️ **broken** — imports `flet_kvg_themes` (an old, non-VisualAssault package) which isn't even in `requirements.txt`; theming silently no-ops to a hardcoded dark mode | ✅ | ⚠️ **design resolved, not yet wired in** — `kvg_updater` now has a bundle mode for Flet's directory-shaped build output; needs wiring into KVGenius and verification against a real `flet build`, see `packages/python/kvg_updater/README.md` |
| KVGauge (Stream Deck plugin) | N/A? — needs a decision, see below | ✅ | **N/A by design** — Stream Deck plugins reinstall via `.streamDeckPlugin`/Marketplace, not self-update |
| gameshell-framework (Go library) | ✅ fixed this session (vendored VisualAssault CSS, re-vendor script) — covers card-judge + timeline-trivia too | N/A by design (tag-only release for `go.mod` pinning) | N/A (server-side, no client to update) |
| card-judge | ✅ (inherits from gameshell-framework) | N/A by design (deployed via gameshell-deploy/DO, not a release binary) | N/A |
| timeline-trivia | ✅ (inherits from gameshell-framework) | N/A by design | N/A |

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

### Sweeper
- [ ] Re-vendor `src/renderer/themes.css` from VisualAssault
  `packages/css/themes.css` @ `v0.2.0` (same fix already applied to
  gameshell-framework's `colors.css`). Simpler here than
  gameshell-framework's case: no "Classic" section to preserve — the whole
  file is VisualAssault content, so this can be a straight overwrite.
- [ ] Add a header comment noting the source tag.
- [ ] Update-check: nothing to do, already best-in-class.

### KVG_Converter
- [ ] Add `visual-assault-tkinter` (pinned tag) to `requirements.txt`.
- [ ] Add a theme picker to `ConverterGUI` (`rtf_to_pdf_converter.py`),
  following KVGrainy's `theming.py` pattern (`apply_theme`,
  `capture_defaults` for "System Default").
- [ ] Add `kvg-updater` (pinned tag) + an `updater.py` wrapper, same as
  KVGroove above.

### KVGenius
- [ ] Remove the `flet_kvg_themes` import path entirely — it's dead (not
  installed, falls back silently).
- [ ] Add VisualAssault's `packages/flet` (pinned tag) as the real theme
  source instead.
- [ ] Wire `kvg_updater`'s bundle mode in (`check_for_bundle_update` /
  `download_and_extract_bundle` / `apply_bundle_update_and_restart`) — the
  design gap is resolved, this is now an implementation task. Before
  trusting it silently: confirm `Path(sys.executable).resolve().parent`
  in a real `flet build` output actually points at the bundle root, and
  that `_find_bundle_binary`'s per-platform lookup finds the right
  executable for the Flet version in use. Test on at least one real build
  before relying on it in production.

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
