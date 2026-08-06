# SQLite database location

Any app that stores its own data in a local SQLite file should let the
user relocate that file — outside the app's own install/data directory,
for easier backup or syncing (e.g. into a cloud-synced folder) — rather
than hardcoding a fixed path. This is a shared component, same principle
as theming and update-check: **one implementation, pinned by consumers,
not copy-pasted per repo.**

## The reference: Sweeper

Sweeper (Electron) already had this — `src/main/dbLocation.ts` — before
this was written up as a standard. It's the reference implementation:
default path under `app.getPath('userData')`, an optional override stored
in a small `app-config.json`, copy-on-relocate so moving the file never
loses data, and a full app relaunch after changing (an open sqlite
connection can't be pointed at a new path). See its `main.ts` for the
Settings-UI wiring (`dbLocation:get`/`browseExisting`/`browseNew`/`set`/
`resetToDefault` IPC handlers).

## The packages

| Package | For | Status |
|---|---|---|
| [`packages/python/kvg_dblocation`](packages/python/kvg_dblocation) | Any Python app storing data in SQLite | New — logic smoke-tested (default/effective path, copy-on-relocate, adopt-existing, reset), not yet wired into a real app's Settings UI |

Electron apps don't need a package: Sweeper's `dbLocation.ts` **is** the
pattern — copy its shape (parameterize the two hardcoded values,
`sweeper.db` and the app name, if reusing it in another Electron app).

No Go/Wails app currently stores data in SQLite (card-judge/timeline-trivia
use MariaDB, server-side). If one does in the future, design a
`packages/go/kvgdblocation` following the same shape — see `CLAUDE.md`'s
"New tech stacks" process (design it, get approval, land it here, then
wire it into the consumer).

## The rule

**Consumers pin to a tag, never `@main`/a pseudo-version.**

```
# Python — requirements.txt, wrong:
kvg-dblocation @ git+https://github.com/gerp93/KVG_Standards.git@main#subdirectory=packages/python/kvg_dblocation

# Python — right:
kvg-dblocation @ git+https://github.com/gerp93/KVG_Standards.git@v0.3.0#subdirectory=packages/python/kvg_dblocation
```

**Current interim exception**, same as `update-check-versioning.md`:
KVG_Standards has no tagged releases yet, so consumers pin to `@main`
until a first tag exists. Once one exists, switch pins to it.

## What a consumer app still owns

The package only manages the path/config bookkeeping. Each app supplies:
- Its own data directory (reuse whatever convention the app already has —
  don't invent a second one alongside an existing cache/output-dir scheme).
- Opening/closing its own sqlite3 connection — always close it before
  calling `set_db_path`/`reset_to_default_db_path`.
- A Settings-UI section with the three actions (choose existing file,
  choose new location, reset to default) and a restart afterward.

See each package's README for a full wrapper example.

## Bumping a pinned version

Same discipline as a theme or update-check version bump: update the
pinned tag in its own commit, don't bundle it into an unrelated change,
and re-test the relocate flow (not just that the app still builds) —
copy-on-relocate touching the wrong file/losing data would be a bad bug
to ship silently.
