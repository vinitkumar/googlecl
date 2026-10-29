package auth

import (
	"os"
	"path/filepath"
	"testing"

	"golang.org/x/oauth2"
)

func TestTokenRoundTrip(t *testing.T) {
	path := filepath.Join(t.TempDir(), "tokens", "token.json")
	token := &oauth2.Token{AccessToken: "access", RefreshToken: "refresh", TokenType: "Bearer"}
	if err := saveToken(path, token); err != nil {
		t.Fatal(err)
	}
	got, err := loadToken(path)
	if err != nil {
		t.Fatal(err)
	}
	if got.RefreshToken != "refresh" {
		t.Fatalf("refresh token = %q", got.RefreshToken)
	}
	info, err := os.Stat(path)
	if err != nil {
		t.Fatal(err)
	}
	if info.Mode().Perm()&0077 != 0 && os.PathSeparator != '\\' {
		t.Fatalf("unsafe permissions: %v", info.Mode())
	}
}

func TestTokenPathIsolation(t *testing.T) {
	t.Setenv("GOOGLECL_CONFIG_DIR", t.TempDir())
	a, err := tokenPath("../../user", "docs")
	if err != nil {
		t.Fatal(err)
	}
	b, _ := tokenPath("other", "docs")
	c, _ := tokenPath("../../user", "calendar")
	if a == b || a == c {
		t.Fatal("profiles and scopes must not share tokens")
	}
	if filepath.Dir(a) != filepath.Join(os.Getenv("GOOGLECL_CONFIG_DIR"), "tokens") {
		t.Fatal("profile escaped token directory")
	}
}

func TestUnsupportedScope(t *testing.T) {
	if _, err := serviceScopes("picasa"); err == nil {
		t.Fatal("expected unsupported service error")
	}
}
