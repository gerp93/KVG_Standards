# kvg_update (Godot)

Notify-only update check for Godot games built via `release-godot.yml`. See
`kvg_update.gd`'s doc comment for why this is notify-only (opens the release
page) rather than a self-replacing updater like `kvg-updater` (Python) or
`kvgupdate` (Go).

## Install

Godot has no dependency manager that can pin a git ref, so this is vendored
into each consumer repo rather than declared as a dependency. Copy it in with
a pinned-commit header, then keep it refreshed with a small script like
`scripts/update-kvg-update.sh` (see `gerp93/airport` for the reference
version) that re-copies from a local `KVG_Standards` checkout and stamps the
commit it came from into a header comment. Fix bugs here upstream, not in a
vendored copy.

## Usage

```gdscript
var updater := preload("res://addons/kvg_update/kvg_update.gd").new()
add_child(updater)
updater.check_complete.connect(_on_update_check_complete)
updater.check("gerp93/airport", ProjectSettings.get_setting("application/config/version"))

func _on_update_check_complete(result: Dictionary) -> void:
	if result.available:
		# result.latest, result.url — show a "new version available" prompt
		pass
```

`current_version` should be `application/config/version` from `project.godot`
— `release-godot.yml` stamps the real release tag into that field at build
time, so a plain editor run (which still has the committed dev placeholder)
will usually report itself as behind the latest release. That's expected.
