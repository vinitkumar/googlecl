package cli

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/vinitkumar/googlecl/internal/app"
	"github.com/vinitkumar/googlecl/internal/auth"
	"github.com/vinitkumar/googlecl/internal/googleapi"
	"google.golang.org/api/option"
)

func runCommand(t *testing.T, handler http.HandlerFunc, args ...string) (string, string, error) {
	t.Helper()
	dir := t.TempDir()
	t.Setenv("GOOGLECL_CONFIG_DIR", dir)
	t.Setenv("XDG_CONFIG_HOME", dir)
	server := httptest.NewServer(handler)
	defer server.Close()
	var stdout, stderr bytes.Buffer
	factory := func(ctx context.Context, opts auth.LoginOptions) (*app.Workspace, error) {
		client, err := googleapi.NewClient(ctx, opts.Service, server.Client(), option.WithEndpoint(server.URL+"/"))
		if err != nil {
			return nil, err
		}
		return app.NewWorkspace(client), nil
	}
	cmd := NewCommand("test", Dependencies{Input: strings.NewReader(""), Output: &stdout, Errors: &stderr, Workspace: factory})
	cmd.SetArgs(args)
	err := cmd.ExecuteContext(context.Background())
	return stdout.String(), stderr.String(), err
}

func noAPI(t *testing.T) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		t.Errorf("unexpected API call: %s %s", r.Method, r.URL)
		http.Error(w, "unexpected request", 500)
	}
}

func TestHelpWithoutAuthentication(t *testing.T) {
	for _, args := range [][]string{{}, {"--help"}, {"--version"}, {"docs", "help"}, {"calendar", "help"}, {"help", "docs"}, {"contacts", "--help"}} {
		t.Run(strings.Join(args, " "), func(t *testing.T) {
			out, _, err := runCommand(t, noAPI(t), args...)
			if err != nil {
				t.Fatal(err)
			}
			if out == "" {
				t.Fatal("empty help")
			}
		})
	}
}

func TestLegacyDocumentList(t *testing.T) {
	for _, tc := range []struct {
		args []string
		want string
	}{
		{[]string{"docs", "list"}, "Report Q1,https://docs/one\nRésumé,N/A\n"},
		{[]string{"docs", "list", "^Report", "--fields=title,id", "--delimiter=|"}, "Report,Q1|one\n"},
		{[]string{"--fields=id", "docs", "list", "--title=Résumé"}, "two\n"},
		{[]string{"docs", "list", "--literal", "--title=Report,Q1", "--fields=id"}, "one\n"},
	} {
		t.Run(strings.Join(tc.args, " "), func(t *testing.T) {
			calls := 0
			out, _, err := runCommand(t, func(w http.ResponseWriter, r *http.Request) {
				calls++
				w.Header().Set("Content-Type", "application/json")
				if r.URL.Path != "/files" {
					t.Errorf("path = %s", r.URL.Path)
				}
				if r.URL.Query().Get("pageToken") == "" {
					fmt.Fprint(w, `{"files":[{"id":"one","name":"Report,Q1","webViewLink":"https://docs/one"}],"nextPageToken":"next"}`)
					return
				}
				fmt.Fprint(w, `{"files":[{"id":"two","name":"Résumé"}]}`)
			}, tc.args...)
			if err != nil {
				t.Fatal(err)
			}
			if out != tc.want {
				t.Fatalf("got %q; want %q", out, tc.want)
			}
			if calls != 2 {
				t.Fatalf("pagination calls=%d", calls)
			}
		})
	}
}

func TestLegacyDocumentGet(t *testing.T) {
	for _, style := range []string{"positional", "flags", "id"} {
		t.Run(style, func(t *testing.T) {
			dest := filepath.Join(t.TempDir(), "result.pdf")
			args := []string{"docs", "get", "My Doc", dest, "--format=pdf"}
			if style == "flags" {
				args = []string{"docs", "get", "--title=My Doc", "--dest=" + dest, "--format=pdf"}
			}
			if style == "id" {
				args = []string{"docs", "get", "--id=one", dest, "--format=pdf"}
			}
			_, _, err := runCommand(t, func(w http.ResponseWriter, r *http.Request) {
				switch r.URL.Path {
				case "/files":
					fmt.Fprint(w, `{"files":[{"id":"one","name":"My Doc","mimeType":"application/vnd.google-apps.document"}]}`)
				case "/files/one":
					fmt.Fprint(w, `{"id":"one","name":"My Doc","mimeType":"application/vnd.google-apps.document"}`)
				case "/files/one/export":
					if r.URL.Query().Get("mimeType") != "application/pdf" {
						t.Error("wrong export MIME")
					}
					fmt.Fprint(w, "PDF bytes")
				default:
					t.Errorf("unexpected %s", r.URL)
					http.NotFound(w, r)
				}
			}, args...)
			if err != nil {
				t.Fatal(err)
			}
			content, err := os.ReadFile(dest)
			if err != nil {
				t.Fatal(err)
			}
			if string(content) != "PDF bytes" {
				t.Fatalf("got %q", content)
			}
		})
	}
}

