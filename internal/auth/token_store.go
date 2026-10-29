// Package auth owns desktop OAuth credentials and per-profile token storage.
package auth

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"

	"github.com/vinitkumar/googlecl/internal/config"
	"golang.org/x/oauth2"
)

func tokenPath(profile, service string) (string, error) {
	dir, err := config.ConfigDir()
	if err != nil {
		return "", err
	}
	sum := sha256.Sum256([]byte(profile + "\x00" + service))
	return filepath.Join(dir, "tokens", fmt.Sprintf("%x.json", sum[:16])), nil
}

func loadToken(path string) (*oauth2.Token, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read OAuth token: %w", err)
	}
	var token oauth2.Token
	if err := json.Unmarshal(data, &token); err != nil {
		return nil, fmt.Errorf("decode OAuth token: %w", err)
	}
	return &token, nil
}

func saveToken(path string, token *oauth2.Token) error {
	return savePrivateJSON(path, token)
}

func saveClientConfig(opts LoginOptions, cfg *oauth2.Config) error {
	path, err := tokenPath(opts.Profile, opts.Service)
	if err != nil {
		return err
	}
	return savePrivateJSON(path+".client.json", map[string]any{
		"installed": map[string]string{"client_id": cfg.ClientID, "client_secret": cfg.ClientSecret},
	})
}

func savePrivateJSON(path string, value any) error {
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0700); err != nil {
		return fmt.Errorf("create token directory: %w", err)
	}
	// Create with private permissions before writing; rename prevents partial reads.
	file, err := os.CreateTemp(dir, ".token-*")
	if err != nil {
		return err
	}
	defer os.Remove(file.Name())
	if err := json.NewEncoder(file).Encode(value); err != nil {
		file.Close()
		return err
	}
	if err := file.Sync(); err != nil {
		file.Close()
		return err
	}
	if err := file.Close(); err != nil {
		return err
	}
	if err := os.Rename(file.Name(), path); err != nil {
		return fmt.Errorf("save OAuth token: %w", err)
	}
	return nil
}

type storedTokenSource struct {
	mu     sync.Mutex
	source oauth2.TokenSource
	path   string
	last   *oauth2.Token
}

func (s *storedTokenSource) Token() (*oauth2.Token, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	token, err := s.source.Token()
	if err != nil {
		return nil, fmt.Errorf("refresh OAuth token; run google auth login again: %w", err)
	}
	if s.last == nil || token.AccessToken != s.last.AccessToken || token.RefreshToken != s.last.RefreshToken || !token.Expiry.Equal(s.last.Expiry) {
		if err := saveToken(s.path, token); err != nil {
			return nil, err
		}
		s.last = token
	}
	return token, nil
}
