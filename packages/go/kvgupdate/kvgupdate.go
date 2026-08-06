// Package kvgupdate is a generic GitHub-Releases self-updater for Wails
// (or any Go) desktop apps packaged via KVG_Standards' release-go-gui.yml.
//
// Consumers pin this module to a released KVG_Standards tag in their
// go.mod (go get github.com/gerp93/KVG_Standards/packages/go/kvgupdate@vX.Y.Z)
// — never the module's HEAD via a pseudo-version, see
// ../../../update-check-versioning.md in the KVG_Standards repo.
//
// This is a first-generation port of KVGrainy's Python updater.py to Go —
// the check/download logic is straightforward and low-risk, but the full
// download-extract-replace-relaunch path has not yet been exercised
// end-to-end against a real gameshell-deploy release. Verify it against an
// actual build before shipping it silently in a production app.
package kvgupdate

import (
	"archive/tar"
	"archive/zip"
	"compress/gzip"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"runtime"
	"strconv"
	"strings"
	"time"
)

// UpdateInfo describes an available newer release.
type UpdateInfo struct {
	Version     string // e.g. "1.2.3" (no leading "v")
	DownloadURL string
}

type releaseAsset struct {
	Name               string `json:"name"`
	BrowserDownloadURL string `json:"browser_download_url"`
}

type releaseResponse struct {
	TagName string         `json:"tag_name"`
	Assets  []releaseAsset `json:"assets"`
}

var versionDigits = regexp.MustCompile(`\d+`)

func parseVersion(text string) [3]int {
	core := strings.TrimPrefix(strings.TrimSpace(text), "v")
	if i := strings.Index(core, "-"); i >= 0 {
		core = core[:i]
	}
	pieces := strings.Split(core, ".")
	var out [3]int
	for i := 0; i < 3; i++ {
		if i >= len(pieces) {
			break
		}
		digits := versionDigits.FindString(pieces[i])
		if digits == "" {
			continue
		}
		n, _ := strconv.Atoi(digits)
		out[i] = n
	}
	return out
}

func versionLess(a, b [3]int) bool {
	for i := 0; i < 3; i++ {
		if a[i] != b[i] {
			return a[i] < b[i]
		}
	}
	return false
}

// platformName matches release-go-gui.yml's matrix.platform values.
func platformName() string {
	switch runtime.GOOS {
	case "windows":
		return "windows"
	case "darwin":
		return "macos"
	default:
		return "linux"
	}
}

func archiveExt() string {
	if runtime.GOOS == "windows" {
		return "zip"
	}
	return "tar.gz"
}

// assetName matches release-go-gui.yml's staged package name:
// "{app_name}-{version}-{platform}.{zip|tar.gz}".
func assetName(appName, version string) string {
	return fmt.Sprintf("%s-%s-%s.%s", appName, version, platformName(), archiveExt())
}

// CheckForUpdate queries repo's (e.g. "gerp93/gameshell-deploy") latest
// GitHub Release. Returns nil (no error) if already up to date or the
// expected asset for this platform isn't attached to the release.
func CheckForUpdate(repo, appName, currentVersion string) (*UpdateInfo, error) {
	url := fmt.Sprintf("https://api.github.com/repos/%s/releases/latest", repo)
	req, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Accept", "application/vnd.github+json")

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("kvgupdate: unexpected status %d from %s", resp.StatusCode, url)
	}

	var release releaseResponse
	if err := json.NewDecoder(resp.Body).Decode(&release); err != nil {
		return nil, err
	}

	if !versionLess(parseVersion(currentVersion), parseVersion(release.TagName)) {
		return nil, nil
	}

	// version passed to assetName must match the tag exactly (with "v"
	// prefix stripped is NOT correct here — release-go-gui.yml stages
	// using the full tag, e.g. "v1.2.3", not "1.2.3").
	want := assetName(appName, release.TagName)
	for _, asset := range release.Assets {
		if asset.Name == want {
			return &UpdateInfo{
				Version:     strings.TrimPrefix(release.TagName, "v"),
				DownloadURL: asset.BrowserDownloadURL,
			}, nil
		}
	}
	return nil, nil
}

