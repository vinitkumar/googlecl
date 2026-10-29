//go:build !windows

package auth

import (
	"context"
	"os"
	"path/filepath"
	"runtime"
	"testing"
	"time"
)

func TestBrowserDoesNotBlock(t *testing.T) {
	dir := t.TempDir()
	launcher := "xdg-open"
	if runtime.GOOS == "darwin" {
		launcher = "open"
	}
	// Some desktop launchers stay alive as long as the browser window does.
	if err := os.WriteFile(filepath.Join(dir, launcher), []byte("#!/bin/sh\nexec /bin/sleep 30\n"), 0700); err != nil {
		t.Fatal(err)
	}
	t.Setenv("PATH", dir+string(os.PathListSeparator)+os.Getenv("PATH"))
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	done := make(chan error, 1)
	go func() { done <- openBrowser(ctx, "https://accounts.google.com/") }()
	select {
	case err := <-done:
		if err != nil {
			t.Fatal(err)
		}
	case <-time.After(time.Second):
		t.Fatal("browser launcher blocked OAuth callback handling")
	}
}
