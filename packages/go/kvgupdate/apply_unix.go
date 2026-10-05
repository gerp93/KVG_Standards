//go:build !windows

package kvgupdate

import (
	"io"
	"os"
	"path/filepath"
	"syscall"
)

// ApplyUpdateAndRestart replaces the running executable (or, on macOS, the
// binary inside the running .app bundle — os.Executable() already resolves
// to that nested path, so no special-casing is needed here) with the one
// found in stagedDir, then exec's into it. Never returns on success.
//
// Before touching the executable, it also syncs every other staged file
// (scripts, templates, docs — whatever the release packaged alongside the
// binary) into targetDir, skipping anything named in preserve (operator
// data that must survive an update untouched, e.g. gameshell-deploy's
// "games" directory). Pass the app's own ops/install directory as
// targetDir — for an app with no such split, its own directory (the one
// holding the executable) is a reasonable targetDir.
func ApplyUpdateAndRestart(stagedDir, appName, targetDir string, preserve []string) error {
	newBinary, err := findNewBinary(stagedDir, appName)
	if err != nil {
		return err
	}
	currentExe, err := os.Executable()
	if err != nil {
		return err
	}
	currentExe, err = filepath.Abs(currentExe)
	if err != nil {
		return err
	}

	root, err := packageRoot(stagedDir)
	if err != nil {
		return err
	}
	skipName, err := topLevelName(root, newBinary)
	if err != nil {
		return err
	}
	preserveNames := make(map[string]bool, len(preserve))
	for _, p := range preserve {
		preserveNames[p] = true
	}
	if err := syncStagedFiles(root, targetDir, map[string]bool{skipName: true}, preserveNames); err != nil {
		return err
	}

	if err := replaceFile(newBinary, currentExe); err != nil {
		return err
	}
	if err := os.Chmod(currentExe, 0o755); err != nil {
		return err
	}

	return syscall.Exec(currentExe, os.Args, os.Environ())
}

// replaceFile copies src over dst rather than os.Rename, since the staged
// download and the current executable may live on different filesystems
// (temp dir vs. install dir), where rename fails with EXDEV.
func replaceFile(src, dst string) error {
	in, err := os.Open(src)
	if err != nil {
		return err
	}
	defer in.Close()

	out, err := os.OpenFile(dst, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0o755)
	if err != nil {
		return err
	}
	if _, err := io.Copy(out, in); err != nil {
		out.Close()
		return err
	}
	return out.Close()
}
