# 1.0 readiness

Attestations for [KVG_Standards' 1.0 readiness standard](https://github.com/gerp93/KVG_Standards/blob/main/app-1-0-readiness.md).
The mechanical gates (M1–M7) are computed by the audit; this file holds the
compat-surface declaration and the five attested gates (A1–A5).

An attestation is valid only for the version it names, and counts as
failing if any compat-surface path changed (other than adding new migration
files) after that version's tag. Re-test and re-date rather than editing in
place.

## Compat surface

Path globs for everything users can't cheaply recreate — what a 1.0
promises not to break. The audit's compatibility-freeze gate (M3) watches
these. Leave nothing out: an empty list fails M3.

- `<path/to/schema-or-migrations/**>` — database schema/migrations
- `<path/to/settings-schema>` — persisted settings
- `<path/to/update-manifest-code>` — update channel / release asset naming
- (file formats, CLI flags, if any)

## Attestations

For each gate: **status** (`pass` / `fail` / `N/A — reason`), **date**,
**version tested**, **evidence** link.

### A1 — Upgrade path

Installed previous release → updated via the in-app updater → data and
settings intact. One line per OS the app ships.

- Windows: <status> · <date> · <from → to version> · <evidence>
- macOS: <status or N/A — reason> · …
- Linux: <status or N/A — reason> · …

### A2 — Migration test

Automated test migrating the oldest supported data/schema to current.

- <status> · <date> · <version> · <link to test>

### A3 — Failure behavior

A missing/corrupt data path never silently creates an empty database; a
failed launch leaves a recoverable state.

- <status> · <date> · <version> · <evidence>

### A4 — Real use

Owner used the app for its actual purpose for 30+ days, no data loss.

- <status> · <date range> · <version> · <evidence/notes>

### A5 — Docs

README covers install, usage, and known limitations.

- <status> · <date> · <version> · <link to README sections>
