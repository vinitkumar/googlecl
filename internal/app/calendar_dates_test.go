package app

import (
	"testing"
	"time"
)

func TestCalendarDateRange(t *testing.T) {
	zone, err := time.LoadLocation("America/New_York")
	if err != nil {
		t.Fatal(err)
	}
	now := time.Date(2026, 3, 8, 12, 0, 0, 0, zone)
	for _, tc := range []struct{ input, start, end string }{
		{"today", "2026-03-08T00:00:00-05:00", "2026-03-09T00:00:00-04:00"},
		{"today,", "2026-03-08T00:00:00-05:00", ""},
		{"2026-03-08,2026-03-09", "2026-03-08T00:00:00-05:00", "2026-03-10T00:00:00-04:00"},
	} {
		t.Run(tc.input, func(t *testing.T) {
			start, end, err := CalendarRange(tc.input, now)
			if err != nil {
				t.Fatal(err)
			}
			if start != tc.start || end != tc.end {
				t.Fatalf("got %s %s", start, end)
			}
		})
	}
	for _, input := range []string{"nonsense", "2026-03-09,2026-03-08", "a,b,c"} {
		if _, _, err := CalendarRange(input, now); err == nil {
			t.Fatalf("accepted %q", input)
		}
	}
}

func TestReminderMinutes(t *testing.T) {
	for input, want := range map[string]int64{"0": 0, "10m": 10, "2h": 120, "1d": 1440, "1w": 10080} {
		got, err := ReminderMinutes(input)
		if err != nil {
			t.Fatal(err)
		}
		if *got != want {
			t.Fatalf("%s = %d", input, *got)
		}
	}
	for _, input := range []string{"-1", "fish", "5w"} {
		if _, err := ReminderMinutes(input); err == nil {
			t.Fatalf("accepted %q", input)
		}
	}
}
