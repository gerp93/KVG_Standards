# Static sites (directory engine)

A new category: **static websites generated from data**, built with
[`directory-engine`](https://github.com/gerp93/directory-engine) (a private Go
generator). Each site, called a *niche*, is a small repo holding only
config, listings and assets, named after its content (not "directory-something").
The engine does the building, so the niche repos stay thin and never grow their
own copy of the templates.

This doesn't fit the desktop-app, Go web app or Claude plugin categories: there is
no binary to release, no server to deploy, and nothing for users to update.

## The two repo shapes

| Shape | Contains | Release | CI |
|---|---|---|---|
| **Engine** (`directory-engine`) | Go module: CLI, templates, embedded assets | Bare semver tag via `templates/cut-tag.yml`, no build artifact. Niche repos pin it | `ci.yml` calling `ci-go.yml` with `working_directory: .` and `run_tests: true` |
| **Niche site** (one repo per site) | `site.yaml`, listings file, `public/` assets | None. The site is published, not released | Build and publish workflow, see below |

## Rules

- **Pin the engine by tag** wherever a niche builds it (`go install
  github.com/gerp93/directory-engine/cmd/directory-engine@vX.Y.Z`). Never
  `@main` or `@latest` in a niche repo, for the same reason theming and
  update-check pin by tag. **Interim:** the engine has no tag until its first
  `cut-tag.yml` run, so a niche may use `@main` until then (same exception
  `update-check-versioning.md` documents for KVG_Standards itself); move to the
  first tag as soon as it exists.
- **Niche repos hold no generator logic.** No copied templates, CSS or build
  scripts. A niche that needs something the engine lacks gets a PR on the engine.
- **Validation gates the build.** Niche CI runs `directory-engine validate -strict`
  on pull requests so bad data fails review instead of shipping.
- **Licensing:** AGPL-3.0 by default, as everywhere (`licensing.md`). The
  engine's dependencies are `gopkg.in/yaml.v3` (MIT/Apache-2.0) and
  `golang.org/x/text` (BSD-3-Clause), both compatible. A niche's *dataset* may
  warrant a different license or have third-party terms of its own; that is a
  per-niche decision to record in that niche's README, not a silent default.
- **Docs:** each repo's README or CLAUDE.md states it follows KVG_Standards, and each has a `TODO.md`.
- **Visible-output hygiene:** featured/paid listings carry `rel="sponsored"`;
  every niche has a `site.contact_email` or states why not; `sitemap.xml`,
  canonical URLs and `robots.txt` come from the engine and aren't hand-edited.

## Theming (decision to confirm)

[VisualAssault](https://github.com/gerp93/VisualAssault) is deliberately loud,
eye-searing palettes for apps. That is wrong for a public directory that wants to
look trustworthy to searchers and to businesses buying listings. So the engine's
theming is **per-niche `theme:` config** (validated hex colors and a font stack, a
neutral default), emitted as CSS variables. This is a deliberate exception to "one
VisualAssault dependency per repo", not drift, but it is a shared-standard decision
and needs the owner's sign-off. If VisualAssault later gains a calm theme set, the
engine can read a theme by name instead.

## Build and publish (not yet standardized)

A niche is built with `directory-engine build` and the `dist/` folder published to a
static host (Cloudflare Pages or GitHub Pages). A reusable workflow for this does
not exist yet. The blocker is that the engine repo is private, so a niche's CI needs
a cross-repo token (or a release-binary download) to fetch it. Until that is
designed and approved, niche repos publish manually or with a repo-local workflow
that is flagged as interim. The design goes through the "New tech stacks" process in
`CLAUDE.md`.

## Not applicable

Theming package, update-check, Windows installer, Electron menu, SQLite location,
logo generation script, release notes and 1.0 readiness. A niche is data plus
config, with no shipped binary.

## Audit checklist (also in the `app-standards` skill)

- Engine: `ci.yml` calls `ci-go.yml` with `run_tests: true`; `cut-tag.yml` present; `LICENSE`; `TODO.md`; docs point here.
- Niche: `site.yaml` + listings + optional `public/`; no copied engine code; engine pinned by tag (or the interim `@main`); `validate -strict` in CI; `LICENSE`; `TODO.md`; docs point here.
