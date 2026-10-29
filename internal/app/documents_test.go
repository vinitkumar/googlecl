package app

import (
	"context"
	"errors"
	"io"
	"os"
	"path/filepath"
	"testing"

	"github.com/vinitkumar/googlecl/internal/model"
)

type documentBackend struct {
	Backend
	files       []model.Document
	downloadErr error
}

func (b *documentBackend) ListDocuments(context.Context, string) ([]model.Document, error) {
	return b.files, nil
}
func (b *documentBackend) DownloadDocument(_ context.Context, _ model.Document, _ string, out io.Writer) error {
	_, err := io.WriteString(out, "new content")
	if err != nil {
		return err
	}
	return b.downloadErr
}

func TestDocumentTitleRegex(t *testing.T) {
	w := NewWorkspace(&documentBackend{files: []model.Document{{Title: "Résumé"}, {Title: "Report 2026"}, {Title: "Notes"}}})
	files, err := w.FindDocuments(context.Background(), DocumentQuery{Title: "^R", Match: MatchRegex})
	if err != nil {
		t.Fatal(err)
	}
	if len(files) != 2 {
		t.Fatalf("got %v", files)
	}
	if _, err := w.FindDocuments(context.Background(), DocumentQuery{Title: "[", Match: MatchRegex}); err == nil {
		t.Fatal("invalid regex accepted")
	}
}

func TestDownloadNeverClobbers(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "report.txt")
	if err := os.WriteFile(path, []byte("existing"), 0600); err != nil {
		t.Fatal(err)
	}
	w := NewWorkspace(&documentBackend{})
	err := w.DownloadFile(context.Background(), model.Document{Title: "report.txt"}, path, "txt")
	if err == nil {
		t.Fatal("expected overwrite refusal")
	}
	got, _ := os.ReadFile(path)
	if string(got) != "existing" {
		t.Fatal("file overwritten")
	}
}

func TestFailedDownloadRemoved(t *testing.T) {
	path := filepath.Join(t.TempDir(), "download.txt")
	w := NewWorkspace(&documentBackend{downloadErr: errors.New("connection reset")})
	if err := w.DownloadFile(context.Background(), model.Document{Title: "report"}, path, "txt"); err == nil {
		t.Fatal("expected failure")
	}
	if _, err := os.Stat(path); !os.IsNotExist(err) {
		t.Fatalf("partial file retained: %v", err)
	}
}

func TestUnsafeDownloadName(t *testing.T) {
	for _, title := range []string{"../escape", `..\escape`, ".", "..", ""} {
		w := NewWorkspace(&documentBackend{})
		if err := w.DownloadFile(context.Background(), model.Document{Title: title}, t.TempDir(), "txt"); err == nil {
			t.Fatalf("unsafe title accepted: %q", title)
		}
	}
}

func TestPortableDownloadNames(t *testing.T) {
	for _, title := range []string{"NUL", "con.txt", "COM1", "COM¹.txt", "LPT²", "CON .txt", "report:stream", "report.", "report ", "line\nbreak"} {
		t.Run(title, func(t *testing.T) {
			w := NewWorkspace(&documentBackend{})
			if err := w.DownloadFile(context.Background(), model.Document{Title: title}, t.TempDir(), "txt"); err == nil {
				t.Fatalf("unsafe filename accepted: %q", title)
			}
		})
	}
}

func TestExportSuffixCannotEscape(t *testing.T) {
	dir := t.TempDir()
	if err := os.Mkdir(filepath.Join(dir, "report.bad"), 0700); err != nil {
		t.Fatal(err)
	}
	w := NewWorkspace(&documentBackend{})
	err := w.DownloadFile(context.Background(), model.Document{Title: "report", MIMEType: "application/vnd.google-apps.document"}, dir, "bad/../../escape")
	if err == nil {
		t.Fatal("export suffix escaped destination")
	}
}

func TestEmptyFolderIDRejected(t *testing.T) {
	w := NewWorkspace(&documentBackend{})
	if _, err := w.FindDocuments(context.Background(), DocumentQuery{Folder: "id:"}); err == nil {
		t.Fatal("empty folder ID broadened selection")
	}
}
