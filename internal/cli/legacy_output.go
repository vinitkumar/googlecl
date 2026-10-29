package cli

import (
	"encoding/json"
	"fmt"
	"io"
	"strings"
	"time"

	"github.com/vinitkumar/googlecl/internal/model"
)

type legacyOutput struct {
	fields     []string
	delimiter  string
	missing    string
	dateLayout string
	json       bool
}

func (o legacyOutput) writeRows(out io.Writer, rows []map[string]string, resources any) error {
	if o.json {
		encoder := json.NewEncoder(out)
		encoder.SetEscapeHTML(false)
		return encoder.Encode(resources)
	}
	for _, row := range rows {
		values := make([]string, len(o.fields))
		for i, field := range o.fields {
			value := row[field]
			if value == "" {
				value = o.missing
			}
			// Historical output replaces embedded delimiters rather than CSV-quoting them.
			values[i] = strings.ReplaceAll(value, o.delimiter, " ")
		}
		if _, err := fmt.Fprintln(out, strings.Join(values, o.delimiter)); err != nil {
			return err
		}
	}
	return nil
}

func (o legacyOutput) documents(out io.Writer, files []model.Document) error {
	rows := make([]map[string]string, 0, len(files))
	for _, file := range files {
		rows = append(rows, map[string]string{"id": file.ID, "title": file.Title, "name": file.Title, "url": file.URL, "url-site": file.URL, "type": file.MIMEType})
	}
	return o.writeRows(out, rows, files)
}

func (o legacyOutput) events(out io.Writer, events []model.Event) error {
	rows := make([]map[string]string, 0, len(events))
	for _, event := range events {
		rows = append(rows, map[string]string{"id": event.ID, "title": event.Title, "url": event.URL, "url-site": event.URL, "when": o.formatDate(event.Start) + " - " + o.formatDate(event.End), "where": event.Location, "start": event.Start, "end": event.End})
	}
	return o.writeRows(out, rows, events)
}

func (o legacyOutput) formatDate(value string) string {
	for _, layout := range []string{time.RFC3339, "2006-01-02"} {
		if parsed, err := time.ParseInLocation(layout, value, time.Local); err == nil {
			return parsed.In(time.Local).Format(o.dateLayout)
		}
	}
	return value
}

func (o legacyOutput) contacts(out io.Writer, contacts []model.Contact) error {
	rows := make([]map[string]string, 0, len(contacts))
	separator := ","
	if strings.TrimSpace(o.delimiter) == "," {
		separator = ";"
	}
	for _, contact := range contacts {
		rows = append(rows, map[string]string{"id": contact.ID, "name": contact.Name, "title": contact.Name, "email": strings.Join(contact.Emails, separator), "phone": strings.Join(contact.Phones, separator)})
	}
	return o.writeRows(out, rows, contacts)
}

func dateLayout(format string) (string, error) {
	replacements := map[byte]string{'Y': "2006", 'y': "06", 'm': "01", 'b': "Jan", 'B': "January", 'd': "02", 'e': "_2", 'H': "15", 'I': "03", 'M': "04", 'S': "05", 'p': "PM", 'a': "Mon", 'A': "Monday", 'z': "-0700", 'Z': "MST", '%': "%"}
	var result strings.Builder
	for i := 0; i < len(format); i++ {
		if format[i] != '%' {
			result.WriteByte(format[i])
			continue
		}
		i++
		if i == len(format) {
			return "", fmt.Errorf("incomplete date_print_format directive")
		}
		value, ok := replacements[format[i]]
		if !ok {
			return "", fmt.Errorf("unsupported date_print_format directive %%%c", format[i])
		}
		result.WriteString(value)
	}
	return result.String(), nil
}
