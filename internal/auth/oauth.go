package auth

import (
	"context"
	"crypto/rand"
	"crypto/subtle"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"time"

	"github.com/vinitkumar/googlecl/internal/config"
	"golang.org/x/oauth2"
	"golang.org/x/oauth2/google"
)

const (
	loginTimeout            = 5 * time.Minute
	callbackShutdownTimeout = time.Second
)

// LoginOptions identifies a named local profile, not a verified Google identity.
type LoginOptions struct {
	Profile     string
	Service     string
	Credentials string
	NoBrowser   bool
}

func serviceScopes(service string) ([]string, error) {
	switch service {
	case "docs":
		return []string{"https://www.googleapis.com/auth/drive"}, nil
	case "calendar":
		return []string{"https://www.googleapis.com/auth/calendar"}, nil
	case "contacts":
		return []string{"https://www.googleapis.com/auth/contacts.readonly"}, nil
	default:
		return nil, fmt.Errorf("OAuth service %q is not supported; choose docs, calendar, or contacts", service)
	}
}

func loadOAuthConfig(opts LoginOptions) (*oauth2.Config, error) {
	scopes, err := serviceScopes(opts.Service)
	if err != nil {
		return nil, err
	}
	path := opts.Credentials
	if path == "" {
		saved, err := tokenPath(opts.Profile, opts.Service)
		if err != nil {
			return nil, err
		}
		if _, err := os.Stat(saved + ".client.json"); err == nil {
			path = saved + ".client.json"
		}
	}
	if path == "" {
		dir, err := config.ConfigDir()
		if err != nil {
			return nil, err
		}
		path = filepath.Join(dir, "credentials.json")
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read OAuth desktop credentials (use --credentials PATH): %w", err)
	}
	var desktop struct {
		Installed *struct {
			ClientID     string `json:"client_id"`
			ClientSecret string `json:"client_secret"`
		} `json:"installed"`
	}
	if err := json.Unmarshal(data, &desktop); err != nil {
		return nil, fmt.Errorf("decode OAuth credentials: %w", err)
	}
	if desktop.Installed == nil || desktop.Installed.ClientID == "" {
		return nil, errors.New("OAuth credentials must be a Google Desktop app client")
	}
	// Never send tokens to endpoints supplied by an untrusted credentials file.
	return &oauth2.Config{ClientID: desktop.Installed.ClientID, ClientSecret: desktop.Installed.ClientSecret, Endpoint: google.Endpoint, Scopes: scopes}, nil
}

// AuthorizedClient refreshes credentials without starting an interactive login.
func AuthorizedClient(ctx context.Context, opts LoginOptions) (*http.Client, error) {
	// Bound token refresh independently of API request timeouts.
	ctx = context.WithValue(ctx, oauth2.HTTPClient, &http.Client{Timeout: 30 * time.Second})
	cfg, err := loadOAuthConfig(opts)
	if err != nil {
		return nil, err
	}
	path, err := tokenPath(opts.Profile, opts.Service)
	if err != nil {
		return nil, err
	}
	token, err := loadToken(path)
	if err != nil {
		return nil, fmt.Errorf("not authenticated; run google auth login --service %s --user %q: %w", opts.Service, opts.Profile, err)
	}
	source := &storedTokenSource{source: cfg.TokenSource(ctx, token), path: path, last: token}
	client := oauth2.NewClient(ctx, source)
	client.Timeout = 2 * time.Minute
	return client, nil
}

