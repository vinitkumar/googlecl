package auth

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
	"time"

	"golang.org/x/oauth2"
)

func TestRefreshPersistsToken(t *testing.T) {
	calls := 0
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		calls++
		if err := r.ParseForm(); err != nil {
			t.Error(err)
		}
		if r.Form.Get("refresh_token") != "saved-refresh" {
			t.Error("missing refresh token")
		}
		w.Header().Set("Content-Type", "application/json")
		fmt.Fprint(w, `{"access_token":"renewed","expires_in":3600,"token_type":"Bearer"}`)
	}))
	defer server.Close()
	cfg := &oauth2.Config{ClientID: "client", Endpoint: oauth2.Endpoint{TokenURL: server.URL}}
	token := &oauth2.Token{AccessToken: "expired", RefreshToken: "saved-refresh", Expiry: time.Now().Add(-time.Hour)}
	path := filepath.Join(t.TempDir(), "token.json")
	source := &storedTokenSource{source: cfg.TokenSource(context.Background(), token), path: path, last: token}
	got, err := source.Token()
	if err != nil {
		t.Fatal(err)
	}
	if got.AccessToken != "renewed" {
		t.Fatalf("token=%q", got.AccessToken)
	}
	saved, err := loadToken(path)
	if err != nil {
		t.Fatal(err)
	}
	if saved.AccessToken != "renewed" || saved.RefreshToken != "saved-refresh" {
		t.Fatal("refresh did not persist credentials")
	}
	if _, err := source.Token(); err != nil {
		t.Fatal(err)
	}
	if calls != 1 {
		t.Fatalf("refresh calls=%d", calls)
	}
}

func TestLoginRemembersClient(t *testing.T) {
	t.Setenv("GOOGLECL_CONFIG_DIR", t.TempDir())
	cfg := &oauth2.Config{ClientID: "desktop-client", ClientSecret: "desktop-secret"}
	opts := LoginOptions{Profile: "alice", Service: "docs"}
	if err := saveClientConfig(opts, cfg); err != nil {
		t.Fatal(err)
	}
	loaded, err := loadOAuthConfig(opts)
	if err != nil {
		t.Fatal(err)
	}
	if loaded.ClientID != cfg.ClientID {
		t.Fatal("stored client was not reused")
	}
	other := opts
	other.Profile = "bob"
	if _, err := loadOAuthConfig(other); err == nil {
		t.Fatal("profiles shared client credentials")
	}
}

func TestCredentialEndpointsIgnored(t *testing.T) {
	path := filepath.Join(t.TempDir(), "client.json")
	data := map[string]any{"installed": map[string]string{"client_id": "client", "client_secret": "secret", "token_uri": "https://attacker.invalid/token"}}
	encoded, _ := json.Marshal(data)
	if err := os.WriteFile(path, encoded, 0600); err != nil {
		t.Fatal(err)
	}
	cfg, err := loadOAuthConfig(LoginOptions{Credentials: path, Service: "docs"})
	if err != nil {
		t.Fatal(err)
	}
	if cfg.Endpoint.TokenURL == "https://attacker.invalid/token" {
		t.Fatal("trusted supplied token endpoint")
	}
}
