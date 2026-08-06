# Update-check versioning

Self-update (checking GitHub Releases for a newer build and replacing the
running binary) is a shared component, same principle as theming:
**one implementation, pinned by consumers, not copy-pasted per repo.**

## The packages

| Package | For | Status |
|---|---|---|
| [`packages/python/kvg_updater`](packages/python/kvg_updater) | PyInstaller-built Python GUI apps | Extracted from KVGrainy's working `updater.py` — battle-tested logic, just parameterized |
| [`packages/go/kvgupdate`](packages/go/kvgupdate) | Wails (Go) desktop apps | New — check/download logic is low-risk, but the extract-and-replace path hasn't been run against a real build yet |

Flet apps (KVGenius) and Electron apps don't have a package here yet:
Flet's `flet build` output layout hasn't been confirmed compatible with
`kvg_updater`'s PyInstaller assumptions (see that package's README);
Electron already has a real, maintained answer in `electron-updater` —
nothing to build, see Sweeper's `src/main/main.ts` for the reference
wiring (`setupAutoUpdater`/`checkForUpdatesNow`).

## The rule

**Consumers pin to a tag, never `@main`/a pseudo-version.**

```
# Python — requirements.txt, wrong:
kvg-updater @ git+https://github.com/gerp93/KVG_Standards.git@main#subdirectory=packages/python/kvg_updater

# Python — right:
kvg-updater @ git+https://github.com/gerp93/KVG_Standards.git@v0.3.0#subdirectory=packages/python/kvg_updater
```

```bash
# Go — wrong:
go get github.com/gerp93/KVG_Standards/packages/go/kvgupdate@latest

# Go — right:
go get github.com/gerp93/KVG_Standards/packages/go/kvgupdate@v0.3.0
```

Same reasoning as `themes-versioning.md`: `@main` silently picks up
whatever `KVG_Standards` HEAD happens to be on every install; a pinned tag
makes a version bump a deliberate, reviewable, one-line change.

## What a consumer app still owns

The packages are generic; each app supplies its own thin wrapper with:
- Its GitHub repo (`"owner/repo"`)
- Its app name (must match the name used in its `release-*.yml` call, since
  that's what determines the release asset's filename)
- Where its current build-time version comes from (KVGrainy: a
  CI-generated, gitignored `_version.py`; a new app should follow the same
  pattern rather than invent another one)

See each package's README for a full wrapper example.

## Bumping a pinned version

Same discipline as a theme version bump: update the pinned tag in its own
commit, don't bundle it into an unrelated change, and re-test the update
flow (not just that the app still builds) since a `kvg_updater`/`kvgupdate`
version bump could change the replace-while-running behavior itself.
