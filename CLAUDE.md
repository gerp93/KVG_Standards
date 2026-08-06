# CLAUDE.md — KVG_Standards

This repo has no application code — it's the standards source of truth for
other gerp93 app repos. Changes here affect every repo that calls its
reusable workflows or uses its skill, so treat edits as a shared-API change:

- Reusable workflows in `.github/workflows/` are called by tag
  (`@main` today, since no versioned tags exist yet) from other repos — a
  breaking input change breaks every caller silently until they run.
- `templates/*.yml` are copied into consumer repos, not called — editing a
  template doesn't retroactively update anyone; existing consumers keep
  their old copy until someone re-syncs them.
- See `README.md` for the workflow catalog and `themes-versioning.md` for
  the theming rule.

## New tech stacks

If you're building or retrofitting an app on a stack this repo doesn't yet
cover (theming, release/CI, update-check, or licensing — see the
`app-standards` skill's checklists), that gap is not yours to paper over
locally in the app repo. The process is:

1. Design the standard for that stack (which package/workflow shape it
   needs, following the existing pattern for its category).
2. **Ask the human to approve the design before implementing it** — this is
   a shared-API decision, not a local one.
3. Once approved, add it here (new `packages/`, `.github/workflows/`,
   `templates/`, and a doc like `themes-versioning.md`/
   `update-check-versioning.md`), then update the `app-standards` skill so
   future repos and audits pick it up automatically.
4. Only then wire it into the app repo that needed it.

A one-off implementation that lives only in the consumer app repo — even a
good one — is exactly the kind of drift this repo exists to prevent.
