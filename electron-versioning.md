# Electron version

Every Electron app here should be pinned to a reasonably current major
version of `electron`, checked against what's actually current — not
copied from whatever an existing sibling app's `package.json` happens to
say. That's how this drifted in the first place.

## What went wrong (2026-09-14)

FileShuttle, Sweeper, TrackDraft, and Bracketeer were all pinned to
`"electron": "^28.0.0"` — Electron 28, released ~December 2023. FileShuttle
and Bracketeer are both new apps (created within weeks of this audit), not
old ones that simply never got updated: they were scaffolded by copying an
existing app's `package.json`, which already had the stale pin, so the new
app started its life over two years behind current on day one.

RolePlaymate is the one exception, pinned to `^35.7.5` (Electron 35) — newer,
but still not current at the time it was created, and still not current now
(current latest as of this writing is 44.3.0 — check `npm view electron
version` for the actual current number, don't trust this file to stay
up to date). Nobody had copied a repo with a newer pin yet when it was
built; it was luck, not a rule anyone was following.

This surfaced while chasing a real, unreproducible startup hang in
FileShuttle (see its `REPO_SCOPE.md` entry and `db-location-versioning.md`'s
"Instance isolation" section) — an ancient, long-unmaintained Electron/V8
build is a real candidate for an unexplained low-level stall like that.
Whether that turns out to be the actual cause or not, shipping a brand-new
app already 2+ years behind on its runtime is wrong regardless.

## The rule

**When creating a new Electron app, or auditing an existing one:** check
`npm view electron version` (or the npm page) for the actual current
release, and pin to that major version — not to whatever an existing
sibling repo happens to have. Don't assume a recently-created app is
automatically current; check it directly.

```
npm view electron version
```

Use a caret range on the major (`"electron": "^44.0.0"`, not `"44.3.0"`
exact-pinned) so patch releases within that major still apply normally —
same spirit as the version pins used elsewhere in this repo, just without a
tag/release process to pin *to* (there's no KVG_Standards-published Electron
package; `electron` is a normal upstream npm dependency).

A major-version jump this large (e.g. the 28 → 44 upgrades this triggered)
can carry real breaking changes — sandboxing/context-isolation default
changes, removed APIs, Node version bumps affecting native deps like
`sql.js`/`better-sqlite3`/`node:sqlite`. Treat it as its own PR: bump the
dependency, `npm install`, then actually exercise the app (typecheck, a
real launch, the core user flows) before merging — don't just bump the
number and assume it's fine because the build succeeded.

- **Violation to flag:** an Electron app pinned more than a couple of major
  versions behind current `npm view electron version`, especially one
  created recently (a new app inheriting a stale pin from whatever it was
  scaffolded from is the most likely way this happens — check for it
  explicitly, don't assume "new app" means "current dependency").
- **Violation to flag:** an exact-pinned Electron version (`"electron":
  "44.3.0"` with no `^`) — blocks picking up patch releases (security
  fixes included) without a manual bump.

## Current state (2026-09-14 audit)

| Repo | Electron version | Notes |
|---|---|---|
| FileShuttle | 28.3.3 → being upgraded, see its own PR history | New app, inherited a 2+ year old pin |
| Sweeper | 28.3.3 | Not yet upgraded |
| TrackDraft | 28.3.3 | Not yet upgraded |
| Bracketeer | 28.3.3 (pinned; not yet installed at audit time) | New app, inherited a 2+ year old pin |
| RolePlaymate | 35.7.5 | Newer than the others but still not current |

Sweeper, TrackDraft, Bracketeer, and RolePlaymate have not been upgraded as
part of this pass — only FileShuttle, as the live test case for whether a
current Electron version actually resolves the startup-hang investigation.
If it does, the same upgrade is worth doing across the rest; track that
here or in each repo's own `REPO_SCOPE.md` entry when it happens.