func TestLegacyCalendarList(t *testing.T) {
	out, _, err := runCommand(t, func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/users/me/calendarList":
			fmt.Fprint(w, `{"items":[{"id":"work@example.com","summary":"Work","primary":true}]}`)
		case "/calendars/work@example.com/events":
			if r.URL.Query().Get("timeMin") == "" || r.URL.Query().Get("singleEvents") != "true" {
				t.Error("missing date/recurrence filter")
			}
			fmt.Fprint(w, `{"items":[{"id":"event","summary":"Lunch","start":{"date":"2026-01-01"},"end":{"date":"2026-01-02"}}]}`)
		default:
			t.Errorf("unexpected %s", r.URL)
			http.NotFound(w, r)
		}
	}, "calendar", "list", "--date=2026-01-01", "--fields=title,id")
	if err != nil {
		t.Fatal(err)
	}
	if out != "\n[Work]\nLunch,event\n" {
		t.Fatalf("got %q", out)
	}
}

func TestLegacyContactList(t *testing.T) {
	out, _, err := runCommand(t, func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/v1/people/me/connections" {
			t.Errorf("path = %s", r.URL.Path)
		}
		fmt.Fprint(w, `{"connections":[{"resourceName":"people/1","names":[{"displayName":"john"}],"emailAddresses":[{"value":"a@example.com"},{"value":"b@example.com"}]},{"names":[{"displayName":"jane"}]}]}`)
	}, "contacts", "list", "john")
	if err != nil {
		t.Fatal(err)
	}
	if out != "john,a@example.com;b@example.com\n" {
		t.Fatalf("got %q", out)
	}
}

func TestJSONOutputHasNoHeaders(t *testing.T) {
	out, _, err := runCommand(t, func(w http.ResponseWriter, r *http.Request) { fmt.Fprint(w, `{"files":[]}`) }, "docs", "list", "--json")
	if err != nil {
		t.Fatal(err)
	}
	var rows []any
	if err := json.Unmarshal([]byte(out), &rows); err != nil {
		t.Fatal(err)
	}
	if rows == nil {
		t.Fatal("empty output must be [] rather than null")
	}
}

func TestDeleteRequiresConfirmation(t *testing.T) {
	writes := 0
	_, _, err := runCommand(t, func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			writes++
			t.Error("write without confirmation")
		}
		fmt.Fprint(w, `{"files":[{"id":"one","name":"Doc"}]}`)
	}, "docs", "delete", "Doc")
	if err == nil || !strings.Contains(err.Error(), "--yes") {
		t.Fatalf("expected confirmation refusal, got %v", err)
	}
	if writes != 0 {
		t.Fatal("unsafe delete")
	}
}

func TestDeleteTrashesInsteadOfDestroy(t *testing.T) {
	writes := 0
	_, _, err := runCommand(t, func(w http.ResponseWriter, r *http.Request) {
		if r.Method == http.MethodGet {
			fmt.Fprint(w, `{"files":[{"id":"one","name":"Doc"}]}`)
			return
		}
		writes++
		if r.Method != http.MethodPatch || r.URL.Path != "/files/one" {
			t.Errorf("unexpected mutation %s %s", r.Method, r.URL)
		}
		var body struct {
			Trashed bool `json:"trashed"`
		}
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			t.Error(err)
		}
		if !body.Trashed {
			t.Error("file not trashed")
		}
		fmt.Fprint(w, `{}`)
	}, "docs", "delete", "Doc", "--yes")
	if err != nil {
		t.Fatal(err)
	}
	if writes != 1 {
		t.Fatalf("writes=%d", writes)
	}
}

func TestUnsupportedFlagsRejected(t *testing.T) {
	for _, args := range [][]string{
		{"docs", "delete", "Report", "--query=important", "--yes"},
		{"docs", "upload", "file.txt", "--id=existing"},
		{"calendar", "today", "--date=2030-01-01"},
		{"contacts", "list", "--folder=work"},
		{"docs", "get", "Report", ".", "--json"},
	} {
		t.Run(strings.Join(args, " "), func(t *testing.T) {
			_, _, err := runCommand(t, noAPI(t), args...)
			if err == nil {
				t.Fatal("unsupported flag silently ignored")
			}
		})
	}
}

func TestLegacyConfigDefaults(t *testing.T) {
	path := filepath.Join(t.TempDir(), "config")
	if err := os.WriteFile(path, []byte("[GENERAL]\nfields = id\ndelimiter = |\n[DOCS]\nfields = title,id\nregex = false\n"), 0600); err != nil {
		t.Fatal(err)
	}
	for _, tc := range []struct {
		extra []string
		want  string
	}{
		{nil, "Report|one\n"},
		{[]string{"--fields=id", "--delimiter=,"}, "one\n"},
	} {
		args := append([]string{"docs", "list", "Report", "--config=" + path}, tc.extra...)
		out, _, err := runCommand(t, func(w http.ResponseWriter, r *http.Request) {
			fmt.Fprint(w, `{"files":[{"id":"one","name":"Report"},{"id":"two","name":"Report 2"}]}`)
		}, args...)
		if err != nil {
			t.Fatal(err)
		}
		if out != tc.want {
			t.Fatalf("got %q; want %q", out, tc.want)
		}
	}
}

func TestInvalidCommandsFailOffline(t *testing.T) {
	for _, args := range [][]string{
		{"picasa", "post", "album", "image.jpg"}, {"finance", "list"}, {"blogger", "post"}, {"docs", "edit", "Doc"}, {"contacts", "delete", "john"},
		{"docs", "get"}, {"docs", "upload"}, {"docs", "list", "--fields=banana"}, {"calendar", "list", "--date=nonsense"}, {"calendar", "add", "Meeting", "--reminder=-1"},
	} {
		t.Run(strings.Join(args, " "), func(t *testing.T) {
			_, _, err := runCommand(t, noAPI(t), args...)
			if err == nil {
				t.Fatal("expected error")
			}
		})
	}
}
