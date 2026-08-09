# Game repos

Games are app repos, but several standards here assume a *utility desktop app*
— a window with chrome, a settings dialog, a theme, a self-updater. A game
breaks some of those assumptions for real reasons, not out of laziness. This
doc says which standards apply unchanged, which change shape, and which are
deliberately out of scope, so an audit doesn't keep re-flagging the same
non-issues.

Current game repos: **airport** (Godot 4, GDScript).

## Applies unchanged

| Standard | Notes |
|---|---|
| **Licensing** | AGPL-3.0 default, dependency-checked like any other repo. See the engine-attribution note below. |
| **`TODO.md`** | A game has more open design questions than most apps, not fewer. |
| **Docs point back here** | Same rule: `README.md` and/or `CLAUDE.md` must state the repo follows KVG_Standards. |
| **`REPO_SCOPE.md` entry** | Games go in the scope matrix like anything else. |
| **Release notes** | If it ships a downloadable build, releases get install instructions. |
| **`VERSION_BUMP.md`** | Required once the repo has `auto-release.yml`, same trigger as any other repo. |

## Changes shape

### Theming is art direction, not chrome

The theming standard exists so app *chrome* doesn't drift from VisualAssault.
A game's visuals are its art direction — palette, sprite style, readability of
game state — and are not interchangeable with a shared UI theme. Forcing a
game's playfield through VisualAssault would be a category error.

- **In scope:** a game's *out-of-game* surfaces, if it grows them — launcher,
  settings menu, options dialogs. If a game gets real menu chrome, that chrome
  should use the shared theme rather than a hand-rolled palette.
- **Out of scope:** the playfield, HUD, and anything whose colour encodes game
  state (aircraft status, valid/invalid placement). These are gameplay
  legibility decisions.
- **Don't flag** a game repo for having hardcoded colours in its render code.
  **Do flag** a game repo that grows a full settings/menu layer with its own
  duplicate palette.

### Save-game location is the DB-location standard

`db-location-versioning.md` exists so users can relocate their data for
backup/syncing instead of it sitting in a hardcoded relative path. A game's
save file is the same concern under a different name.

- Engines usually already provide the correct per-user location — Godot's
  `user://` maps to the platform's app-data directory. Using it satisfies the
  spirit of the standard.
- **Violation to flag:** a game writing saves to a hardcoded relative path
  (`./save.dat`, next to the executable) — same defect as KVGenius's
  `"./chat_history.db"`, and worse on Windows where the install directory may
  not be writable.
- A user-relocatable save directory is *nice*, not required, since save files
  are small and engines put them somewhere sane by default. Don't flag its
  absence.

### Update-check depends on distribution, and games only notify

The update-check standard assumes the app is downloaded directly from GitHub
Releases and must replace its own binary. That holds for a game distributed that
way, and does **not** hold for one distributed through a storefront.

- **Direct download (GitHub Releases, itch.io direct):** in scope. Use
  [`packages/godot/kvg_update`](packages/godot/kvg_update).
- **Storefront (Steam, itch app, console):** out of scope by design. The
  storefront owns updating, the same reasoning that makes KVGauge's Stream Deck
  plugin a documented exception rather than a gap.
- Record which of these a game repo is in `REPO_SCOPE.md` rather than leaving it
  ambiguous — the answer changes whether a missing updater is a gap.

**The Godot package is notify-only, and that is the standard, not a shortcut.**
`kvg_updater` and `kvgupdate` self-replace because their apps are single
binaries built around that flow. A Godot export is an executable plus resources
and the engine holds file handles on them, so replacing it in place is
platform-specific and easy to get subtly wrong — the exact class of bug the
shared-package rule exists to stop multiplying. A game therefore reports that a
new version exists and opens the download page. If one genuinely needs true
self-update, design it in KVG_Standards, not in the game repo.

