# Python MCP servers and other headless uv projects

Standard for a repo that is a **uv-managed Python package with no GUI and no
PyInstaller build**: an MCP server (stdio, launched by Claude Desktop or Claude
Code), a command-line tool, or a library. First consumer:
[ColorBookForge](https://github.com/gerp93/ColorBookForge).

This is its own category because nothing else fits. It isn't a desktop GUI app
(no installer, no icon, no update-check), it isn't a Claude Code plugin (it is a
standalone server the user registers in a client's config), and it isn't a Go
library.

## What applies

| Standard | Applies? |
|---|---|
| Licensing | Yes. AGPL-3.0 by default; check dependency licenses first, as in `licensing.md`. |
| Release / CI | Yes. Both `templates/auto-release.yml` and `templates/cut-release.yml` calling `release-python-mcp.yml`, `templates/VERSION_BUMP.md`, and `templates/ci-python.yml` as `ci.yml`. |
| `TODO.md` | Yes. |
| Docs link back to KVG_Standards | Yes. |
| Theming, logo & branding, update-check, installer, application menu | N/A (no UI). |
| DB location | Only if the project keeps its own SQLite file, then as in `db-location-versioning.md`. |
| 1.0 readiness | N/A until the project has a compatibility surface worth promising. |

## Layout

- `pyproject.toml` with a `src/<package>/` layout, `uv_build` backend, and a
  `[project.scripts]` entry for the console command.
- `uv.lock` checked in. CI installs with `--locked`, so a stale lockfile fails.
- `ruff` and `pytest` in the `dev` dependency group. Tests must run with no
  network, GPU or running service; anything that needs one is marked and skipped
  by default.
- Python 3.11 or newer.

## Release

`release-python-mcp.yml` lints, tests, stamps the tag's version into the build
(`uv version --frozen`, not committed), runs `uv build`, and publishes a GitHub
Release with the wheel and sdist attached and the usual "Installing" blurb on top
of the generated notes. `version` in `pyproject.toml` is a placeholder: the tag is
the version. Users install with
`uv tool install git+https://github.com/<repo>@<tag>` or run it with `uvx --from`.

Publishing to PyPI is deliberately not part of this workflow. If a project ever
needs it, extend the reusable workflow here rather than adding a local copy.

## Registering an MCP server

The README of a consumer repo carries the client config snippet. For Claude
Desktop that is an entry under `mcpServers` that runs the installed command (or
`uvx --from git+https://github.com/<repo>@<tag> <command>`) over stdio, with any
paths passed through `env`, never hardcoded.

## Violations to flag

- A local copy of lint/test/build/release logic instead of calling the reusable
  workflows.
- A repo with `auto-release.yml` but no `VERSION_BUMP.md`, or one with only one of
  `auto-release.yml` / `cut-release.yml`.
- A missing or stale `uv.lock`.
- A hand-maintained version in `pyproject.toml` that is expected to match the tag.
