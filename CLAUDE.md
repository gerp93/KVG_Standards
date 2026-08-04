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
