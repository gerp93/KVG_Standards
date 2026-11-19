# Secrets

A secret is anything that lets someone act as the user or the maintainer: API keys, access and
refresh tokens, passwords, signing keys, client secrets, a connection URL with credentials in it.
This rule exists because a leaked key is not fixed by the next commit, and because an app that keeps
a key in the wrong place (a database the user syncs to a shared folder) leaks it without anyone doing
anything wrong. The good repos already follow it; this writes it down.

## 1. Never committed

A secret never goes in a tracked file, a template, a test fixture, a README example, a log sample or
git history. Tracked config holds **names** of secrets, never values:
[gameshell-deploy](https://github.com/gerp93/gameshell-deploy)'s `deploy.conf.template` lists
`EXTRA_ENV_VARS` (names only) and `create.sh` reads each value from the operator's environment at
run time. Use obvious placeholders in examples (`YOUR_API_KEY`), and keep a repo's real deployment
settings in a file the repo ignores, with an `*.example` beside it (kvguzzler's `deploy.env`,
`scripts/deploy.env.example`).

Every repo's `.gitignore` carries at least:

```
.env
.env.*
!.env.example
*.pem
*.key
secrets.json
```

`.env` is where local tooling puts keys, `*.pem`/`*.key` are private keys and certificates, and
`secrets.json` is the name the apps below use for their key file. Add the repo's own secret file
names beside them.

**If a secret was ever committed, rotate it first**, then clean the history if you want to. Deleting
the line is not enough: anyone who cloned, forked or read the Actions logs already has it, and
rewriting history does not take it back from them.

## 2. CI and release secrets

They live in GitHub Actions secrets and are used as `secrets.NAME`, nowhere else. The reusable
workflows here need none beyond the built-in `GITHUB_TOKEN`
(`release-electron.yml`, `release-avalonia.yml`). If a workflow ever needs another, it takes it as a
declared `workflow_call` secret that the caller passes by name (never `secrets: inherit`), and it
is never echoed, never put in a command line that gets logged, and never written into an artifact.
Release builds here are unsigned today, so there are no signing keys; when there are, same rule.

## 3. Secrets a user enters in an app

An API key, access URL or token pasted into Settings is stored **encrypted with the OS secret
store, in a small file of its own, outside the app's SQLite database.** The database is relocatable
and may sit in a synced or shared folder (see [`db-location-versioning.md`](db-location-versioning.md)),
and an OS-encrypted blob would not decrypt on another machine anyway. Keep the file in the app's
per-user config location (`userData` for Electron), not the data folder.

**Fail closed.** If real OS encryption is not available, refuse to save and say so. Never fall back
to plain text. On Linux, Electron's `safeStorage` can report itself available while using a fixed
key (`basic_text`, or `unknown`); that is not protection, so treat it as unavailable.

### Electron

Use `safeStorage`. The reference is Sweeper's `src/main/simplefin/store.ts`: its own file under
`userData` (never the database), written atomically (temp file with mode `0600`, then rename), the
Linux backend check above, decrypted only in memory right before a request, and the file deleted when
the connection is removed. Two other apps keep the key the same way, with less of it:

- playtime-roi's `src/main/secrets.ts`: a `secrets.json` in `userData`, `0600`, atomic write, fails
  closed when `safeStorage` is unavailable. No Linux backend check.
- TrackDraft's `src/main/ai/aiConfig.ts`: the Claude API key in `claude-api-key.enc` in `userData`,
  out of the database and the settings JSON, fails closed. Plain `writeFileSync` (not atomic, no
  explicit mode) and no Linux backend check.

New Electron apps copy Sweeper's version. There is no shared package for it yet.

### Other stacks

Python/Tkinter, Go/Wails, .NET/Avalonia and Godot have **no shared helper**. The requirement is the
same: the OS secret store where the stack has one (`keyring` for Python; DPAPI through
`ProtectedData` for .NET on Windows; the OS keyring for Go), otherwise a file outside the data
folder, readable by the owner only. That stack-specific helper is **not yet standardized**. Per
[`CLAUDE.md`](CLAUDE.md)'s "New tech stacks" process it has to be designed and approved here before an app
invents its own. For reference only, gameshell-deploy's `gui/secrets` keeps operator credentials in
the OS keyring through `go-keyring`, but it is repo-local, not a shared package.

### Headless tools and servers

A Python script or Go service that can't ask the OS: keep the file outside the repo and outside any
shared or synced data, mode `0600`, written to a temp file and renamed. For operator tooling,
environment variables are fine; never a file in the repo.

- SoSmartButNeverPunctual (`punctual.py`): tokens live in a per-user config directory
  (`~/.config/sosmartbutneverpunctual`, `%APPDATA%` on Windows), written by `_write_private`
  (`0600`, fsync, `os.replace`), and encrypted with DPAPI on Windows.
- KVGuzzler's house server (`server/internal/store/secrets.go`): API keys in `secrets.json` beside
  the database, mode `0600`, atomic write, and kept **out of the database on purpose** so the nightly
  snapshots and shared read-only copies don't carry keys. It is plain text for whoever can read the
  file; the point is who can read it and what gets copied, not encryption.

## 4. Handling in the app

- **Write-only in the UI.** Show "Saved" / "Not set". Typing replaces it. Never send the value back
  to the renderer or the page.
- **Never logged.** Not in a log, an error message, a crash report, an export, a diagnostic dump or a
  test snapshot. When a key is a query parameter (OpenEI, EIA), error text must not carry the URL.
- **Decrypt late.** In memory, right before the request, and drop it after.
- **Send it only where it belongs.** A key goes to the one host it is for, fixed in code, never one
  taken from a setting or a response.
- **Removing a connection deletes the secret.** Disconnect means the stored value is gone, not hidden.
- **A value that can't be decrypted** (copied from another computer, OS store reset) reads as "Not
  set" and asks for it again. It never crashes and never falls back to a guess.

## Known gaps

Checked in code on 2026-11-19; fix by moving to the pattern above.

- **KVGuzzler (Avalonia app)** keeps the OpenEI key in its settings database
  (`SetSetting(SettingKeys.OpenEiKey, ...)`, `src/KVGuzzler/Views/MainWindow.RateLookup.cs`), and the
  carbon feed key in `carbon.json`, written with `File.WriteAllText`
  (`src/KVGuzzler.Core/Carbon/CarbonConfig.cs`): plain text, no permission mode, no OS store. There is
  no .NET helper to move to yet; that is the "not yet standardized" case above.
- **TrackDraft** and **playtime-roi** lack the Linux `basic_text` check (see Electron above);
  TrackDraft also writes its key file non-atomically.
- **Sweeper's and TrackDraft's `.gitignore`** do not list `.env` or key files.