**Vendored, not pinned.** Godot has no dependency manager that can pin a git ref
the way `requirements.txt` or `go.mod` can, so the package is copied into
`addons/kvg_update/` with a header comment recording its source commit plus a
re-vendor script — the same approach already used for VisualAssault's CSS in
gameshell-framework and Sweeper.
- **Violation to flag:** a vendored copy with no pin comment or no re-vendor
  script. That is how silent drift starts.

### Logo & branding: same surfaces, engine-specific plumbing

The placement checklist still applies (README, window/taskbar icon, in-app
usage, packaged binary icon), but the wiring is engine config rather than
`BrowserWindow({ icon })` or `iconphoto`:

- Godot: window icon via `config/icon` in `project.godot` (and
  `DisplayServer.set_icon` at runtime if it needs to change), packaged-binary
  icon via the export preset's per-platform icon fields.
- Icon generation still must be a checked-in script from one source mark, never
  hand-exported per size. Node+`sharp` and Python+Pillow are the existing
  reference scripts; an engine repo can use either — this is a build-time
  script, it doesn't have to be written in the game's language.
- **A game with no art assets yet is a real gap but not a drift risk.** Flag it
  as "needs a logo" and move on; don't invent a placeholder mark to tick the
  box.

## Engine attribution

Permissively-licensed engines still carry attribution obligations that survive
into the shipped build, and an AGPL-3.0 repo license does not discharge them:

- **Godot is MIT.** An exported game bundles the engine binary, so the build
  must include Godot's copyright notice. Godot exposes the full third-party
  list via `Engine.get_license_text()` / `get_copyright_info()` — surface it in
  an about/credits screen, or ship it as a text file alongside the build.
- Check this per engine. It is easy to miss because the *repo* license is
  correct while the *distributed artifact* is missing a notice.
- **Violation to flag:** a released game build with no engine attribution
  anywhere in it.

## Release / CI

Games are the "Desktop GUI app / plugin" category by shape — they ship a binary
end users download, so they get **both** `auto-release.yml` and
`cut-release.yml`, calling
[`release-godot.yml`](.github/workflows/release-godot.yml).

That variant differs from the others in ways worth knowing before editing it:

- **One Linux runner, not a three-OS matrix.** Godot's export templates are
  cross-platform, so a single runner holding them emits Windows, macOS and Linux
  builds in one pass. A matrix would triple runtime and engine downloads for
  nothing. The cost is that macOS output is an unsigned `.zip` rather than a
  signed/notarized `.dmg` (that needs a macOS runner plus certificates) and
  Windows icon embedding is skipped (needs `rcedit`). Both are moot while builds
  are unsigned.
- **Export templates are version-locked.** The `.tpz` download must match the
  engine version exactly or export fails with "template not found", which is why
  `godot_version` is a required input rather than "latest".
- **`export_presets.cfg` must be committed.** Godot cannot export without it and
  fresh projects gitignore it, since it can carry signing paths and keystore
  passwords. Either commit a secret-free preset file and keep signing material
  in Actions secrets, or reconstruct it in CI. The workflow fails with an
  explicit message rather than a confusing engine error if it is absent.
- **Version injection has no `_version.py` equivalent.** The workflow stamps the
  tag into `project.godot`'s `config/version`, which is what the in-game update
  check compares against GitHub's latest tag.
- **Godot exits 0 on some export failures**, so the workflow asserts each
  artifact exists and is non-empty instead of trusting exit status. Keep that if
  you touch it.

### Starting pre-1.0

`auto-release.yml`'s version bump starts from whatever the newest existing tag
is, so cut the first release deliberately with `cut-release.yml` at `v0.1.0`
rather than letting the auto-bump pick `v0.0.1`. After that, auto-release keeps
it pre-1.0 on its own: Conventional Commit `fix:` gives `0.1.x`, `feat:` gives
`0.x.0`, and **only** an explicit breaking change (`feat!:` or a
`BREAKING CHANGE:` footer) jumps to `1.0.0` — so avoid those until the game is
genuinely ready to claim it.
