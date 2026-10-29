package auth

import (
	"context"
	"errors"
	"io"
	"net"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"golang.org/x/oauth2"
)

func TestLoginCallbackResponse(t *testing.T) {
	for _, test := range []struct {
		name, query, body, loginError string
		status                        int
	}{
		{"denied", "error=access_denied", "authorization denied\n", "authorization denied", http.StatusBadRequest},
		{"exchange-failed", "code=test-code", "Authorization received. Return to your terminal.\n", "exchange OAuth code", http.StatusOK},
	} {
		t.Run(test.name, func(t *testing.T) {
			t.Setenv("GOOGLECL_CONFIG_DIR", t.TempDir())
			path := filepath.Join(t.TempDir(), "client.json")
			if err := os.WriteFile(path, []byte(`{"installed":{"client_id":"test-client"}}`), 0600); err != nil {
				t.Fatal(err)
			}
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cancel()
			// Immediate exchange failure must not truncate the browser response either.
			ctx = context.WithValue(ctx, oauth2.HTTPClient, &http.Client{Transport: oauthTransport(func(r *http.Request) (*http.Response, error) {
				return nil, errors.New("test exchange failure")
			})})
			urls := make(chan string, 1)
			result := make(chan error, 1)
			go func() {
				result <- Login(ctx, LoginOptions{Profile: "default", Service: "docs", Credentials: path, NoBrowser: true}, authorizationWriter{url: urls})
			}()
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
			callback := parsed.Query().Get("redirect_uri") + "?state=" + parsed.Query().Get("state") + "&" + test.query
			// A fresh connection exposes premature closure without an automatic retry.
			transport := &http.Transport{DisableKeepAlives: true}
			defer transport.CloseIdleConnections()
			client := &http.Client{Transport: transport, Timeout: 5 * time.Second}
			response, err := client.Get(callback)
			if err != nil {
				t.Fatalf("callback response lost: %v", err)
			}
			defer response.Body.Close()
			body, err := io.ReadAll(response.Body)
			if err != nil {
				t.Fatal(err)
			}
			if response.StatusCode != test.status || string(body) != test.body {
				t.Fatalf("callback status=%d body=%q", response.StatusCode, body)
			}
			select {
			case err := <-result:
				if err == nil || !strings.Contains(err.Error(), test.loginError) {
					t.Fatalf("login error=%v", err)
				}
			case <-ctx.Done():
				t.Fatal(ctx.Err())
			}
		})
	}
}

func TestLoginCancelOpenConn(t *testing.T) {
	t.Setenv("GOOGLECL_CONFIG_DIR", t.TempDir())
	path := filepath.Join(t.TempDir(), "client.json")
	if err := os.WriteFile(path, []byte(`{"installed":{"client_id":"test-client"}}`), 0600); err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	urls := make(chan string, 1)
	result := make(chan error, 1)
	go func() {
		result <- Login(ctx, LoginOptions{Profile: "default", Service: "docs", Credentials: path, NoBrowser: true}, authorizationWriter{url: urls})
	}()
	var authorization string
	select {
	case authorization = <-urls:
	case err := <-result:
		t.Fatalf("login ended early: %v", err)
	case <-time.After(5 * time.Second):
		t.Fatal("login did not start")
	}
	parsed, err := url.Parse(authorization)
	if err != nil {
		t.Fatal(err)
	}
	callback, err := url.Parse(parsed.Query().Get("redirect_uri"))
	if err != nil {
		t.Fatal(err)
	}
	conn, err := net.DialTimeout("tcp", callback.Host, time.Second)
	if err != nil {
		t.Fatal(err)
	}
	defer conn.Close()
	if err := conn.SetDeadline(time.Now().Add(3 * time.Second)); err != nil {
		t.Fatal(err)
	}
	// An incomplete request must not keep a canceled login alive indefinitely.
	if _, err := io.WriteString(conn, "GET /oauth/callback HTTP/1.1\r\nHost: localhost\r\n"); err != nil {
		t.Fatal(err)
	}
	cancel()
	select {
	case err := <-result:
		if !errors.Is(err, context.Canceled) {
			t.Fatalf("login error=%v", err)
		}
	case <-time.After(3 * time.Second):
		t.Fatal("unfinished callback request blocked cancellation")
	}
	if _, err := conn.Read(make([]byte, 1)); err == nil {
		t.Fatal("canceled callback connection remained readable")
	} else if networkError, ok := err.(net.Error); ok && networkError.Timeout() {
		t.Fatal("canceled callback connection remained open")
	}
}
