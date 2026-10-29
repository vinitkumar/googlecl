package googleapi

import (
	"context"
	"errors"
	"io"
	"net/http"
	"strings"
	"testing"
	"time"
)

type transportFunc func(*http.Request) (*http.Response, error)

func (f transportFunc) RoundTrip(r *http.Request) (*http.Response, error) { return f(r) }

func TestRetryOnlySafeReads(t *testing.T) {
	for _, method := range []string{http.MethodGet, http.MethodPost, http.MethodPatch, http.MethodDelete} {
		t.Run(method, func(t *testing.T) {
			calls := 0
			retry := &retryTransport{base: transportFunc(func(r *http.Request) (*http.Response, error) {
				calls++
				return &http.Response{StatusCode: 503, Header: http.Header{}, Body: io.NopCloser(strings.NewReader("unavailable"))}, nil
			}), delay: func(context.Context, time.Duration) error { return nil }}
			request, _ := http.NewRequest(method, "https://example.com", nil)
			response, err := retry.RoundTrip(request)
			if err != nil {
				t.Fatal(err)
			}
			response.Body.Close()
			expected := 1
			if method == http.MethodGet {
				expected = maxReadAttempts
			}
			if calls != expected {
				t.Fatalf("%s attempts=%d, want %d", method, calls, expected)
			}
		})
	}
}

func TestRetryHonorsCancellation(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	retry := &retryTransport{base: transportFunc(func(r *http.Request) (*http.Response, error) {
		return &http.Response{StatusCode: 429, Header: http.Header{}, Body: io.NopCloser(strings.NewReader("quota"))}, nil
	}), delay: waitRetry}
	request, _ := http.NewRequestWithContext(ctx, http.MethodGet, "https://example.com", nil)
	if _, err := retry.RoundTrip(request); !errors.Is(err, context.Canceled) {
		t.Fatalf("got %v", err)
	}
}

func TestRetryAfterBounded(t *testing.T) {
	if got := retryDelay("3600", 0); got != maxRetryDelay {
		t.Fatalf("unbounded Retry-After: %s", got)
	}
	if got := retryDelay("2", 0); got != 2*time.Second {
		t.Fatalf("Retry-After=%s", got)
	}
}
