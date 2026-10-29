package cli

import (
	"encoding/json"
	"fmt"
	"strings"

	"github.com/spf13/cobra"
	"github.com/vinitkumar/googlecl/internal/app"
	"github.com/vinitkumar/googlecl/internal/model"
)

func newCalendarCommand(opts *commandOptions) *cobra.Command {
	root := &cobra.Command{Use: "calendar", Short: "List and manage calendar events"}
	for _, task := range []string{"list", "today"} {
		root.AddCommand(&cobra.Command{Use: task + " [TITLE]", Short: "List events with historical title,when output", Args: cobra.MaximumNArgs(1), RunE: opts.listEvents})
	}
	root.AddCommand(&cobra.Command{Use: "add [EVENT...]", Short: "Create events from text or explicit --date boundaries", RunE: opts.addEvents})
	root.AddCommand(&cobra.Command{Use: "delete [TITLE]", Short: "Delete matching event instances after confirmation", Args: cobra.MaximumNArgs(1), RunE: opts.deleteEvents})
	root.AddCommand(&cobra.Command{Use: "calendars", Short: "List calendar IDs and titles", Args: cobra.NoArgs, RunE: func(cmd *cobra.Command, args []string) error {
		workspace, err := opts.workspace(cmd, "calendar")
		if err != nil {
			return err
		}
		calendars, err := workspace.Calendars(cmd.Context())
		if err != nil {
			return err
		}
		if opts.json {
			return json.NewEncoder(opts.deps.Output).Encode(calendars)
		}
		for _, cal := range calendars {
			if _, err := fmt.Fprintf(opts.deps.Output, "%s%s%s\n", cal.Title, opts.delimiter, cal.ID); err != nil {
				return err
			}
		}
		return nil
	}})
	return root
}

func (o *commandOptions) eventTitle(args []string) (string, error) {
	if len(args) == 0 {
		return o.title, nil
	}
	if o.title != "" {
		return "", fmt.Errorf("unexpected positional title with --title")
	}
	return args[0], nil
}

func (o *commandOptions) listEvents(cmd *cobra.Command, args []string) error {
	title, err := o.eventTitle(args)
	if err != nil {
		return err
	}
	date := o.date
	if cmd.Name() == "today" {
		date = "today"
	}
	if date == "" && title == "" && o.query == "" {
		date = "today,"
	}
	start, end, err := app.CalendarRange(date, nowLocal())
	if err != nil {
		return err
	}
	output, err := o.output("calendar")
	if err != nil {
		return err
	}
	workspace, err := o.workspace(cmd, "calendar")
	if err != nil {
		return err
	}
	calendar, err := workspace.ResolveCalendar(cmd.Context(), o.calendar)
	if err != nil {
		return err
	}
	events, err := workspace.Events(cmd.Context(), calendar.ID, start, end, o.query, title, o.matchMode())
	if err != nil {
		return err
	}
	if !o.json {
		if _, err := fmt.Fprintf(o.deps.Output, "\n[%s]\n", calendar.Title); err != nil {
			return err
		}
	}
	return output.events(o.deps.Output, events)
}

func (o *commandOptions) addEvents(cmd *cobra.Command, args []string) error {
	texts := append([]string{}, args...)
	if o.source != "" {
		texts = append([]string{o.source}, texts...)
	}
	if len(texts) == 0 {
		text, err := o.required("", "src")
		if err != nil {
			return err
		}
		texts = []string{text}
	}
	for _, text := range texts {
		if strings.TrimSpace(text) == "" {
			return fmt.Errorf("event text cannot be empty")
		}
	}
	start, end, err := app.EventDates(o.date, nowLocal())
	if err != nil {
		return err
	}
	reminder, err := app.ReminderMinutes(o.reminder)
	if err != nil {
		return err
	}
	workspace, err := o.workspace(cmd, "calendar")
	if err != nil {
		return err
	}
	calendar, err := workspace.ResolveCalendar(cmd.Context(), o.calendar)
	if err != nil {
		return err
	}
	created := []model.Event{}
	for _, text := range texts {
		event, err := workspace.AddEvent(cmd.Context(), calendar.ID, text, start, end, reminder)
		if err != nil {
			return err
		}
		created = append(created, event)
		o.progress("Event created: %s", event.URL)
	}
	if o.json {
		return json.NewEncoder(o.deps.Output).Encode(created)
	}
	return nil
}

func (o *commandOptions) deleteEvents(cmd *cobra.Command, args []string) error {
	title, err := o.eventTitle(args)
	if err != nil {
		return err
	}
	if o.id != "" && (title != "" || o.query != "" || o.date != "") {
		return fmt.Errorf("--id cannot be combined with --title, --query, or --date")
	}
	if o.id == "" && title == "" && o.query == "" {
		title, err = o.required("", "title")
		if err != nil {
			return err
		}
	}
	start, end, err := app.CalendarRange(o.date, nowLocal())
	if err != nil {
		return err
	}
	workspace, err := o.workspace(cmd, "calendar")
	if err != nil {
		return err
	}
	calendar, err := workspace.ResolveCalendar(cmd.Context(), o.calendar)
	if err != nil {
		return err
	}
	events := []model.Event{{ID: o.id, Title: o.id}}
	if o.id == "" {
		events, err = workspace.Events(cmd.Context(), calendar.ID, start, end, o.query, title, o.matchMode())
		if err != nil {
			return err
		}
	}
	if len(events) == 0 {
		return fmt.Errorf("no calendar events matched")
	}
	names := make([]string, 0, len(events))
	for _, event := range events {
		names = append(names, fmt.Sprintf("%q (%s)", event.Title, event.ID))
	}
	if err := o.confirm("Delete events from " + calendar.Title + ": " + strings.Join(names, ", ")); err != nil {
		return err
	}
	for _, event := range events {
		if err := workspace.DeleteEvent(cmd.Context(), calendar.ID, event.ID); err != nil {
			return err
		}
		o.progress("Deleted event %s", event.ID)
	}
	return nil
}
