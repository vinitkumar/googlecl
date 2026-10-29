package googleapi

import (
	"context"
	"fmt"

	"github.com/vinitkumar/googlecl/internal/model"
	"google.golang.org/api/calendar/v3"
)

func eventFromAPI(event *calendar.Event) model.Event {
	result := model.Event{ID: event.Id, Title: event.Summary, URL: event.HtmlLink, Location: event.Location}
	if event.Start != nil {
		result.Start = event.Start.DateTime
		if result.Start == "" {
			result.Start = event.Start.Date
		}
	}
	if event.End != nil {
		result.End = event.End.DateTime
		if result.End == "" {
			result.End = event.End.Date
		}
	}
	return result
}

// ListCalendars returns accessible calendars across every page.
func (c *Client) ListCalendars(ctx context.Context) ([]model.Calendar, error) {
	result := []model.Calendar{}
	token := ""
	for page := 0; page < maxPages; page++ {
		response, err := c.calendar.CalendarList.List().PageToken(token).Context(ctx).Do()
		if err != nil {
			return nil, fmt.Errorf("list calendars: %w", err)
		}
		for _, entry := range response.Items {
			result = append(result, model.Calendar{ID: entry.Id, Title: entry.Summary, Primary: entry.Primary})
		}
		if response.NextPageToken == "" {
			return result, nil
		}
		token = response.NextPageToken
	}
	return nil, fmt.Errorf("Calendar pagination exceeded %d pages", maxPages)
}

// ListEvents expands recurring instances and returns events ordered by start time.
func (c *Client) ListEvents(ctx context.Context, calendarID, start, end, query string) ([]model.Event, error) {
	result := []model.Event{}
	token := ""
	for page := 0; page < maxPages; page++ {
		call := c.calendar.Events.List(calendarID).SingleEvents(true).OrderBy("startTime").MaxResults(2500).PageToken(token).Context(ctx)
		if start != "" {
			call.TimeMin(start)
		}
		if end != "" {
			call.TimeMax(end)
		}
		if query != "" {
			call.Q(query)
		}
		response, err := call.Do()
		if err != nil {
			return nil, fmt.Errorf("list calendar events: %w", err)
		}
		for _, event := range response.Items {
			result = append(result, eventFromAPI(event))
		}
		if response.NextPageToken == "" {
			return result, nil
		}
		token = response.NextPageToken
	}
	return nil, fmt.Errorf("Calendar event pagination exceeded %d pages; narrow --date", maxPages)
}

// AddEvent uses Calendar's natural-language parser when no explicit dates are supplied.
func (c *Client) AddEvent(ctx context.Context, calendarID, title, start, end string, reminder *int64) (model.Event, error) {
	var event *calendar.Event
	var err error
	if start == "" {
		event, err = c.calendar.Events.QuickAdd(calendarID, title).Context(ctx).Do()
		if err != nil {
			return model.Event{}, fmt.Errorf("quick-add calendar event: %w", err)
		}
		if reminder != nil {
			event, err = c.calendar.Events.Patch(calendarID, event.Id, &calendar.Event{Reminders: eventReminder(*reminder)}).Context(ctx).Do()
			if err != nil {
				return model.Event{}, fmt.Errorf("event was created but reminder update failed; do not retry add: %w", err)
			}
		}
	} else {
		value := &calendar.Event{Summary: title, Start: eventDate(start), End: eventDate(end)}
		if reminder != nil {
			value.Reminders = eventReminder(*reminder)
		}
		event, err = c.calendar.Events.Insert(calendarID, value).Context(ctx).Do()
		if err != nil {
			return model.Event{}, fmt.Errorf("create calendar event: %w", err)
		}
	}
	return eventFromAPI(event), nil
}

func eventDate(value string) *calendar.EventDateTime {
	if len(value) == len("2006-01-02") {
		return &calendar.EventDateTime{Date: value}
	}
	return &calendar.EventDateTime{DateTime: value}
}

func eventReminder(minutes int64) *calendar.EventReminders {
	return &calendar.EventReminders{UseDefault: false, ForceSendFields: []string{"UseDefault"}, Overrides: []*calendar.EventReminder{{Method: "popup", Minutes: minutes, ForceSendFields: []string{"Minutes"}}}}
}

// DeleteEvent deletes only the selected event or expanded recurrence instance.
func (c *Client) DeleteEvent(ctx context.Context, calendarID, id string) error {
	if err := c.calendar.Events.Delete(calendarID, id).Context(ctx).Do(); err != nil {
		return fmt.Errorf("delete calendar event: %w", err)
	}
	return nil
}
