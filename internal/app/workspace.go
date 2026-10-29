// Package app implements workflows independently of CLI parsing and Google SDK types.
package app

import (
	"context"
	"io"

	"github.com/vinitkumar/googlecl/internal/model"
)

// Backend is the boundary to Google APIs; implementations must respect cancellation.
type Backend interface {
	ListDocuments(context.Context, string) ([]model.Document, error)
	GetDocument(context.Context, string) (model.Document, error)
	UploadDocument(context.Context, string, string, string, string, io.Reader) (model.Document, error)
	DownloadDocument(context.Context, model.Document, string, io.Writer) error
	TrashDocument(context.Context, string) error
	ListCalendars(context.Context) ([]model.Calendar, error)
	ListEvents(context.Context, string, string, string, string) ([]model.Event, error)
	AddEvent(context.Context, string, string, string, string, *int64) (model.Event, error)
	DeleteEvent(context.Context, string, string) error
	ListContacts(context.Context) ([]model.Contact, error)
}

// Workspace coordinates domain operations without owning credential lifetimes.
type Workspace struct{ backend Backend }

// NewWorkspace binds workflows to a real or test Google API adapter.
func NewWorkspace(backend Backend) *Workspace { return &Workspace{backend: backend} }
