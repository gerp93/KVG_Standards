# kvgupdate

Generic GitHub-Releases self-updater for Go desktop apps (Wails, or plain
Go) packaged via `release-go-gui.yml`. First-generation port of
`kvg-updater`'s (Python) logic — see that package's README for the
KVGrainy origin story.

**Not yet verified end-to-end against a real build.** The check/download
logic is plain HTTP+JSON and low-risk; the extract-and-replace path uses
well-established OS techniques (the same Windows self-delete-batch trick
and Unix `exec` swap as `kvg-updater`) but hasn't been run against an
actual `gameshell-deploy` release yet. Verify before shipping silently.

## Install

Pin to a released tag — never a `@main`/pseudo-version:

```
go get github.com/gerp93/KVG_Standards/packages/go/kvgupdate@v0.3.0
```

## Usage

```go
import "github.com/gerp93/KVG_Standards/packages/go/kvgupdate"

const (
    githubRepo     = "gerp93/gameshell-deploy"
    appName        = "gameshell-deploy-gui"
    currentVersion = "1.2.3" // however this app tracks its own build version
)

func checkAndApplyUpdate() error {
    info, err := kvgupdate.CheckForUpdate(githubRepo, appName, currentVersion)
    if err != nil || info == nil {
        return err // nil, nil means already up to date
    }
    stagedDir, err := kvgupdate.DownloadAndExtract(info, appName)
    if err != nil {
        return err
    }
    return kvgupdate.ApplyUpdateAndRestart(stagedDir, appName) // does not return on success
}
```

Asset naming assumes `release-go-gui.yml`'s staged package name
(`{app_name}-{version}-{platform}.{zip|tar.gz}`) — no extra config needed
if you're already using that workflow.
