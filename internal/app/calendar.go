package app

import (
	"context"
	"fmt"

	"github.com/vinitkumar/googlecl/internal/model"
)

// Calendars lists calendars available to the current Google account.
func (w *Workspace) Calendars(ctx context.Context) ([]model.Calendar, error) {
	return w.backend.ListCalendars(ctx)
}

// ResolveCalendar accepts a legacy title or an exact calendar ID, rejecting ambiguity.
func (w *Workspace) ResolveCalendar(ctx context.Context, selector string) (model.Calendar, error) {
	calendars, err := w.backend.ListCalendars(ctx)
	if err != nil {
		return model.Calendar{}, err
	}
	matches := []model.Calendar{}
	for _, cal := range calendars {
		if ((selector == "" || selector == "primary") && cal.Primary) || cal.ID == selector {
			return cal, nil
		}
		if cal.Title == selector {
			matches = append(matches, cal)
		}
	}
	if len(matches) != 1 {
		return model.Calendar{}, fmt.Errorf("calendar %q matched %d calendars; use --cal CALENDAR_ID", selector, len(matches))
	}
	return matches[0], nil
}

// Events filters title patterns without altering Google's full-text query semantics.
func (w *Workspace) Events(ctx context.Context, calendarID, start, end, query, title string, mode MatchMode) ([]model.Event, error) {
	match, err := titleMatcher(title, mode)
	if err != nil {
		return nil, err
	}
	events, err := w.backend.ListEvents(ctx, calendarID, start, end, query)
	if err != nil {
		return nil, err
	}
	result := []model.Event{}
	for _, event := range events {
		if match(event.Title) {
			result = append(result, event)
		}
	}
	return result, nil
}

// AddEvent creates one event; retries of non-idempotent writes are intentionally disabled.
func (w *Workspace) AddEvent(ctx context.Context, calendarID, title, start, end string, reminder *int64) (model.Event, error) {
	if title == "" {
		return model.Event{}, fmt.Errorf("event text is required")
	}
	return w.backend.AddEvent(ctx, calendarID, title, start, end, reminder)
}

// DeleteEvent removes exactly one resolved event instance.
func (w *Workspace) DeleteEvent(ctx context.Context, calendarID, id string) error {
	return w.backend.DeleteEvent(ctx, calendarID, id)
}

// Contacts filters saved contacts by their legacy name pattern.
func (w *Workspace) Contacts(ctx context.Context, title string, mode MatchMode) ([]model.Contact, error) {
	match, err := titleMatcher(title, mode)
	if err != nil {
		return nil, err
	}
	contacts, err := w.backend.ListContacts(ctx)
	if err != nil {
		return nil, err
	}
	result := []model.Contact{}
	for _, contact := range contacts {
		if match(contact.Name) {
			result = append(result, contact)
		}
	}
	return result, nil
}
