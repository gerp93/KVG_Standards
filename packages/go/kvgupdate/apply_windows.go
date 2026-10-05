//go:build windows

package kvgupdate

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"
)

// ApplyUpdateAndRestart replaces the running executable with the one found
// in stagedDir and relaunches it. Never returns on success.
//
// Before touching the executable, it also syncs every other staged file
// (scripts, templates, docs — whatever the release packaged alongside the
// binary) into targetDir, skipping anything named in preserve (operator
// data that must survive an update untouched, e.g. gameshell-deploy's
// "games" directory). Pass the app's own ops/install directory as
// targetDir — for an app with no such split, its own directory (the one
// holding the executable) is a reasonable targetDir.
//
// Same shape as kvg-updater's Python/PyInstaller equivalent: the running
// exe can't overwrite itself on Windows, so a detached batch script polls
// for it to become deletable, moves the new binary into place, and
// relaunches — then this process exits immediately, before the script's
// delete-retry loop can race it.
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

	slug := strings.ToLower(strings.ReplaceAll(appName, " ", "_"))
	scriptPath := filepath.Join(filepath.Dir(newBinary), slug+"_update.bat")
	script := "@echo off\r\n" +
		":retry\r\n" +
		fmt.Sprintf("del \"%s\" >nul 2>&1\r\n", currentExe) +
		fmt.Sprintf("if exist \"%s\" (\r\n", currentExe) +
		"  timeout /t 1 /nobreak >nul 2>&1\r\n" +
		"  goto retry\r\n" +
		")\r\n" +
		fmt.Sprintf("move /y \"%s\" \"%s\" >nul 2>&1\r\n", newBinary, currentExe) +
		"timeout /t 2 /nobreak >nul 2>&1\r\n" +
		fmt.Sprintf("explorer.exe \"%s\"\r\n", currentExe) +
		"del \"%~f0\"\r\n"

	if err := os.WriteFile(scriptPath, []byte(script), 0o644); err != nil {
		return err
	}

	cmd := exec.Command("cmd", "/c", scriptPath)
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true, CreationFlags: 0x08000000} // CREATE_NO_WINDOW
	if err := cmd.Start(); err != nil {
		return err
	}

	os.Exit(0)
	return nil // unreachable
}
