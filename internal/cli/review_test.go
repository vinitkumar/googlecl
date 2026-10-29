package cli

import (
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestAuthServiceProfile(t *testing.T) {
	path := filepath.Join(t.TempDir(), "config")
	if err := os.WriteFile(path, []byte("[GENERAL]\nuser = general\n[docs]\nuser = alice\n"), 0600); err != nil {
		t.Fatal(err)
	}
	out, _, err := runCommand(t, noAPI(t), "auth", "status", "--service=docs", "--config="+path)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.HasPrefix(out, "alice (docs):") {
		t.Fatalf("wrong profile: %s", out)
	}
}

func TestIgnoredFlagsFailOffline(t *testing.T) {
	for _, args := range [][]string{
		{"docs", "upload", "missing.txt", "--fields=title"},
		{"docs", "upload", "missing.txt", "--json", "--fields=banana"},
		{"docs", "list", "--json", "--delimiter=|"},
		{"contacts", "list", "--yes"},
		{"auth", "status", "--credentials=unused.json"},
	} {
		t.Run(strings.Join(args, " "), func(t *testing.T) {
			_, _, err := runCommand(t, noAPI(t), args...)
			if err == nil || !strings.Contains(err.Error(), "does not support") {
				t.Fatalf("expected unsupported flags, got %v", err)
			}
		})
	}
}

func TestGetWithFolderAndTitle(t *testing.T) {
	dest := t.TempDir()
	_, _, err := runCommand(t, func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Query().Get("alt") == "media" {
			fmt.Fprint(w, "content")
			return
		}
		if !strings.Contains(r.URL.Query().Get("q"), "'folder' in parents") {
			t.Error("missing folder filter")
		}
		fmt.Fprint(w, `{"files":[{"id":"one","name":"Report.txt"},{"id":"two","name":"Other.txt"}]}`)
	}, "docs", "get", "Report", dest, "--folder=id:folder")
	if err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(filepath.Join(dest, "Report.txt")); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(filepath.Join(dest, "Other.txt")); !os.IsNotExist(err) {
		t.Fatal("downloaded unmatched file")
	}
}

func TestJSONIgnoresTextConfig(t *testing.T) {
	path := filepath.Join(t.TempDir(), "config")
	if err := os.WriteFile(path, []byte("[docs]\nfields = obsolete\ndate_print_format = %Q\n"), 0600); err != nil {
		t.Fatal(err)
	}
	out, _, err := runCommand(t, func(w http.ResponseWriter, r *http.Request) { fmt.Fprint(w, `{"files":[]}`) }, "docs", "list", "--json", "--config="+path)
	if err != nil {
		t.Fatal(err)
	}
	if out != "[]\n" {
		t.Fatalf("output=%q", out)
	}
}

func TestDocsIgnoreCalendarFormat(t *testing.T) {
	path := filepath.Join(t.TempDir(), "config")
	if err := os.WriteFile(path, []byte("[GENERAL]\ndate_print_format = %Q\n"), 0600); err != nil {
		t.Fatal(err)
	}
	_, _, err := runCommand(t, func(w http.ResponseWriter, r *http.Request) { fmt.Fprint(w, `{"files":[]}`) }, "docs", "list", "--config="+path)
	if err != nil {
		t.Fatal(err)
	}
}
