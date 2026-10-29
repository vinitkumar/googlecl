package googleapi

import (
	"context"
	"fmt"
	"io"
	"strings"

	"github.com/vinitkumar/googlecl/internal/model"
	"google.golang.org/api/drive/v3"
	"google.golang.org/api/googleapi"
)

const driveFileFields = "id,name,mimeType,webViewLink"

func documentFromAPI(file *drive.File) model.Document {
	return model.Document{ID: file.Id, Title: file.Name, MIMEType: file.MimeType, URL: file.WebViewLink}
}

// ListDocuments follows all result pages; query is a Drive v3 expression.
func (c *Client) ListDocuments(ctx context.Context, query string) ([]model.Document, error) {
	files := []model.Document{}
	token := ""
	for page := 0; page < maxPages; page++ {
		result, err := c.drive.Files.List().Q(query).PageSize(1000).PageToken(token).OrderBy("name").Fields("nextPageToken,files(" + googleapi.Field(driveFileFields) + ")").Context(ctx).Do()
		if err != nil {
			return nil, fmt.Errorf("list Drive files: %w", err)
		}
		for _, file := range result.Files {
			files = append(files, documentFromAPI(file))
		}
		if result.NextPageToken == "" {
			return files, nil
		}
		token = result.NextPageToken
	}
	return nil, fmt.Errorf("Drive pagination exceeded %d pages; narrow the query", maxPages)
}

// GetDocument resolves an immutable Drive ID, not a possibly ambiguous title.
func (c *Client) GetDocument(ctx context.Context, id string) (model.Document, error) {
	file, err := c.drive.Files.Get(id).Fields(googleapi.Field(driveFileFields)).Context(ctx).Do()
	if err != nil {
		return model.Document{}, fmt.Errorf("get Drive file: %w", err)
	}
	return documentFromAPI(file), nil
}

// UploadDocument streams media; targetMIME requests a native Google conversion.
func (c *Client) UploadDocument(ctx context.Context, title, parent, targetMIME, sourceMIME string, source io.Reader) (model.Document, error) {
	metadata := &drive.File{Name: title, MimeType: targetMIME}
	if parent != "" {
		metadata.Parents = []string{parent}
	}
	file, err := c.drive.Files.Create(metadata).Media(source, googleapi.ContentType(sourceMIME)).Fields(googleapi.Field(driveFileFields)).Context(ctx).Do()
	if err != nil {
		return model.Document{}, fmt.Errorf("upload Drive file: %w", err)
	}
	return documentFromAPI(file), nil
}

// DownloadDocument exports native Google files and downloads other files unchanged.
func (c *Client) DownloadDocument(ctx context.Context, file model.Document, format string, dst io.Writer) error {
	var body io.ReadCloser
	if strings.HasPrefix(file.MIMEType, "application/vnd.google-apps.") {
		mimeType, err := ExportMIME(format)
		if err != nil {
			return err
		}
		response, err := c.drive.Files.Export(file.ID, mimeType).Context(ctx).Download()
		if err != nil {
			return fmt.Errorf("export Google document: %w", err)
		}
		body = response.Body
	} else {
		response, err := c.drive.Files.Get(file.ID).Context(ctx).Download()
		if err != nil {
			return fmt.Errorf("download Drive file: %w", err)
		}
		body = response.Body
	}
	defer body.Close()
	if _, err := io.Copy(dst, body); err != nil {
		return fmt.Errorf("write Drive download: %w", err)
	}
	return nil
}

// TrashDocument moves a file to trash; the alpha never permanently deletes files.
func (c *Client) TrashDocument(ctx context.Context, id string) error {
	_, err := c.drive.Files.Update(id, &drive.File{Trashed: true}).Context(ctx).Do()
	if err != nil {
		return fmt.Errorf("trash Drive file: %w", err)
	}
	return nil
}

// ExportMIME maps historical export extensions to current Google export MIME types.
func ExportMIME(format string) (string, error) {
	formats := map[string]string{
		"txt": "text/plain", "pdf": "application/pdf", "html": "text/html", "csv": "text/csv", "tsv": "text/tab-separated-values",
		"docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
		"xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
		"pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
		"odt":  "application/vnd.oasis.opendocument.text", "ods": "application/vnd.oasis.opendocument.spreadsheet",
		"odp": "application/vnd.oasis.opendocument.presentation", "rtf": "application/rtf", "png": "image/png", "svg": "image/svg+xml", "jpg": "image/jpeg",
	}
	mimeType, ok := formats[strings.ToLower(format)]
	if !ok {
		return "", fmt.Errorf("unsupported export format %q; use txt, pdf, docx, xlsx, pptx, odt, ods, odp, rtf, csv, tsv, html, png, jpg, or svg (xls/ppt are retired)", format)
	}
	return mimeType, nil
}
