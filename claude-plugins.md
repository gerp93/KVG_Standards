# Claude Code plugins (including mods)

For a repo whose product is a [Claude Code plugin](https://code.claude.com/docs/en/plugins)
rather than an app users download: a plugin that adds a skill, command, agent or hook,
or a **mod**, a plugin whose code registers function hooks and draws panes, status
lines and toasts. First consumer: [Shipwatch](https://github.com/gerp93/Shipwatch).

A plugin has no build artifact. It is installed from the repo itself through a
marketplace, so almost everything the desktop-app standards cover (theming, installer,
update-check, DB location, logo placement) doesn't apply. What does apply is below.

## Layout

```
.claude-plugin/plugin.json      manifest, userConfig options, `types` for a mod
.claude-plugin/marketplace.json single-plugin marketplace, source "./"
hooks/hooks.json                { "modules": ["./register.tsx"] }   (mods only)
hooks/register.tsx              exports register(on, options)
hooks/<logic>.ts                pure logic, one concern per file
hooks/*.test.ts                 run by `claude plugin test`
types/index.d.ts                $.state contract (mods that keep state)
```

`marketplace.json` makes the repo installable without a clone:

```bash
claude plugin marketplace add gerp93/<Repo>
claude plugin install <plugin>@<marketplace>
```

Put both commands in the README's Install section. Don't name a plugin starting with
`claude-` or `anthropic-`; `claude plugin validate` rejects those as reserved.

## Versioning: omit `version`

**Leave `version` out of `plugin.json` and out of the marketplace entry.** For a plugin
whose marketplace entry uses a relative-path source in a Git-hosted marketplace, Claude
Code then uses the commit SHA as the version, so every push to `main` is a new version
and `claude plugin update` picks it up. A pinned `version` does the opposite: users stay
on the cached copy until someone bumps the string, however many commits land. That
fights `auto-release.yml`, which ships on every push.

`claude plugin validate` warns about the missing `version`. That warning is expected;
don't "fix" it, and don't run validate with `--strict`.

Git tags (`vX.Y.Z`, from `auto-release.yml` / `cut-release.yml`) and GitHub Releases are
markers for people. They don't pin installs. Don't use `claude plugin tag`: it names tags
`<name>--v<version>` and requires a `version`, which this standard omits.

## Release / CI

Same triggers as every other pipeline: **both** `templates/auto-release.yml` (every push
to `main`) and `templates/cut-release.yml` (explicit version), plus
`templates/VERSION_BUMP.md`, calling `release-claude-plugin.yml` with
`plugin_name` (and `marketplace_name` if it differs). It re-runs validate and test on the
tagged commit, then publishes a Release with the install commands on top and generated
notes below. Nothing is attached.

CI is `templates/ci-claude-plugin.yml` (copy as `.github/workflows/ci.yml`), calling
`ci-claude-plugin.yml`: install the CLI from npm, `claude plugin validate`, `claude plugin test`.
Neither needs a sign-in. `claude_code_version` defaults to `latest` on purpose: the mods
API is early access and changes between releases, so a failure on a new release is the
signal to adapt. Pin it per repo only to unblock a release while fixing.

## Mod conventions

These come from what `claude plugin validate` enforces and from mistakes already made.

- **`$` only goes into top-level functions of `register.tsx`.** Passing it to a helper
  in another file, or to a closure declared inside `register`, fails validation. Keep
  every `$.noun.method()` call in `register.tsx`, in function declarations at the top of
  the file, and put pure logic in other files. Inject I/O instead of passing `$`: for
  example a `{ run, fetch }` object whose members are arrows calling `$.process.run` and
  `$.http.fetch`.
- **State a drawing reads belongs in `$.state`** (declared in `types/index.d.ts`), not in
  module variables: a hot reload resets those. A render hook never writes state.
- **Test the pure logic** in `*.test.ts` (`claude plugin test`), including the failure
  and first-run cases. The UI itself is only checked by running it.
- **Prefer the `gh` CLI over tokens** for GitHub access. If a token fallback is offered,
  make it a `sensitive` `userConfig` option, never a file in the repo.
- **Anything autonomous is opt-in and capped.** A mod that starts turns on its own
  (`$.prompt.submit`) defaults to off, limits how many it sends per session, and sends
  at most one per triggering event.
- **Allow-list anything interpolated into a prompt.** Names that come from outside
  (repo, branch, file, PR title) are controlled by someone else and can carry
  instructions. Refuse unusual values instead of sanitizing them, and test that.
- Every `userConfig` option needs `type`, `title` and `description`, and a safe `default`.
- Mods are early access. Say so in the README and in release notes, and mark a first
  release a pre-release if its install path hasn't been exercised.

## Licensing, docs, TODO

Same as every repo: AGPL-3.0 `LICENSE` (see [`licensing.md`](licensing.md)), a README or
`CLAUDE.md` stating the repo follows KVG_Standards, and `TODO.md` / `VERSION_BUMP.md` from
`templates/`. A plugin with no third-party dependencies has nothing to check against
AGPL-3.0.

## Not applicable

Theming, Windows installer, update-check (the marketplace handles updates), DB location,
Electron menu and Electron version, logo and icon placement, and release-notes patching
beyond the install blurb in `release-claude-plugin.yml`.
