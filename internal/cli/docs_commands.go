package cli

import (
	"fmt"
	"os"
	"strings"

	"github.com/spf13/cobra"
	"github.com/vinitkumar/googlecl/internal/app"
	"github.com/vinitkumar/googlecl/internal/model"
)

func newDocsCommand(opts *commandOptions) *cobra.Command {
	root := &cobra.Command{Use: "docs", Short: "List, upload, download, and trash Drive documents"}
	root.AddCommand(&cobra.Command{Use: "list [TITLE]", Short: "List documents (title,url-site by default)", Args: cobra.MaximumNArgs(1), RunE: opts.listDocuments})
	root.AddCommand(&cobra.Command{Use: "get [TITLE] [DEST]", Short: "Download matching documents; export native documents", Args: cobra.MaximumNArgs(2), RunE: opts.getDocuments})
	root.AddCommand(&cobra.Command{Use: "upload [FILE...]", Short: "Upload files, converting supported formats by default", RunE: opts.uploadDocuments})
	root.AddCommand(&cobra.Command{Use: "delete [TITLE]", Short: "Move matching documents to trash after confirmation", Args: cobra.MaximumNArgs(1), RunE: opts.deleteDocuments})
	root.AddCommand(&cobra.Command{Use: "edit [TITLE]", Short: "Not available in this alpha", RunE: func(cmd *cobra.Command, args []string) error {
		return fmt.Errorf("docs edit is not implemented in this alpha; use docs get and docs upload (upload creates a new file)")
	}})
	return root
}

func (o *commandOptions) documentQuery(args []string) (app.DocumentQuery, error) {
	title := o.title
	if len(args) > 0 {
		if title != "" || o.id != "" {
			return app.DocumentQuery{}, fmt.Errorf("unexpected positional title with --title or --id")
		}
		title = args[0]
	}
	return app.DocumentQuery{ID: o.id, Title: title, Folder: o.folder, Match: o.matchMode()}, nil
}

func (o *commandOptions) listDocuments(cmd *cobra.Command, args []string) error {
	query, err := o.documentQuery(args)
	if err != nil {
		return err
	}
	output, err := o.output("docs")
	if err != nil {
		return err
	}
	workspace, err := o.workspace(cmd, "docs")
	if err != nil {
		return err
	}
	files, err := workspace.FindDocuments(cmd.Context(), query)
	if err != nil {
		return err
	}
	return output.documents(o.deps.Output, files)
}

func (o *commandOptions) getDocuments(cmd *cobra.Command, args []string) error {
	query := app.DocumentQuery{ID: o.id, Title: o.title, Folder: o.folder, Match: o.matchMode()}
	if query.ID == "" && query.Title == "" && (query.Folder == "" || len(args) == 2 || o.destination != "") {
		if len(args) > 0 {
			query.Title, args = args[0], args[1:]
		}
		title, err := o.required(query.Title, "title")
		if err != nil {
			return err
		}
		query.Title = title
	}
	destination := o.destination
	if destination == "" && len(args) > 0 {
		destination, args = args[0], args[1:]
	}
	if len(args) != 0 {
		return fmt.Errorf("unexpected docs get arguments: %s", strings.Join(args, " "))
	}
	var err error
	destination, err = o.required(destination, "dest")
	if err != nil {
		return err
	}
	workspace, err := o.workspace(cmd, "docs")
	if err != nil {
		return err
	}
	files, err := workspace.FindDocuments(cmd.Context(), query)
	if err != nil {
		return err
	}
	if len(files) == 0 {
		return fmt.Errorf("no documents matched")
	}
	if len(files) > 1 {
		stat, err := os.Stat(destination)
		if err != nil || !stat.IsDir() {
			return fmt.Errorf("multiple documents matched; --dest must be an existing directory")
		}
	}
	for _, file := range files {
		format := o.downloadFormat(file)
		if err := workspace.DownloadFile(cmd.Context(), file, destination, format); err != nil {
			return err
		}
		o.progress("Downloaded %s", file.Title)
	}
	return nil
}

func (o *commandOptions) downloadFormat(file model.Document) string {
	if o.format != "" {
		return strings.ToLower(o.format)
	}
	key, fallback := "document_format", "txt"
	switch file.MIMEType {
	case "application/vnd.google-apps.spreadsheet":
		key, fallback = "spreadsheet_format", "xlsx"
	case "application/vnd.google-apps.presentation":
		key, fallback = "presentation_format", "pptx"
	case "application/vnd.google-apps.drawing":
		key, fallback = "drawing_format", "png"
	}
	return o.settings.Value("docs", key, fallback)
}

func (o *commandOptions) uploadDocuments(cmd *cobra.Command, args []string) error {
	paths := append([]string{}, args...)
	if o.source != "" {
		paths = append([]string{o.source}, paths...)
	}
	if len(paths) == 0 {
		source, err := o.required("", "src")
		if err != nil {
			return err
		}
		paths = []string{source}
	}
	if len(paths) > 1 && o.title != "" {
		return fmt.Errorf("--title requires a single upload source")
	}
	conversion := app.ConvertNative
	if o.noConvert {
		conversion = app.KeepOriginal
	}
	workspace, err := o.workspace(cmd, "docs")
	if err != nil {
		return err
	}
	uploaded := []model.Document{}
	for _, path := range paths {
		file, err := workspace.UploadFile(cmd.Context(), path, o.title, o.folder, o.format, conversion)
		if err != nil {
			return err
		}
		uploaded = append(uploaded, file)
		o.progress("Uploaded %s: %s", file.Title, file.URL)
	}
	if o.json {
		output, err := o.output("docs")
		if err != nil {
			return err
		}
		return output.documents(o.deps.Output, uploaded)
	}
	return nil
}

func (o *commandOptions) deleteDocuments(cmd *cobra.Command, args []string) error {
	query, err := o.documentQuery(args)
	if err != nil {
		return err
	}
	if query.Title == "" && query.ID == "" {
		query.Title, err = o.required("", "title")
		if err != nil {
			return err
		}
	}
	workspace, err := o.workspace(cmd, "docs")
	if err != nil {
		return err
	}
	files, err := workspace.FindDocuments(cmd.Context(), query)
	if err != nil {
		return err
	}
	if len(files) == 0 {
		return fmt.Errorf("no documents matched")
	}
	names := make([]string, 0, len(files))
	for _, file := range files {
		names = append(names, fmt.Sprintf("%q (%s)", file.Title, file.ID))
	}
	if err := o.confirm("Trash " + strings.Join(names, ", ")); err != nil {
		return err
	}
	for _, file := range files {
		if err := workspace.TrashDocument(cmd.Context(), file); err != nil {
			return err
		}
		o.progress("Trashed %s", file.Title)
	}
	return nil
}
