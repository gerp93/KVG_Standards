# Cloudflare Workers (MCP connectors and other Workers)

A category for a repo whose product is a **Cloudflare Worker**: a small server that runs on
Cloudflare, not an app users download. First consumer:
[RecipeConnector](https://github.com/gerp93/RecipeConnector) (an MCP server that lets Claude
read, search and save recipes in a GitHub repo, on Cloudflare's free plan).

It doesn't fit the desktop-app, Go web app or Claude plugin categories: there is no binary,
installer or release asset, nothing for users to update, and the deploy target is Cloudflare
rather than DigitalOcean (`gameshell-deploy`) or a marketplace. **Merging to `main` is the
release**: the code on `main` is what is running.

## What lives where

| Thing | Where | Rule |
|---|---|---|
| Code, `wrangler.toml`, tests | the repo | `account_id` and non-secret `[vars]` may be in `wrangler.toml`; an account ID is not a secret |
| Worker secrets (API keys, shared passwords the Worker checks) | Cloudflare, set with `wrangler secret put` | **Never in the repo, in GitHub, or in a `.dev.vars` that is committed.** A deploy does not touch them. Cloudflare never shows one again, so a lost one is replaced, not recovered |
| `CLOUDFLARE_API_TOKEN` | GitHub, the repo's Actions secrets | The only secret CI needs. Made from Cloudflare's "Edit Cloudflare Workers" template, limited to the one account |
| Deploy logic | `deploy-cloudflare-worker.yml` here | Called by tag, never copied into the repo |

## Pipeline

Reusable workflow
[`deploy-cloudflare-worker.yml`](.github/workflows/deploy-cloudflare-worker.yml), called from
the repo's `.github/workflows/ci.yml` (copy [`templates/deploy-cloudflare-worker.yml`](templates/deploy-cloudflare-worker.yml)).

| Event | What runs |
|---|---|
| Pull request | `npm ci`, `npm run typecheck`, `npm test`. The deploy job is skipped, so the Cloudflare token is never given to code from a PR |
| Push to `main` (what merging a PR does) | The same, then `npx wrangler deploy` |
| Run by hand (`workflow_dispatch`) on `main` | The same, to redeploy without a change |

- The "only on `main`, never on a PR" gate lives in the shared workflow, so a caller can't
  forget it. The deploy job is serialized (`concurrency`, no cancel) so two merges can't race.
- The caller passes `CLOUDFLARE_API_TOKEN` explicitly (`secrets:`), never `secrets: inherit`.
- The repo must have `typecheck` and `test` npm scripts (`run_typecheck: false` skips the first).
- The workflow runs on `ubuntu-latest` with Node 24 by default (`node_version`).
- **Repo requirements:** commit `package-lock.json` (CI uses `npm ci`); put `account_id` in
  `wrangler.toml` so the token can deploy without guessing the account.

## Rules

- **Call the shared workflow**; a local copy of the test-and-deploy logic is drift, same as for
  every other `release-*.yml`. Pin it the way every other consumer does (`@main` until KVG_Standards
  cuts tags, then the tag).
- **Docs the maintainer will need later.** The README keeps a "Coming back to this later" section:
  what it is and where it runs, how to change it, the table above filled in for this repo with a
  "if it breaks" column, and how to run things by hand. A Worker is easy to forget about, and its
  secrets can't be read back.
- **Tools that Claude has already saved.** If the Worker is an MCP server, Claude saves the tool
  list when the connector is added; after tools or their arguments change the connector must be
  removed and added again. Say so in the README.
- **Versioning:** none on GitHub. No `auto-release.yml`, `cut-release.yml`, tags or
  `VERSION_BUMP.md` (they exist to produce release assets, and there are none). `package.json`
  stays `private` and its `version` is not meaningful; Cloudflare keeps the deployment history
  (`wrangler deployments list`, and `wrangler rollback` to go back).
- **Licensing:** AGPL-3.0 by default as everywhere (`licensing.md`); `LICENSE` file plus
  `"license": "AGPL-3.0-only"` in `package.json`. Check the dependencies (the MCP SDK is MIT, zod is MIT).
- **Every repo also needs** `TODO.md` and a README that says it follows KVG_Standards.
- **Keep `package.json` honest:** no unused dependencies (an unused web framework in a Worker
  is dead weight and a security-advisory surface).

## Not applicable

Theming (no UI), logo placement and icon generation, update-check, Windows installer, Electron
menu and version, SQLite location, release notes, auto/cut release, `VERSION_BUMP.md`, and 1.0
readiness (that applies to downloadable desktop apps and Godot games only).

If a Worker does grow a user-facing page, theming becomes a question for that page; take it
through the "New tech stacks" process in `CLAUDE.md` rather than deciding locally.

## Not verified / open

- The shared workflow's first real run is RecipeConnector's first push to `main` after it switches
  to it. Until that is green, treat the deploy path as unproven. The previous repo-local version
  was verified by a manual run.
- A pull-request `wrangler deploy --dry-run` step (catches config and bundling errors before
  merge, needs no token) is not in the workflow yet. Worth adding once a Worker wants it, as an
  opt-in input.
- Design approval: this category was designed in the same change that added it, as the owner
  asked; per `CLAUDE.md`'s "New tech stacks" process it still wants the owner's sign-off on review.

## Audit checklist (also in the `app-standards` skill)

- `ci.yml` calls `deploy-cloudflare-worker.yml` (pinned like other consumers), passes `CLOUDFLARE_API_TOKEN` explicitly, triggers on `pull_request`, `push` to `main` and `workflow_dispatch`; no local copy of the logic.
- No secret values anywhere in the repo; `account_id` only in `wrangler.toml`.
- `package-lock.json` committed; no unused dependencies; `typecheck` and `test` scripts.
- `LICENSE` (AGPL-3.0); `TODO.md`; README states it follows KVG_Standards and has a "Coming back to this later" section.
- No `auto-release.yml`, `cut-release.yml` or `VERSION_BUMP.md` (nothing to release).
