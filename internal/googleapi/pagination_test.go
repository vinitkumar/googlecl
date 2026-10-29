package googleapi

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"google.golang.org/api/option"
)

func TestPagination(t *testing.T) {
	for _, service := range []string{"docs", "calendar", "events", "contacts"} {
		for _, scenario := range []string{"pages", "error", "limit"} {
			t.Run(service+"/"+scenario, func(t *testing.T) {
				calls := 0
				server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
					calls++
					if calls > 1 && r.URL.Query().Get("pageToken") != "next" {
						t.Error("page token not forwarded")
					}
					if scenario == "error" && calls == 2 {
						http.Error(w, "denied", http.StatusForbidden)
						return
					}
					next := `,"nextPageToken":"next"`
					if scenario == "pages" && calls == 2 {
						next = ""
					}
					body := `"files":[{"id":"file"}]`
					switch service {
					case "calendar":
						body = `"items":[{"id":"calendar"}]`
					case "events":
						body = `"items":[{"id":"event"}]`
					case "contacts":
						body = `"connections":[{"resourceName":"people/1"}]`
					}
					fmt.Fprintf(w, "{%s%s}", body, next)
				}))
				defer server.Close()
				apiService := service
				if service == "events" {
					apiService = "calendar"
				}
				client, err := NewClient(context.Background(), apiService, server.Client(), option.WithEndpoint(server.URL+"/"))
				if err != nil {
					t.Fatal(err)
				}
				count := 0
				switch service {
				case "docs":
					rows, e := client.ListDocuments(context.Background(), "")
					count, err = len(rows), e
				case "calendar":
					rows, e := client.ListCalendars(context.Background())
					count, err = len(rows), e
				case "events":
					rows, e := client.ListEvents(context.Background(), "cal", "", "", "")
					count, err = len(rows), e
				case "contacts":
					rows, e := client.ListContacts(context.Background())
					count, err = len(rows), e
				}
				if scenario == "pages" {
					if err != nil || count != 2 || calls != 2 {
						t.Fatalf("rows=%d calls=%d err=%v", count, calls, err)
					}
					return
				}
				if err == nil || count != 0 {
					t.Fatalf("partial success: rows=%d err=%v", count, err)
				}
				if scenario == "limit" && (calls != maxPages || !strings.Contains(err.Error(), "pagination exceeded")) {
					t.Fatalf("calls=%d err=%v", calls, err)
				}
			})
		}
	}
}
