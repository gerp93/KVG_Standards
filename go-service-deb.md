# Go service as a .deb (headless server)

A headless Go service (a server with no window that runs on the house server or another Debian/Ubuntu machine)
ships as **one static binary**, packed as an `amd64` `.deb` with its systemd unit, settings file and maintainer
scripts, attached to the repo's GitHub Release. The install is `sudo apt install ./app_1.2.3_amd64.deb`; there is
no Go to install and no Docker. The workflow is [`.github/workflows/release-go-deb.yml`](.github/workflows/release-go-deb.yml).
First consumer: [kvg-mcp-gateway](https://github.com/gerp93/kvg-mcp-gateway), the house server's MCP gateway. Approved 2026-11-28
(the owner asked for the gateway to be built in Go, which needed this stack). It is the Go sibling of
[`node-service-deb.md`](node-service-deb.md) and extends [`deb-packaging.md`](deb-packaging.md): read those first;
the rules not repeated here are the same.

## The rule: one source, no drift

1. **Built from the repo's own code.** The workflow runs `go build` on `main_package` (for example `./cmd/kvg-mcp-gateway`)
   from the tag's checkout. No `debian/` copy of the code, no hand-built binary attached to a release.
2. **Same commit, same tag, same run.** The `go-deb` job is in **both** `auto-release.yml` and `cut-release.yml`
   with identical inputs. In a repo whose only release asset is the `.deb`, it creates the Release itself
   (`generate_release_notes: true`).
3. **Same version string.** The tag's version (`v1.2.3` becomes `1.2.3`) is baked in with
   `-ldflags "-X main.version=1.2.3"` (`version_var` names another variable). No version file to keep in step.
4. **A smoke test enforces it.** The workflow installs the `.deb` on the runner, runs `<command> --version`, fails
   unless the output has the tag's version, then removes and purges the package and checks the command is gone.
5. **Tests run first.** `go vet ./...` and `test_command` (default `go test ./...`) run before the build.

## What the package is

- **One static binary**: `CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -trimpath -ldflags "-s -w -X ..."`. It
  needs nothing from apt (`Depends: adduser` by default, for the maintainer scripts). The Go version is the one in
  `go.mod` (`go-version-file`).
- **Inputs shared with `release-node-deb.yml`**: `install_map` (`<path> <absolute path> [mode]`, files or folders
  from the checkout), `symlinks`, `conffiles`, `scripts_dir`, `depends`, `smoke_args`, `publish`.
- **Layout**: the binary at `/usr/lib/<package_name>/<command_name>` (0755) with a `/usr/bin/<command_name>`
  symlink, units in `/usr/lib/systemd/system/`, settings in `/etc/<package_name>/` as conffiles, data in
  `/var/lib/<package_name>/` created by the maintainer scripts (kept on `remove`, deleted on `purge`).
- **Maintainer scripts** from `scripts_dir`, as in `deb-packaging.md`: create the system user, enable the unit,
  re-runnable, no failure without systemd (`[ -d /run/systemd/system ]`). A service whose settings must be filled in
  first (an address, a sign-in) is **enabled but not started** until its own config check passes.
- **Units** carry `MemoryMax=` (warned when missing), run as the package's own user with `NoNewPrivileges=yes`,
  `ProtectSystem=strict` and `ReadWritePaths=/var/lib/<package_name>`, and listen on **localhost only**.
- `ci.yml` calls the same workflow on pull requests with `version: v0.0.0` and `publish: false`, next to
  `ci-go.yml` with `run_tests: true`.

## Secrets

As [`secrets.md`](secrets.md): never in the package or a conffile default. A service keeps its secrets in
`/etc/<package_name>/secrets.json`, made by the owner, mode 0600, owned by the service user, and **refuses to
start** when the file is readable by anyone else. The settings file names which secret each part uses.

## Internet-facing services (remote MCP gateway)

`node-service-deb.md` says a service that can change files is never reachable from the public internet. A **remote
MCP gateway** is the one exception, because its whole job is to let Claude on the owner's phone reach the house
server from anywhere. It is allowed only in this shape, which kvg-mcp-gateway follows:

- **One gateway per machine**, the only thing on the box that faces the internet. Apps stay on localhost and are
  reached only through it; no app gets its own tunnel, port-forward or Funnel.
- **Behind Cloudflare Tunnel and Cloudflare Access** (Managed OAuth for Claude's connector sign-in), so nothing
  reaches the gateway without an Access session for the one allowed account. The gateway listens on `127.0.0.1`
  and **re-checks Access's signed pass** (the `Cf-Access-Jwt-Assertion` JWT: signature against the team's keys,
  issuer, audience tag, expiry and the allowed email) on every request, so a tunnel or Access mistake does not open
  it. A GitHub OAuth fallback built into the gateway is allowed for when Access is not used; it signs in only the one
  allowed GitHub login and accepts only Claude's callback addresses.
- **Allow list**: only tools named in the settings file exist. No shell, no generic HTTP fetch, no file browser.
- **Read-only by default.** A tool that changes something is split into `_prepare` (changes nothing, returns a plain
  summary and a one-time code) and `_confirm` (does exactly that, once, within minutes), so Claude must show the
  owner the summary and get a yes first. Apps that already confirm keep their own confirmation too.
- **Every call is logged** (who, tool, a summary of the arguments with secret-looking keys blanked, result) and a
  tool does not run if its log line cannot be written. Results are marked as data, never instructions.
- **Limits**: calls per minute, answer size, a timeout on every app call.
- Tools that can delete user files at scale (Sweeper) are **not** exposed through a gateway.

## Not covered (yet)

- arm64, signing and an apt repository (bring the design here first).
- Automatic updates: upgrades are `sudo apt install ./new.deb`.
