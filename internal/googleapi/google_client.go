// Package googleapi adapts generated Google clients to GoogleCL domain resources.
package googleapi

import (
	"context"
	"fmt"
	"net/http"

	"google.golang.org/api/calendar/v3"
	"google.golang.org/api/drive/v3"
	"google.golang.org/api/option"
	"google.golang.org/api/people/v1"
)

const maxPages = 1000

// Client initializes only the requested service; no credentials are shared across services.
type Client struct {
	drive    *drive.Service
	calendar *calendar.Service
	people   *people.Service
}

// NewClient uses an authorized HTTP transport; endpoint overrides are test-only options.
func NewClient(ctx context.Context, service string, httpClient *http.Client, opts ...option.ClientOption) (*Client, error) {
	// Copy rather than mutating the caller's shared HTTP client.
	clientCopy := *httpClient
	transport := clientCopy.Transport
	if transport == nil {
		transport = http.DefaultTransport
	}
	clientCopy.Transport = &retryTransport{base: transport, delay: waitRetry}
	opts = append([]option.ClientOption{option.WithHTTPClient(&clientCopy)}, opts...)
	client := &Client{}
	var err error
	switch service {
	case "docs":
		client.drive, err = drive.NewService(ctx, opts...)
	case "calendar":
		client.calendar, err = calendar.NewService(ctx, opts...)
	case "contacts":
		client.people, err = people.NewService(ctx, opts...)
	default:
		return nil, fmt.Errorf("Google API service %q is unsupported", service)
	}
	if err != nil {
		return nil, fmt.Errorf("initialize %s API: %w", service, err)
	}
	return client, nil
}
