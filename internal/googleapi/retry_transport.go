package googleapi

import (
	"context"
	"net/http"
	"strconv"
	"time"
)

const (
	maxReadAttempts = 3
	maxRetryDelay   = 30 * time.Second
)

type retryTransport struct {
	base  http.RoundTripper
	delay func(context.Context, time.Duration) error
}

func (t *retryTransport) RoundTrip(request *http.Request) (*http.Response, error) {
	for attempt := 0; ; attempt++ {
		response, err := t.base.RoundTrip(request)
		// Never replay mutations: an uncertain response may hide a successful write.
		if request.Method != http.MethodGet || err != nil || attempt == maxReadAttempts-1 {
			return response, err
		}
		if response.StatusCode != 429 && response.StatusCode != 500 && response.StatusCode != 502 && response.StatusCode != 503 && response.StatusCode != 504 {
			return response, nil
		}
		delay := retryDelay(response.Header.Get("Retry-After"), attempt)
		response.Body.Close()
		if err := t.delay(request.Context(), delay); err != nil {
			return nil, err
		}
	}
}

func retryDelay(header string, attempt int) time.Duration {
	delay := time.Second << attempt
	if seconds, err := strconv.ParseInt(header, 10, 64); err == nil && seconds >= 0 {
		if seconds >= int64(maxRetryDelay/time.Second) {
			return maxRetryDelay
		}
		delay = time.Duration(seconds) * time.Second
	} else if date, err := http.ParseTime(header); err == nil {
		delay = time.Until(date)
	}
	if delay > maxRetryDelay {
		return maxRetryDelay
	}
	if delay < 0 {
		return 0
	}
	return delay
}

func waitRetry(ctx context.Context, delay time.Duration) error {
	timer := time.NewTimer(delay)
	defer timer.Stop()
	select {
	case <-ctx.Done():
		return ctx.Err()
	case <-timer.C:
		return nil
	}
}