// DownloadAndExtract downloads info's asset and extracts it into a fresh
// temp directory, returning that directory's path (the staged package
// root, i.e. "{app_name}-{version}-{platform}/" contents).
func DownloadAndExtract(info *UpdateInfo, appName string) (string, error) {
	req, err := http.NewRequest(http.MethodGet, info.DownloadURL, nil)
	if err != nil {
		return "", err
	}
	req.Header.Set("Accept", "application/octet-stream")

	client := &http.Client{Timeout: 60 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("kvgupdate: unexpected status %d downloading asset", resp.StatusCode)
	}

	destDir, err := os.MkdirTemp("", strings.ToLower(appName)+"_update_")
	if err != nil {
		return "", err
	}

	if archiveExt() == "zip" {
		if err := extractZipStream(resp.Body, destDir); err != nil {
			return "", err
		}
	} else {
		if err := extractTarGzStream(resp.Body, destDir); err != nil {
			return "", err
		}
	}
	return destDir, nil
}

func extractTarGzStream(r io.Reader, destDir string) error {
	gz, err := gzip.NewReader(r)
	if err != nil {
		return err
	}
	defer gz.Close()

	tr := tar.NewReader(gz)
	for {
		header, err := tr.Next()
		if err == io.EOF {
			return nil
		}
		if err != nil {
			return err
		}
		target := filepath.Join(destDir, header.Name)
		switch header.Typeflag {
		case tar.TypeDir:
			if err := os.MkdirAll(target, 0o755); err != nil {
				return err
			}
		case tar.TypeReg:
			if err := os.MkdirAll(filepath.Dir(target), 0o755); err != nil {
				return err
			}
			out, err := os.OpenFile(target, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, os.FileMode(header.Mode))
			if err != nil {
				return err
			}
			if _, err := io.Copy(out, tr); err != nil {
				out.Close()
				return err
			}
			out.Close()
		}
	}
}

func extractZipStream(r io.Reader, destDir string) error {
	// zip.Reader needs io.ReaderAt + size, so buffer to a temp file first
	// rather than the whole response body in memory.
	tmp, err := os.CreateTemp("", "kvgupdate_download_*.zip")
	if err != nil {
		return err
	}
	defer os.Remove(tmp.Name())
	defer tmp.Close()

	size, err := io.Copy(tmp, r)
	if err != nil {
		return err
	}

	zr, err := zip.NewReader(tmp, size)
	if err != nil {
		return err
	}

	for _, f := range zr.File {
		target := filepath.Join(destDir, f.Name)
		if f.FileInfo().IsDir() {
			if err := os.MkdirAll(target, 0o755); err != nil {
				return err
			}
			continue
		}
		if err := os.MkdirAll(filepath.Dir(target), 0o755); err != nil {
			return err
		}
		rc, err := f.Open()
		if err != nil {
			return err
		}
		out, err := os.OpenFile(target, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, f.Mode())
		if err != nil {
			rc.Close()
			return err
		}
		_, copyErr := io.Copy(out, rc)
		rc.Close()
		out.Close()
		if copyErr != nil {
			return copyErr
		}
	}
	return nil
}

// findNewBinary locates the extracted package's executable inside
// stagedDir. Matches release-go-gui.yml's exact packaging shape per OS —
// see that workflow's "Stage release package" step.
func findNewBinary(stagedDir, appName string) (string, error) {
	entries, err := os.ReadDir(stagedDir)
	if err != nil {
		return "", err
	}
	// The archive contains one top-level "{app_name}-{version}-{platform}"
	// directory; descend into it if present.
	root := stagedDir
	if len(entries) == 1 && entries[0].IsDir() {
		root = filepath.Join(stagedDir, entries[0].Name())
	}

	switch runtime.GOOS {
	case "windows":
		matches, _ := filepath.Glob(filepath.Join(root, "*.exe"))
		if len(matches) == 0 {
			return "", fmt.Errorf("kvgupdate: no .exe found in %s", root)
		}
		return matches[0], nil
	case "darwin":
		matches, _ := filepath.Glob(filepath.Join(root, "*.app"))
		if len(matches) == 0 {
			return "", fmt.Errorf("kvgupdate: no .app bundle found in %s", root)
		}
		bundle := matches[0]
		binName := strings.TrimSuffix(filepath.Base(bundle), ".app")
		return filepath.Join(bundle, "Contents", "MacOS", binName), nil
	default:
		rootEntries, err := os.ReadDir(root)
		if err != nil {
			return "", err
		}
		for _, e := range rootEntries {
			if !e.IsDir() {
				return filepath.Join(root, e.Name()), nil
			}
		}
		return "", fmt.Errorf("kvgupdate: no binary found in %s", root)
	}
}
