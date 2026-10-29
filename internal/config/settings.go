// Package config reads legacy INI settings without modifying them.
package config

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"gopkg.in/ini.v1"
)

// Settings resolves service options before GENERAL options.
type Settings struct{ file *ini.File }

// ConfigDir honors GOOGLECL_CONFIG_DIR for isolated installations and tests.
func ConfigDir() (string, error) {
	if path := os.Getenv("GOOGLECL_CONFIG_DIR"); path != "" {
		return path, nil
	}
	path, err := os.UserConfigDir()
	if err != nil {
		return "", fmt.Errorf("config directory: %w", err)
	}
	return filepath.Join(path, "googlecl"), nil
}

// LoadSettings reads an explicit file or the existing legacy config path.
func LoadSettings(path string) (*Settings, error) {
	if path == "" {
		dir, err := ConfigDir()
		if err != nil {
			return nil, err
		}
		path = filepath.Join(dir, "config")
		if _, err := os.Stat(path); os.IsNotExist(err) {
			// An explicit directory must not inherit another installation's settings.
			if os.Getenv("GOOGLECL_CONFIG_DIR") != "" {
				return &Settings{file: ini.Empty()}, nil
			}
			// Older releases used XDG paths even on macOS and Windows.
			home, homeErr := os.UserHomeDir()
			if homeErr != nil {
				return nil, homeErr
			}
			base := os.Getenv("XDG_CONFIG_HOME")
			if base == "" {
				base = filepath.Join(home, ".config")
			}
			path = filepath.Join(base, "googlecl", "config")
			if _, err := os.Stat(path); os.IsNotExist(err) {
				return &Settings{file: ini.Empty()}, nil
			}
		}
	}
	file, err := ini.LoadSources(ini.LoadOptions{Insensitive: true}, path)
	if err != nil {
		return nil, fmt.Errorf("read legacy config: %w", err)
	}
	return &Settings{file: file}, nil
}

// Value returns an option from a service section, GENERAL, or the fallback.
func (s *Settings) Value(service, key, fallback string) string {
	for _, section := range []string{strings.ToLower(service), "general"} {
		if s.file.Section(section).HasKey(key) {
			return s.file.Section(section).Key(key).String()
		}
	}
	return fallback
}
