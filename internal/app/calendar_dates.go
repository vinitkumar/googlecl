package app

import (
	"fmt"
	"strconv"
	"strings"
	"time"
)

// CalendarRange interprets date-only end boundaries inclusively in the local timezone.
func CalendarRange(value string, now time.Time) (string, string, error) {
	if value == "" {
		return "", "", nil
	}
	parts := strings.Split(value, ",")
	if len(parts) > 2 {
		return "", "", fmt.Errorf("invalid date range %q", value)
	}
	start, _, err := parseCalendarDate(parts[0], now)
	if err != nil {
		return "", "", err
	}
	endText := parts[0]
	if len(parts) == 2 {
		endText = parts[1]
	}
	end, dateOnly, err := parseCalendarDate(endText, now)
	if err != nil {
		return "", "", err
	}
	// Calendar days may span 23 or 25 hours across daylight-saving transitions.
	if !end.IsZero() && dateOnly {
		end = end.AddDate(0, 0, 1)
	}
	if !start.IsZero() && !end.IsZero() && !end.After(start) {
		return "", "", fmt.Errorf("date range end must be after start")
	}
	format := func(value time.Time) string {
		if value.IsZero() {
			return ""
		}
		return value.Format(time.RFC3339)
	}
	return format(start), format(end), nil
}

func parseCalendarDate(value string, now time.Time) (time.Time, bool, error) {
	if value == "" {
		return time.Time{}, false, nil
	}
	day := time.Date(now.Year(), now.Month(), now.Day(), 0, 0, 0, 0, now.Location())
	switch value {
	case "today":
		return day, true, nil
	case "tomorrow":
		return day.AddDate(0, 0, 1), true, nil
	case "yesterday":
		return day.AddDate(0, 0, -1), true, nil
	}
	if parsed, err := time.ParseInLocation("2006-01-02", value, now.Location()); err == nil {
		return parsed, true, nil
	}
	if parsed, err := time.Parse(time.RFC3339, value); err == nil {
		return parsed, false, nil
	}
	return time.Time{}, false, fmt.Errorf("invalid date %q; use YYYY-MM-DD, RFC3339, today, tomorrow, or yesterday", value)
}

// ReminderMinutes accepts historical minute counts and s/m/h/d/w suffixes.
func ReminderMinutes(value string) (*int64, error) {
	if value == "" {
		return nil, nil
	}
	units := map[byte]int64{'s': 1, 'm': 60, 'h': 3600, 'd': 86400, 'w': 604800}
	multiplier := int64(60)
	if unit, ok := units[value[len(value)-1]]; ok {
		multiplier = unit
		value = value[:len(value)-1]
	}
	count, err := strconv.ParseInt(value, 10, 64)
	if err != nil || count < 0 || count > 40320*60/multiplier {
		return nil, fmt.Errorf("reminder must be between 0 and 40320 minutes")
	}
	minutes := count * multiplier / 60
	return &minutes, nil
}

// EventDates validates explicit event boundaries; dates have exclusive end dates.
func EventDates(value string, now time.Time) (string, string, error) {
	if value == "" {
		return "", "", nil
	}
	parts := strings.Split(value, ",")
	if len(parts) > 2 {
		return "", "", fmt.Errorf("event date requires a start and optional end")
	}
	start, dateOnly, err := parseCalendarDate(parts[0], now)
	if err != nil {
		return "", "", err
	}
	if start.IsZero() {
		return "", "", fmt.Errorf("event start date is required")
	}
	end := start.Add(time.Hour)
	if dateOnly {
		end = start.AddDate(0, 0, 1)
	}
	if len(parts) == 2 {
		var endDateOnly bool
		end, endDateOnly, err = parseCalendarDate(parts[1], now)
		if err != nil {
			return "", "", err
		}
		if dateOnly != endDateOnly {
			return "", "", fmt.Errorf("event dates cannot mix all-day and timed boundaries")
		}
	}
	if !end.After(start) {
		return "", "", fmt.Errorf("event end must be after start")
	}
	layout := time.RFC3339
	if dateOnly {
		layout = "2006-01-02"
	}
	return start.Format(layout), end.Format(layout), nil
}
