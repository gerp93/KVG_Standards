# kvg_update (Godot)

Update check for Godot 4 games. Asks GitHub for the latest release tag,
compares it to the running build's version, and reports whether a newer one
exists.

## Notify-only, on purpose

This does **not** download or replace anything, unlike
[`kvg_updater`](../../python/kvg_updater) (Python) and
[`kvgupdate`](../../go/kvgupdate) (Go).

Those self-replace because their apps are single binaries designed around that
flow. A Godot export is an executable plus resources (usually embedded), and
swapping it while the engine holds file handles open is platform-specific and
easy to get subtly wrong — exactly the class of bug the shared-package rule
exists to avoid multiplying. Shipping an untested self-replace into a game is
worse than telling the player a version exists and opening the download page.

If a game genuinely needs true self-update later, design it here — not in the
game repo.

## Consuming it

Godot has no dependency manager that can pin a git ref the way `requirements.txt`
or `go.mod` can. So this is **vendored** into consumer repos with a pin comment
and a re-vendor script, the same approach already used for VisualAssault's CSS
in gameshell-framework and Sweeper.

1. Copy `kvg_update.gd` to `addons/kvg_update/kvg_update.gd` in the game repo.
2. Add a header comment recording the source and the commit/tag it came from.
3. Add a re-vendor script (`scripts/update-kvg-update.sh`) so refreshing it is
   one command and not a manual copy — see airport's for the pattern.

## Using it

```gdscript
const KvgUpdate = preload("res://addons/kvg_update/kvg_update.gd")

func _ready() -> void:
    var checker := KvgUpdate.new()
    add_child(checker)
    checker.check_complete.connect(_on_update_checked)
    checker.check("gerp93/airport",
        ProjectSettings.get_setting("application/config/version", "0.0.0"))

func _on_update_checked(result: Dictionary) -> void:
    if result["available"]:
        print("Update available: %s" % result["latest"])
```

`check_complete` always fires exactly once, with:

| Key | Meaning |
|---|---|
| `available` | `true` only if the latest tag is numerically newer |
| `latest` | Latest release tag, e.g. `v0.1.2` |
| `current` | Version passed in |
| `url` | Release page to open |
| `error` | Empty on success; a human-readable reason otherwise |

## Notes

- **Version comparison is numeric, not lexical.** `0.10.0` correctly beats
  `0.9.0`; a string compare gets that wrong, which matters early while versions
  are pre-1.0 and gaining digits.
- **A repo with no releases yet returns HTTP 404**, reported as
  `"no releases published yet"` rather than an error — a fresh repo is a normal
  state, not a fault.
- **Skip the check in headless/automated runs.** It makes a network call, so a
  game with a deterministic headless test mode should not fire it there.
- The version it compares against is whatever `release-godot.yml` stamped into
  `project.godot`'s `config/version` at build time. In a dev run that setting is
  whatever is committed, so an editor session will usually report itself as
  behind — expected, not a bug.
