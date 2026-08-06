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
| KVGrainy | ✅ VisualAssault v0.2.0, pinned | ✅ | ✅ (`updater.py`, GitHub Releases API + self-replace) |
| KVGroove | ✅ VisualAssault v0.2.0, pinned | ✅ | ❌ **gap** |
| gameshell-deploy (Wails GUI) | ✅ VisualAssault, hand-transcribed, tokens current | ✅ | ❌ **gap** |
| Sweeper (Electron) | ⚠️ **stale vendor** — byte-copy of VisualAssault CSS missing `surface`/`border`/`textMuted`/`accentMuted` (pre-v0.2.0 snapshot, same drift class already fixed in gameshell-framework) | ✅ | ✅ already best-in-class (`electron-updater`, wired up) |
| KVG_Converter | ❌ **gap** — plain Tkinter GUI, no theming at all | ✅ | ❌ **gap** |
| KVGenius (Flet) | ⚠️ **broken** — imports `flet_kvg_themes` (an old, non-VisualAssault package) which isn't even in `requirements.txt`; theming silently no-ops to a hardcoded dark mode | ✅ | ❌ **gap** |
| KVGauge (Stream Deck plugin) | N/A? — needs a decision, see below | ✅ | N/A? — needs a decision, see below |
| gameshell-framework (Go library) | ✅ fixed this session (vendored VisualAssault CSS, re-vendor script) — covers card-judge + timeline-trivia too | N/A by design (tag-only release for `go.mod` pinning) | N/A (server-side, no client to update) |
| card-judge | ✅ (inherits from gameshell-framework) | N/A by design (deployed via gameshell-deploy/DO, not a release binary) | N/A |
| timeline-trivia | ✅ (inherits from gameshell-framework) | N/A by design | N/A |

## Action items by repo

### Sweeper
- [ ] Re-vendor `src/renderer/themes.css` from VisualAssault `packages/css/themes.css` @ `v0.2.0` (same fix already applied to gameshell-framework's `colors.css`). Simpler here than gameshell-framework's case: no "Classic" section to preserve — the whole file is VisualAssault content, so this can be a straight overwrite.
- [ ] Add a header comment noting the source tag, same convention as gameshell-framework's vendored section.
- [ ] Decide: copy `gameshell-framework/scripts/update-visual-assault-css.sh`'s approach (a repo-local re-vendor script), or centralize a version of that script in `KVG_Standards/scripts/` that any CSS-vendoring consumer can call with its own file path. **Open question, see "Open questions" below.**

### KVG_Converter
- [ ] Add `visual-assault-tkinter` (pinned tag) to `requirements.txt`.
- [ ] Add a theme picker to `ConverterGUI` (`rtf_to_pdf_converter.py`), following KVGrainy's `theming.py` pattern (`apply_theme`, `capture_defaults` for "System Default").
- [ ] Add an update-checker (see "Update-check standard" below) — this is a PyInstaller app just like KVGrainy, so the same mechanism applies directly.

### KVGenius
- [ ] Remove the `flet_kvg_themes` import path entirely — it's dead (not installed, falls back silently).
- [ ] Add VisualAssault's `packages/flet` (pinned tag) as the real theme source instead.
- [ ] Add an update-checker — Flet apps package via `flet build`, not PyInstaller, so confirm whether KVGrainy's `updater.py` approach (which assumes a PyInstaller-built binary path) needs adaptation for a `flet build` output layout before reusing it.

### KVGroove
- [ ] Add an update-checker — same shape as KVGrainy's `updater.py` (PyInstaller-built, so directly reusable/adaptable).

### gameshell-deploy (Wails GUI)
- [ ] Add an update-checker. No existing pattern for Go/Wails apps yet — needs a new design (see "Update-check standard" below), not just a port of KVGrainy's Python approach.
- [ ] Optional polish: add a version-pin comment + re-vendor script for `gui/frontend/src/themes.css`, matching the gameshell-framework/Sweeper convention, even though it isn't currently stale.

### KVGauge (Stream Deck plugin)
- [ ] **Needs a decision, not just an implementation**: does a Stream Deck plugin's property inspector (`propertyinspector.html`) even want a VisualAssault theme, given Stream Deck has its own UI chrome/conventions? And does "update-check" make sense here at all — Stream Deck plugins are normally reinstalled via a new `.streamDeckPlugin` file or the Elgato Marketplace, not self-updating. Recommend treating both as **out of scope** unless there's a specific reason to want them.

## Update-check standard (doesn't fully exist yet — needs design)

KVGrainy's `updater.py` is the only real example today: compares a build-time
`_version.py` (written by CI, gitignored) against the latest GitHub Release
via the API, downloads the matching asset, and self-replaces (with
Windows/macOS/Linux-specific replace logic — see KVGrainy's `CLAUDE.md` for
the OS-specific gotchas, especially the `os._exit()` requirement on Windows).

This needs to become a real shared component before rolling it out to
KVGroove/KVG_Converter/KVGenius/gameshell-deploy, the same way VisualAssault
is the shared theme component — otherwise every repo will copy-paste
`updater.py` and drift, which is exactly the problem this whole standards
effort exists to prevent.

**Open questions to resolve before implementing broadly:**
1. **Python (PyInstaller) apps** — KVGrainy, KVGroove, KVG_Converter: should
   `updater.py` become a small pip-installable shared package (own repo or a
   `packages/` subdir here, consumed the same way VisualAssault is — git
   dependency pinned to a tag), rather than copy-pasted three times?
2. **Flet apps** — KVGenius: `flet build` output layout differs from a
   PyInstaller `--onefile` binary. Does the same self-replace strategy even
   work, or does Flet need a different update mechanism?
3. **Go/Wails apps** — gameshell-deploy: no prior art at all. Likely shape:
   check GitHub Releases API from Go, prompt the user, download + replace —
   but Wails apps run as native binaries per-OS same as the PyInstaller
   case, so the replace-while-running logic (Windows self-delete batch
   script trick, macOS/Linux `execv`) may be portable in spirit even though
   the implementation language differs. Worth a design pass, not a blind
   port.
4. Electron apps are **already solved** — `electron-updater` is the
   industry-standard answer there. Nothing to build, just confirm any future
   Electron app wires it up like Sweeper did.

## Open questions (theming)

1. Should the CSS re-vendor script (`gameshell-framework/scripts/update-visual-assault-css.sh`)
   move into `KVG_Standards` as a shared, parameterized script (taking a
   target file path as an argument) instead of living per-repo? Sweeper and
   gameshell-deploy's `gui/frontend` would both want it too.
2. KVGauge theming/update-check scope decision (see above).
