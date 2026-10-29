package auth

import (
	"context"
	"crypto/sha256"
	"encoding/base64"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"golang.org/x/oauth2"
)

type authorizationWriter struct{ url chan string }

func (w authorizationWriter) Write(data []byte) (int, error) {
	for _, line := range strings.Split(string(data), "\n") {
		if strings.HasPrefix(line, "https://accounts.google.com/") {
			w.url <- line
		}
	}
	return len(data), nil
}

type oauthTransport func(*http.Request) (*http.Response, error)

func (f oauthTransport) RoundTrip(r *http.Request) (*http.Response, error) { return f(r) }

func TestLoginStateAndPKCE(t *testing.T) {
	t.Setenv("GOOGLECL_CONFIG_DIR", t.TempDir())
	path := filepath.Join(t.TempDir(), "client.json")
	if err := os.WriteFile(path, []byte(`{"installed":{"client_id":"test-client","client_secret":"test-secret"}}`), 0600); err != nil {
		t.Fatal(err)
	}
	urls := make(chan string, 1)
	result := make(chan error, 1)
	verifier := make(chan string, 1)
	fakeClient := &http.Client{Transport: oauthTransport(func(r *http.Request) (*http.Response, error) {
		if r.URL.Host != "oauth2.googleapis.com" {
			return nil, fmt.Errorf("unexpected OAuth host %s", r.URL.Host)
		}
		if err := r.ParseForm(); err != nil {
			return nil, err
		}
		verifier <- r.Form.Get("code_verifier")
		if r.Form.Get("code") != "callback-code" {
			return nil, fmt.Errorf("wrong authorization code")
		}
		return &http.Response{StatusCode: 200, Header: http.Header{"Content-Type": []string{"application/json"}}, Body: io.NopCloser(strings.NewReader(`{"access_token":"access","refresh_token":"refresh","token_type":"Bearer","expires_in":3600}`))}, nil
	})}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	ctx = context.WithValue(ctx, oauth2.HTTPClient, fakeClient)
	opts := LoginOptions{Profile: "default", Service: "docs", Credentials: path, NoBrowser: true}
	go func() { result <- Login(ctx, opts, authorizationWriter{url: urls}) }()
	var authorization string
	select {
	case authorization = <-urls:
	case err := <-result:
		t.Fatalf("login ended early: %v", err)
	case <-ctx.Done():
		t.Fatal(ctx.Err())
	}
	parsed, err := url.Parse(authorization)
	if err != nil {
		t.Fatal(err)
	}
	query := parsed.Query()
	if query.Get("code_challenge_method") != "S256" || query.Get("state") == "" {
		t.Fatal("missing PKCE/state")
	}
	if strings.Contains(query.Get("scope"), "calendar") {
		t.Fatal("unrelated service scope requested")
	}
	callback := query.Get("redirect_uri")
	response, err := http.Get(callback + "?state=wrong&code=attacker")
	if err != nil {
		t.Fatal(err)
	}
	response.Body.Close()
	if response.StatusCode != http.StatusBadRequest {
		t.Fatalf("invalid state status = %d", response.StatusCode)
	}
	response, err = http.Get(callback + "?state=" + url.QueryEscape(query.Get("state")) + "&code=callback-code")
	if err != nil {
		t.Fatal(err)
	}
	response.Body.Close()
	if err := <-result; err != nil {
		t.Fatal(err)
	}
	digest := sha256.Sum256([]byte(<-verifier))
	if query.Get("code_challenge") != base64.RawURLEncoding.EncodeToString(digest[:]) {
		t.Fatal("PKCE verifier mismatch")
	}
	status, err := TokenStatus("default", "docs")
	if err != nil || status != "authenticated" {
		t.Fatalf("status=%s error=%v", status, err)
	}
	opts.Credentials = ""
	if _, err := loadOAuthConfig(opts); err != nil {
		t.Fatal("login did not persist client settings:", err)
	}
	if err := Logout("default", "docs"); err != nil {
		t.Fatal(err)
	}
	status, err = TokenStatus("default", "docs")
	if err != nil || status != "not authenticated" {
		t.Fatalf("logout status=%s error=%v", status, err)
	}
}

func TestLoginTermination(t *testing.T) {
	for _, scenario := range []string{"cancel", "deadline", "denied"} {
		t.Run(scenario, func(t *testing.T) {
			t.Setenv("GOOGLECL_CONFIG_DIR", t.TempDir())
			path := filepath.Join(t.TempDir(), "client.json")
			if err := os.WriteFile(path, []byte(`{"installed":{"client_id":"test-client"}}`), 0600); err != nil {
				t.Fatal(err)
			}
			ctx, cancel := context.WithCancel(context.Background())
			defer cancel()
			if scenario == "deadline" {
				var stop context.CancelFunc
				ctx, stop = context.WithDeadline(ctx, time.Now().Add(-time.Second))
				defer stop()
			}
			urls := make(chan string, 1)
			result := make(chan error, 1)
			go func() {
				result <- Login(ctx, LoginOptions{Profile: "default", Service: "docs", Credentials: path, NoBrowser: true}, authorizationWriter{url: urls})
			}()
			var authorization string
			select {
			case authorization = <-urls:
			case <-time.After(5 * time.Second):
				t.Fatal("login did not start")
			}
			parsed, err := url.Parse(authorization)
			if err != nil {
				t.Fatal(err)
			}
			callback := parsed.Query().Get("redirect_uri")
			switch scenario {
			case "cancel":
				cancel()
			case "denied":
				response, err := http.Post(callback, "text/plain", strings.NewReader(""))
				if err != nil {
					t.Fatal(err)
				}
				response.Body.Close()
				if response.StatusCode != http.StatusMethodNotAllowed {
					t.Fatal("accepted POST callback")
				}
				response, err = http.Get(callback + "?state=" + parsed.Query().Get("state") + "&error=access_denied")
				if err != nil {
					t.Fatal(err)
				}
				response.Body.Close()
			}
			select {
			case err := <-result:
				if err == nil {
					t.Fatal("login succeeded without authorization")
				}
				if scenario == "cancel" && !errors.Is(err, context.Canceled) {
					t.Fatal(err)
				}
				if scenario == "deadline" && !errors.Is(err, context.DeadlineExceeded) {
					t.Fatal(err)
				}
				if scenario == "denied" && !strings.Contains(err.Error(), "denied") {
					t.Fatal(err)
				}
			case <-time.After(5 * time.Second):
				t.Fatal("login did not terminate")
			}
			client := &http.Client{Timeout: time.Second}
			if response, err := client.Get(callback); err == nil {
				response.Body.Close()
				t.Fatal("callback listener still open")
			}
			status, err := TokenStatus("default", "docs")
			if err != nil || status != "not authenticated" {
				t.Fatalf("status=%s err=%v", status, err)
			}
		})
	}
}
