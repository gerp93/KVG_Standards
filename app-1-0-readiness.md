# 1.0 readiness

When is an app ready to be called 1.0 — and when is a `1.x` version number
premature? This is a deliberately high bar, defined as a fixed set of
pass/fail gates so the answer doesn't depend on mood.

## Why version numbers alone can't decide this

`auto-release.yml` patch-bumps on **every** push to `main`, and its
Conventional Commits handling (`mathieudutour/github-tag-action`) bumps the
major on a `feat!:` / `BREAKING CHANGE` commit. So an app reaches `1.0.0`
by accident of commit wording, not because anyone decided it was ready, and
the patch number climbs whether or not anything meaningful changed. The
version number records what the release tooling did, not maturity.

Under SemVer, `1.0.0` means *"we now promise compatibility."* For a desktop
app the "public API" is whatever a user can't cheaply recreate or work
around: **the on-disk data/DB schema, settings, the update channel, and any
file formats or CLI flags.** The 1.0 question is therefore *"are we ready to
stop breaking those?"* — not *"is it feature complete?"*

## Scope

Applies to apps that ship a versioned build users download: desktop GUI
apps, plugins, and games (the "Desktop GUI app / plugin" and "Godot game"
rows in the `app-standards` skill's pipeline table).

Out of scope, reported as `N/A`:

- **Go web apps** (card-judge, timeline-trivia) — deployed on push, no
  versioned release a user installs.
- **Libraries** (gameshell-framework) — 1.0 there means API stability, a
  different bar. Needs its own design if wanted.
- **Repos with no approved category** (radbot, see `REPO_SCOPE.md`).

## The gates

An app is **ready for 1.0 only if every gate passes.** Seven are
*mechanical* (computed from the repo and GitHub), five are *attested*
(a human signs off in `READINESS.md` with evidence).

### Mechanical gates

| # | Gate | Pass condition | Data source |
|---|---|---|---|
| M1 | Standards | Zero open `app-standards` violations. No `TBD` cells in the app's `REPO_SCOPE.md` row. Electron apps are within **1 major** of `npm view electron version` (stricter than the "couple of majors" rule in `electron-versioning.md`). | repo files |
| M2 | Age | First tagged release is at least **90 days** old. | releases/tags API |
| M3 | Compatibility freeze | In the last **60 days**: no commit marked breaking (`type!:` or a `BREAKING CHANGE` footer), and no change to the declared compat-surface paths other than *adding* new migration files. | git log |
| M4 | Tests in CI | A workflow that runs the app's automated tests runs on push/PR, is green on the default-branch head, and at least **90%** of its runs in the last 30 days were green. | Actions API |
| M5 | Release health | The last **10** release-workflow runs succeeded, and the latest release carries the full asset set for every OS the app ships. | releases + Actions API |
| M6 | Clean backlog | `TODO.md` has no open item under `## Fixes` and no entries under any `## Needs real-world verification` heading. No open issue labeled `bug` or `data-loss`. | repo files, issues API |
| M7 | Dependencies | No high or critical advisories in production dependencies (Dependabot alerts, or `npm audit --omit=dev` / `pip-audit` / `govulncheck`). | Dependabot API or audit tooling |

Notes:

- **M4 requires *a* test-running workflow, not a particular one.** The
  shared release workflows run no tests and there is no reusable
  `ci-node`/`ci-python` yet (only `ci-go.yml`). A shared Node/Python test
  workflow is a worthwhile follow-up (a new shared-API addition, so it
  needs its own approved design) but isn't a precondition of this standard.
- **An empty `TODO.md` is not evidence of "no known issues"** — most apps'
  are still the untouched template. M6 only blocks on things that *are*
  written down; the attested gates and M4 are what supply positive
  evidence.
- **M3 reads the compat surface from `READINESS.md`** (the "Compat
  surface" section lists the path globs: schema/migration files, settings
  schema, update-manifest code). An app with no `READINESS.md`, or with an
  empty compat-surface list, fails M3 — "nothing declared" can't be
  verified frozen.

### Attested gates

Recorded in the app's `READINESS.md` (copy `templates/READINESS.md`). Each
needs a date, the app version tested, and an evidence link (PR, run, test
file, issue). They are only valid against the version they name, and
**go stale** — count as failing — if any compat-surface path changed (other
than additive migrations) after the attested version's tag.

| # | Gate | What is attested |
|---|---|---|
| A1 | Upgrade path | Install the previous release, update to the current one through the in-app updater, confirm data and settings survive — on **each OS the app ships**. |
| A2 | Migration test | An automated test migrates the oldest supported data/schema to current. Link the test. (Apps that store no persistent data mark this `N/A — no persistent data`, with the reason.) |
| A3 | Failure behavior | A missing or corrupt data path never silently creates an empty database (the FileShuttle data-loss incident class — see `db-location-versioning.md`), and a failed launch leaves a recoverable state. |
| A4 | Real use | The owner has used the app for its actual purpose for at least **30 days** with no data loss. |
| A5 | Docs | README covers install, usage, and known limitations. |

## Verdicts

The audit reports exactly one state per in-scope app:

| State | Meaning |
|---|---|
| `PRE-1.0 (n/12)` | Version is `0.x` and not all gates pass; `n` gates pass. List the failing gates. |
| `READY-FOR-1.0` | Version is `0.x` and **every** gate passes. This is the signal to cut `1.0.0` (via `cut-release.yml`, deliberately, not by a stray `feat!:`). |
| `OK-1.0` | Version is `>= 1.0` and every gate passes. |
| `PREMATURE-1.0` | Version is `>= 1.0` but gates fail. Informational — a release can't be un-released — but it means the compatibility promise isn't backed yet, and the failing gates are the work to back it. |
| `N/A` | Out of scope (see above). |

`PREMATURE-1.0` applies to every `>= 1.0` app that fails; there is no
grandfathering. KVGrainy and Sweeper were both at `1.x` before this
standard existed and are reported on the same terms as any other app.

### Gates the auditor can't compute

The automated audit that checks this runs outside this repo (a Claude
routine), and may lack access to some data sources — the Actions API, the
Dependabot API, or issues. **A gate whose data source isn't available is
reported `NOT COMPUTABLE`, never guessed and never silently passed.** An
app with any `NOT COMPUTABLE` gate cannot be `READY-FOR-1.0` or `OK-1.0`;
it is reported as `PRE-1.0`/`PREMATURE-1.0` with the uncomputable gates
listed separately from the failing ones, so "we couldn't check" is never
confused with "it failed". M4, M5, and M7 are the gates most likely to hit
this; M1, M2, M3, and M6 need only repo contents and git history.

## Cutting 1.0

When an app reaches `READY-FOR-1.0`, cut `1.0.0` deliberately with
`cut-release.yml` (explicit version), after a human has re-read the
`READINESS.md` attestations. Avoid reaching 1.0 through a breaking-change
commit message on `auto-release.yml`. Out of scope for this version of the
standard: a guard in `auto-release.yml` that blocks an automatic major bump
unless readiness passes — worth revisiting if an app crosses 1.0 by
accident after this lands.

- **Violation to flag:** an in-scope app whose verdict is `PREMATURE-1.0`.
- **Violation to flag:** an in-scope app with no `READINESS.md` (it can't
  have attested gates, so it can't be ready — note it, but it isn't a
  defect for a `0.x` app that isn't claiming readiness; it just caps it at
  `PRE-1.0`).
