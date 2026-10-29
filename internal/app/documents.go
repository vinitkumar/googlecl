package app

import (
	"context"
	"errors"
	"fmt"
	"mime"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"unicode"

	"github.com/vinitkumar/googlecl/internal/model"
)

// MatchMode preserves historical regular expressions while allowing literal matches.
type MatchMode int

const (
	MatchRegex MatchMode = iota
	MatchLiteral
)

// DocumentQuery selects by immutable ID or legacy title pattern and optional folder.
type DocumentQuery struct {
	ID, Title, Folder string
	Match             MatchMode
}

func titleMatcher(title string, mode MatchMode) (func(string) bool, error) {
	if title == "" {
		return func(string) bool { return true }, nil
	}
	if mode == MatchLiteral {
		return func(value string) bool { return value == title }, nil
	}
	pattern, err := regexp.Compile(title)
	if err != nil {
		return nil, fmt.Errorf("invalid title regular expression: %w", err)
	}
	return pattern.MatchString, nil
}

func driveQuote(value string) string {
	return "'" + strings.NewReplacer("\\", "\\\\", "'", "\\'").Replace(value) + "'"
}

func (w *Workspace) folderID(ctx context.Context, folder string) (string, error) {
	if folder == "" {
		return "", nil
	}
	if strings.HasPrefix(folder, "id:") {
		id := strings.TrimPrefix(folder, "id:")
		if id == "" {
			return "", errors.New("folder ID cannot be empty")
		}
		return id, nil
	}
	files, err := w.backend.ListDocuments(ctx, "trashed = false and mimeType = 'application/vnd.google-apps.folder' and name = "+driveQuote(folder))
	if err != nil {
		return "", err
	}
	if len(files) != 1 {
		return "", fmt.Errorf("folder %q matched %d folders; use --folder id:DRIVE_ID", folder, len(files))
	}
	return files[0].ID, nil
}

// FindDocuments applies legacy title regular expressions after Drive pagination.
func (w *Workspace) FindDocuments(ctx context.Context, query DocumentQuery) ([]model.Document, error) {
	match, err := titleMatcher(query.Title, query.Match)
	if err != nil {
		return nil, err
	}
	if query.ID != "" {
		if query.Title != "" || query.Folder != "" {
			return nil, errors.New("--id cannot be combined with --title or --folder")
		}
		file, err := w.backend.GetDocument(ctx, query.ID)
		if err != nil {
			return nil, err
		}
		return []model.Document{file}, nil
	}
	folder, err := w.folderID(ctx, query.Folder)
	if err != nil {
		return nil, err
	}
	expression := "trashed = false and mimeType != 'application/vnd.google-apps.folder'"
	if folder != "" {
		expression += " and " + driveQuote(folder) + " in parents"
	}
	files, err := w.backend.ListDocuments(ctx, expression)
	if err != nil {
		return nil, err
	}
	result := []model.Document{}
	for _, file := range files {
		if match(file.Title) {
			result = append(result, file)
		}
	}
	return result, nil
}

// Conversion controls whether supported office/text input becomes a Google document.
type Conversion int

const (
	ConvertNative Conversion = iota
	KeepOriginal
)

// UploadFile streams a local regular file, resolving folder names without guessing.
func (w *Workspace) UploadFile(ctx context.Context, path, title, folder, format string, conversion Conversion) (model.Document, error) {
	parent, err := w.folderID(ctx, folder)
	if err != nil {
		return model.Document{}, err
	}
	file, err := os.Open(path)
	if err != nil {
		return model.Document{}, fmt.Errorf("open upload source: %w", err)
	}
	defer file.Close()
	stat, err := file.Stat()
	if err != nil {
		return model.Document{}, err
	}
	if !stat.Mode().IsRegular() {
		return model.Document{}, errors.New("upload source must be a regular file")
	}
	if title == "" {
		title = filepath.Base(path)
	}
	extension := strings.ToLower(filepath.Ext(path))
	if format != "" {
		extension = "." + strings.TrimPrefix(strings.ToLower(format), ".")
	}
	sourceMIME := mime.TypeByExtension(extension)
	if sourceMIME == "" {
		sourceMIME = "application/octet-stream"
	}
	targetMIME := ""
	if conversion == ConvertNative {
		switch extension {
		case ".txt", ".md", ".html", ".htm", ".doc", ".docx", ".odt", ".rtf":
			targetMIME = "application/vnd.google-apps.document"
		case ".csv", ".tsv", ".xls", ".xlsx", ".ods":
			targetMIME = "application/vnd.google-apps.spreadsheet"
		case ".ppt", ".pptx", ".odp":
			targetMIME = "application/vnd.google-apps.presentation"
		}
	}
	return w.backend.UploadDocument(ctx, title, parent, targetMIME, sourceMIME, file)
}

// DownloadFile refuses overwrites and removes partial files on transfer failure.
func (w *Workspace) DownloadFile(ctx context.Context, file model.Document, destination, format string) (err error) {
	if stat, statErr := os.Stat(destination); statErr == nil && stat.IsDir() {
		name := file.Title
		if !safeDownloadName(name) {
			return fmt.Errorf("unsafe remote filename %q; specify an explicit destination file", name)
		}
		if strings.HasPrefix(file.MIMEType, "application/vnd.google-apps.") && !strings.HasSuffix(name, "."+format) {
			name += "." + format
			if !safeDownloadName(name) {
				return fmt.Errorf("unsafe export extension %q", format)
			}
		}
		destination = filepath.Join(destination, name)
	}
	output, err := os.OpenFile(destination, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if err != nil {
		return fmt.Errorf("create download destination (existing files are never overwritten): %w", err)
	}
	defer func() {
		output.Close()
		if err != nil {
			os.Remove(destination)
		}
	}()
	if err = w.backend.DownloadDocument(ctx, file, format, output); err != nil {
		return err
	}
	if err = output.Sync(); err != nil {
		return err
	}
	return output.Close()
}

// TrashDocument requires an already resolved document; confirmation belongs to the caller.
func (w *Workspace) TrashDocument(ctx context.Context, file model.Document) error {
	return w.backend.TrashDocument(ctx, file.ID)
}

// safeDownloadName rejects traversal and Windows device/stream aliases on every OS.
func safeDownloadName(name string) bool {
	if name == "" || strings.TrimRight(name, ". ") != name || strings.ContainsAny(name, `/\:<>"|?*`) {
		return false
	}
	if strings.ContainsFunc(name, unicode.IsControl) {
		return false
	}
	stem, _, _ := strings.Cut(strings.ToUpper(name), ".")
	stem = strings.TrimRight(stem, " ")
	switch stem {
	case "CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$":
		return false
	}
	if strings.HasPrefix(stem, "COM") || strings.HasPrefix(stem, "LPT") {
		// Windows also treats superscript digits as device numbers.
		switch stem[3:] {
		case "1", "2", "3", "4", "5", "6", "7", "8", "9", "¹", "²", "³":
			return false
		}
	}
	return true
}
