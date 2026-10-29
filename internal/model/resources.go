// Package model contains API-independent GoogleCL resources.
package model

// Document is a Drive file; MIMEType distinguishes native Google documents.
type Document struct {
	ID       string `json:"id"`
	Title    string `json:"title"`
	URL      string `json:"url"`
	MIMEType string `json:"mime_type"`
}

// Calendar identifies a calendar by its immutable API ID.
type Calendar struct {
	ID      string `json:"id"`
	Title   string `json:"title"`
	Primary bool   `json:"primary"`
}

// Event preserves RFC3339 timestamps or YYYY-MM-DD all-day dates.
type Event struct {
	ID       string `json:"id"`
	Title    string `json:"title"`
	URL      string `json:"url"`
	Start    string `json:"start"`
	End      string `json:"end"`
	Location string `json:"where"`
}

// Contact contains the supported legacy contact output fields.
type Contact struct {
	ID     string   `json:"id"`
	Name   string   `json:"name"`
	Emails []string `json:"emails"`
	Phones []string `json:"phones"`
}
