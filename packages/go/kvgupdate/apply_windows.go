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
// Same shape as kvg-updater's Python/PyInstaller equivalent: the running
// exe can't overwrite itself on Windows, so a detached batch script polls
// for it to become deletable, moves the new binary into place, and
// relaunches — then this process exits immediately, before the script's
// delete-retry loop can race it.
func ApplyUpdateAndRestart(stagedDir, appName string) error {
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
