package cli

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestLegacyUploadConversion(t *testing.T) {
	for _, original := range []bool{false, true} {
		t.Run(fmt.Sprint(original), func(t *testing.T) {
			path := filepath.Join(t.TempDir(), "notes.txt")
			if err := os.WriteFile(path, []byte("hello upload"), 0600); err != nil {
				t.Fatal(err)
			}
			args := []string{"docs", "upload", path, "--json"}
			if original {
				args = append(args, "--no-convert")
			}
			mutations := 0
			out, _, err := runCommand(t, func(w http.ResponseWriter, r *http.Request) {
				mutations++
				if r.Method != http.MethodPost {
					t.Errorf("upload method=%s", r.Method)
				}
				body, err := io.ReadAll(r.Body)
				if err != nil {
					t.Error(err)
				}
				if !strings.Contains(string(body), "hello upload") {
					t.Error("missing upload bytes")
				}
				converted := strings.Contains(string(body), "application/vnd.google-apps.document")
				if converted == original {
					t.Errorf("conversion=%v original=%v", converted, original)
				}
				w.Header().Set("Content-Type", "application/json")
				fmt.Fprint(w, `{"id":"uploaded","name":"notes.txt","webViewLink":"https://docs/uploaded"}`)
			}, args...)
			if err != nil {
				t.Fatal(err)
			}
			if mutations != 1 {
				t.Fatalf("writes=%d", mutations)
			}
			if !strings.Contains(out, `"id":"uploaded"`) {
				t.Fatalf("output=%s", out)
			}
		})
	}
}

func TestLegacyCalendarAdd(t *testing.T) {
	for _, explicit := range []bool{false, true} {
		t.Run(fmt.Sprint(explicit), func(t *testing.T) {
			args := []string{"calendar", "add", "Lunch tomorrow at noon", "--json"}
			if explicit {
				args = append(args, "--date=2026-03-08", "--reminder=0")
			}
			writes := 0
			out, _, err := runCommand(t, func(w http.ResponseWriter, r *http.Request) {
				if r.Method == http.MethodGet {
					fmt.Fprint(w, `{"items":[{"id":"primary-id","summary":"Personal","primary":true}]}`)
					return
				}
				writes++
				if explicit {
					var event struct {
						Start struct {
							Date string `json:"date"`
						} `json:"start"`
						End struct {
							Date string `json:"date"`
						} `json:"end"`
						Reminders struct {
							UseDefault bool             `json:"useDefault"`
							Overrides  []map[string]any `json:"overrides"`
						} `json:"reminders"`
					}
					if err := json.NewDecoder(r.Body).Decode(&event); err != nil {
						t.Error(err)
					}
					if event.Start.Date != "2026-03-08" || event.End.Date != "2026-03-09" {
						t.Errorf("bad all-day bounds: %+v", event)
					}
					if event.Reminders.UseDefault || len(event.Reminders.Overrides) != 1 || event.Reminders.Overrides[0]["minutes"] != float64(0) {
						t.Error("zero-minute reminder omitted")
					}
				} else {
					if !strings.HasSuffix(r.URL.Path, "/quickAdd") || r.URL.Query().Get("text") != "Lunch tomorrow at noon" {
						t.Errorf("unexpected quick-add request %s", r.URL)
					}
				}
				fmt.Fprint(w, `{"id":"event-one","summary":"Lunch","htmlLink":"https://calendar/event-one","start":{"date":"2026-03-08"},"end":{"date":"2026-03-09"}}`)
			}, args...)
			if err != nil {
				t.Fatal(err)
			}
			if writes != 1 {
				t.Fatalf("writes=%d", writes)
			}
			if !strings.Contains(out, `"id":"event-one"`) {
				t.Fatalf("output=%s", out)
			}
		})
	}
}

func TestAPIErrorIsNotEmptySuccess(t *testing.T) {
	calls := 0
	out, _, err := runCommand(t, func(w http.ResponseWriter, r *http.Request) {
		calls++
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusForbidden)
		fmt.Fprint(w, `{"error":{"code":403,"message":"API not enabled"}}`)
	}, "docs", "list")
	if err == nil || !strings.Contains(err.Error(), "403") {
		t.Fatalf("expected permission error, got %v", err)
	}
	if out != "" || calls != 1 {
		t.Fatalf("output=%q calls=%d", out, calls)
	}
}

func TestMutationsAreNotRetried(t *testing.T) {
	path := filepath.Join(t.TempDir(), "file.txt")
	if err := os.WriteFile(path, []byte("hello"), 0600); err != nil {
		t.Fatal(err)
	}
	calls := 0
	_, _, err := runCommand(t, func(w http.ResponseWriter, r *http.Request) {
		calls++
		http.Error(w, "server failure", http.StatusServiceUnavailable)
	}, "docs", "upload", path)
	if err == nil {
		t.Fatal("expected upload failure")
	}
	if calls != 1 {
		t.Fatalf("write retried %d times", calls)
	}
}
