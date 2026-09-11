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

## Instance isolation (required alongside the above)

Electron apps here use `sql.js` — the whole database is loaded into memory
once at startup and written back to disk with a full overwrite on every
save (not a live, incrementally-written connection). That makes it
dangerous for two processes to ever have the same db file open at once:
whichever one saves last silently clobbers whatever the other one had,
with no error and no merge. This isn't hypothetical — it's what actually
happened to FileShuttle's mapping data (2026-09), traced back to exactly
this. Every Electron app on this pattern needs all three of the following,
not just the path bookkeeping above:

1. **Dev and packaged builds must never resolve to the same userData
   folder.** Don't rely on `app.setName(...)` alone to "pin" a shared
   folder — Electron/Chromium can resolve its *native* default userData
   directory from the running executable's own identity before your JS
   even runs, so `electron.exe` (dev) and `YourApp.exe` (packaged) can
   land in genuinely different folders on case-sensitive filesystems
   (invisible on Windows/NTFS, real on Linux). The fix is to make dev
   *intentionally* separate, not to chase making it match: call
   `app.setPath('userData', ...)` yourself, synchronously, before anything
   else touches `app.getPath('userData')` — pointing dev at a `<name>-dev`
   sibling folder so it can never share a file with a packaged install:
   ```ts
   export function pinUserDataPath(): void {
     const dirName = app.isPackaged ? 'yourapp' : 'yourapp-dev';
     app.setPath('userData', path.join(app.getPath('appData'), dirName));
   }
   ```
   Call `pinUserDataPath()` as the first thing in `main.ts`, before
   `app.setName(...)` and before `app.whenReady()`.
2. **`app.requestSingleInstanceLock()`**, so two copies of the *same*
   build variant can't both hold the db open — the lock is scoped per
   userData folder, so once (1) is in place this also can't cross-block
   dev against packaged. `app.on('second-instance', ...)` should just
   focus/restore the existing window instead of doing nothing.
   **Also add a force-exit safety net on the losing side** — `app.quit()`
   called on the loser (before `whenReady()`, since it never gets there)
   has been directly observed leaving the process alive for hours instead
   of actually exiting, rather than the few-hundred-ms it should take:
   ```ts
   if (!gotLock) {
     app.quit();
     setTimeout(() => process.exit(0), 1000);
   }
   ```
3. **Never silently create a fresh empty database when a *configured*
   custom path is missing** (drive unplugged, cloud-synced folder not
   mounted yet). `initDatabase()`'s existing "create if the default path
   doesn't exist" behavior is correct and expected for first run — but a
   *user-chosen* path from `app-config.json` going missing means their
   real data is probably still out there, unmounted; silently starting
   fresh and then saving over nothing is how it looks "deleted." Check
   before calling `initDatabase()`:
   ```ts
   const configuredDbPath = getConfiguredDbPath(); // raw override, no fallback
   if (configuredDbPath && !fs.existsSync(configuredDbPath)) {
     // show a dialog: Quit, or fall back to the default location
   }
   ```

See Sweeper's and FileShuttle's `src/main/dbLocation.ts` (`pinUserDataPath`,
`getConfiguredDbPath`) and `main.ts` (call order, the single-instance-lock
block, the pre-`initDatabase` guard) for the concrete, current shape of all
three.

**Worth knowing:** RolePlaymate sidesteps the whole "whichever save wins"
failure mode a different way — it uses Node's built-in `node:sqlite`
(`DatabaseSync`, WAL mode, real incremental file writes) instead of
`sql.js`, so there's no in-memory whole-file snapshot to clobber in the
first place. The three items above are still required regardless of
engine (a stale reader can still show wrong data, and two writers can
still corrupt a WAL-mode file if nothing coordinates them), but a future
new Electron app, or a deliberate migration of an existing one, should
weigh `node:sqlite` over `sql.js` — this hasn't been decided as the
default yet (see `REPO_SCOPE.md`'s RolePlaymate section), just flagged as
real prior art.

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
