# Game repos (Godot)

Godot (GDScript, no C#/.NET) is a distinct category from the desktop
GUI-app stacks the rest of this repo covers (PyInstaller/Wails/Electron/
Flet). This doc is the source of truth for how the standards below apply
to a Godot game repo — same role as `themes-versioning.md` /
`update-check-versioning.md` for their topics. Reference implementation:
[gerp93/airport](https://github.com/gerp93/airport).

## Release / CI

Same shape as the desktop-GUI-app category: **both** release triggers,
never just one.

- `templates/auto-release.yml` and `templates/cut-release.yml` (copied in
  as-is, same as any other consumer) call
  [`release-godot.yml`](.github/workflows/release-godot.yml) instead of
  one of the `release-<stack>-gui.yml` variants.
- `release-godot.yml` builds a Windows/Linux/macOS matrix, one native
  `godot --export-release` per OS on a matching runner (export templates
  are version-locked to the editor, so cross-exporting from a single host
  isn't worth the fragility), stamps the release tag into `project.godot`'s
  `config/version`, then packages and publishes like the other
  `release-*.yml` variants (including the install-instructions release
  body).
- Required inputs: `version`, `app_name`, and `godot_version` (must match
  the editor version the project is authored in exactly — export templates
  are version-locked and export fails outright on a mismatch).
- Every repo with `auto-release.yml` still gets `VERSION_BUMP.md` — no
  exception for games.
- Untested against a real end-to-end Godot export as of this writing (see
  `release-godot.yml`'s header comment) — verify a repo's first real
  release manually rather than assuming the matrix build works blind.

## Update-check

[`packages/godot/kvg_update`](packages/godot/kvg_update) — **notify-only**
(opens the release page; does not download or self-replace). Unlike
`kvg_updater` (Python) and `kvgupdate` (Go), a Godot export is an
executable plus (usually embedded) resources, and swapping it while the
engine holds file handles open is platform-specific and easy to get subtly
wrong — shipping an untested self-replace into a game is worse than
telling the player a new version exists.

Godot has no dependency manager that can pin a git ref, so this package is
**vendored (copied), not declared as a pinned dependency** like the
Python/Go packages:

- Copy `packages/godot/kvg_update/kvg_update.gd` into the consumer repo at
  `addons/kvg_update/kvg_update.gd`.
- Keep it refreshed with a small per-repo `scripts/update-kvg-update.sh`
  (see `gerp93/airport`'s copy for the reference version) that re-copies
  from a local `KVG_Standards` checkout and stamps the source commit SHA
  into a header comment — so the vendored copy always records which
  upstream commit it came from instead of drifting silently.
- Fix bugs upstream in `KVG_Standards`, then re-run the script — never
  patch the vendored copy in place.

See the package's own README for usage (`check()`/`check_complete`) and
why `current_version` should read from `project.godot`'s
`config/version` (which `release-godot.yml` stamps with the real tag at
build time — a plain editor run still has the committed dev placeholder
and will normally report itself as behind latest, which is expected).

## Theming

**Not yet covered.** No VisualAssault package exists for Godot/GDScript.
Placeholder shapes with no theme system (the "vibe install" exception the
`app-standards` skill already documents for uncovered stacks) are
acceptable for a prototype, but shouldn't be treated as a real dependency
in anything beyond that. If a game repo starts shipping real art that
needs a consistent palette, that's a "New tech stacks" case — design a
Godot theming package, get human approval, add it here, don't hand-roll a
palette locally.

## Logo & branding / icon generation

**Not yet covered.** No `generate-icons.*` script variant exists for
Godot's export presets (`export_presets.cfg`'s per-platform icon fields).
Flag as an open gap for any game repo that ships real branding, not a
blocker for a prototype with no art assets.

## Licensing

Default AGPL-3.0 applies the same as any other repo — check dependencies
per `licensing.md` before assuming it's fine. Godot Engine itself is MIT
(permissive, no blocker), but an exported build bundles the engine and
must carry Godot's copyright notice in the shipped product — see
[Godot's licensing docs](https://docs.godotengine.org/en/stable/about/complying_with_licenses.html)
for what that notice needs to say.

## Docs

Same rule as every other consumer: the repo's `README.md` and/or
`CLAUDE.md` must link back to
[gerp93/KVG_Standards](https://github.com/gerp93/KVG_Standards) and state
that it follows this standard, not just link to this one doc in passing.
