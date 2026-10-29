package config

import (
	"os"
	"path/filepath"
	"testing"
)

func TestConfigDirIsIsolated(t *testing.T) {
	legacy := t.TempDir()
	t.Setenv("XDG_CONFIG_HOME", legacy)
	t.Setenv("GOOGLECL_CONFIG_DIR", t.TempDir())
	dir := filepath.Join(legacy, "googlecl")
	if err := os.MkdirAll(dir, 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, "config"), []byte("[GENERAL]\nuser = unrelated\n"), 0600); err != nil {
		t.Fatal(err)
	}
	settings, err := LoadSettings("")
	if err != nil {
		t.Fatal(err)
	}
	if got := settings.Value("docs", "user", "default"); got != "default" {
		t.Fatalf("loaded unrelated profile %q", got)
	}
}