// Login uses a loopback callback with state validation and PKCE, never OOB codes.
func Login(ctx context.Context, opts LoginOptions, out io.Writer) error {
	ctx, cancel := context.WithTimeout(ctx, loginTimeout)
	defer cancel()
	cfg, err := loadOAuthConfig(opts)
	if err != nil {
		return err
	}
	path, err := tokenPath(opts.Profile, opts.Service)
	if err != nil {
		return err
	}
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		return fmt.Errorf("OAuth callback listener: %w", err)
	}
	defer listener.Close()
	cfg.RedirectURL = "http://" + listener.Addr().String() + "/oauth/callback"
	random := make([]byte, 32)
	if _, err := rand.Read(random); err != nil {
		return err
	}
	state := hex.EncodeToString(random)
	verifier := oauth2.GenerateVerifier()
	result := make(chan string, 1)
	mux := http.NewServeMux()
	mux.HandleFunc("/oauth/callback", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		if subtle.ConstantTimeCompare([]byte(r.URL.Query().Get("state")), []byte(state)) != 1 {
			http.Error(w, "invalid OAuth state", http.StatusBadRequest)
			return
		}
		code := r.URL.Query().Get("code")
		select {
		case result <- code:
		default:
			http.Error(w, "callback already received", http.StatusConflict)
			return
		}
		if code == "" {
			http.Error(w, "authorization denied", http.StatusBadRequest)
			return
		}
		fmt.Fprintln(w, "Authorization received. Return to your terminal.")
	})
	server := &http.Server{Handler: mux, ReadHeaderTimeout: 5 * time.Second}
	defer func() {
		// Let the callback response finish, even after denial or cancellation.
		shutdown, stop := context.WithTimeout(context.Background(), callbackShutdownTimeout)
		defer stop()
		if err := server.Shutdown(shutdown); err != nil {
			_ = server.Close()
		}
	}()
	serverErrors := make(chan error, 1)
	go func() { serverErrors <- server.Serve(listener) }()
	options := []oauth2.AuthCodeOption{oauth2.AccessTypeOffline, oauth2.S256ChallengeOption(verifier), oauth2.SetAuthURLParam("prompt", "consent")}
	if opts.Profile != "default" {
		options = append(options, oauth2.SetAuthURLParam("login_hint", opts.Profile))
	}
	url := cfg.AuthCodeURL(state, options...)
	fmt.Fprintf(out, "Authorize %s in your browser:\n%s\n", opts.Service, url)
	if !opts.NoBrowser {
		_ = openBrowser(ctx, url)
	}
	select {
	case code := <-result:
		if code == "" {
			return errors.New("OAuth authorization denied")
		}
		token, err := cfg.Exchange(ctx, code, oauth2.VerifierOption(verifier))
		if err != nil {
			return fmt.Errorf("exchange OAuth code: %w", err)
		}
		if token.RefreshToken == "" {
			return errors.New("OAuth response has no refresh token; revoke the app grant and log in again")
		}
		if err := saveClientConfig(opts, cfg); err != nil {
			return err
		}
		return saveToken(path, token)
	case err := <-serverErrors:
		return fmt.Errorf("OAuth callback server: %w", err)
	case <-ctx.Done():
		return fmt.Errorf("OAuth login timed out or canceled: %w", ctx.Err())
	}
}

func openBrowser(ctx context.Context, url string) error {
	var command string
	var args []string
	switch runtime.GOOS {
	case "darwin":
		command, args = "open", []string{url}
	case "windows":
		command, args = "rundll32", []string{"url.dll,FileProtocolHandler", url}
	default:
		command, args = "xdg-open", []string{url}
	}
	process := exec.CommandContext(ctx, command, args...)
	if err := process.Start(); err != nil {
		return err
	}
	// Desktop launchers may stay open; reap them without delaying the callback.
	go func() { _ = process.Wait() }()
	return nil
}

// TokenStatus reports saved credentials without exposing secrets or refreshing them.
func TokenStatus(profile, service string) (string, error) {
	if _, err := serviceScopes(service); err != nil {
		return "", err
	}
	path, err := tokenPath(profile, service)
	if err != nil {
		return "", err
	}
	token, err := loadToken(path)
	if errors.Is(err, os.ErrNotExist) {
		return "not authenticated", nil
	}
	if err != nil {
		return "", err
	}
	if token.Valid() {
		return "authenticated", nil
	}
	if token.RefreshToken != "" {
		return "expired access token; refresh available", nil
	}
	return "login required", nil
}

// Logout removes only this profile/service's local token; it does not revoke grants.
func Logout(profile, service string) error {
	if _, err := serviceScopes(service); err != nil {
		return err
	}
	path, err := tokenPath(profile, service)
	if err != nil {
		return err
	}
	if err := os.Remove(path); err != nil && !errors.Is(err, os.ErrNotExist) {
		return fmt.Errorf("remove OAuth token: %w", err)
	}
	return nil
}
