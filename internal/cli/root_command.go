// Package cli preserves historical GoogleCL command parsing and text output.
package cli

import (
	"bufio"
	"context"
	"fmt"
	"io"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/spf13/cobra"
	"github.com/vinitkumar/googlecl/internal/app"
	"github.com/vinitkumar/googlecl/internal/auth"
	"github.com/vinitkumar/googlecl/internal/config"
	"golang.org/x/term"
)

// WorkspaceFactory delays authentication until a validated command needs an API.
type WorkspaceFactory func(context.Context, auth.LoginOptions) (*app.Workspace, error)

// Dependencies supplies replaceable IO and API construction for command tests.
type Dependencies struct {
	Workspace WorkspaceFactory
	Input     io.Reader
	Output    io.Writer
	Errors    io.Writer
}

type commandOptions struct {
	profile, credentials, configPath                                                                   string
	fields, delimiter, title, folder, format, destination, source, calendar, date, query, reminder, id string
	json, yes, quiet, noConvert, noBrowser, literal                                                    bool
	settings                                                                                           *config.Settings
	input                                                                                              *bufio.Reader
	deps                                                                                               Dependencies
}

// NewCommand builds a fresh command tree; flags never leak between invocations.
func NewCommand(version string, deps Dependencies) *cobra.Command {
	opts := &commandOptions{deps: deps, input: bufio.NewReader(deps.Input)}
	root := &cobra.Command{Use: "google", Short: "Command-line access to Google services", Version: version, SilenceUsage: true, SilenceErrors: true}
	root.SetIn(deps.Input)
	root.SetOut(deps.Output)
	root.SetErr(deps.Errors)
	root.CompletionOptions.DisableDefaultCmd = true
	root.RunE = func(cmd *cobra.Command, args []string) error {
		if len(args) != 0 {
			return fmt.Errorf("unknown command %q", args[0])
		}
		return cmd.Help()
	}
	flags := root.PersistentFlags()
	flags.StringVarP(&opts.profile, "user", "u", "default", "Named account profile (email is also a login hint)")
	flags.StringVar(&opts.credentials, "credentials", "", "Google Desktop OAuth client JSON file")
	flags.StringVar(&opts.configPath, "config", "", "Legacy INI configuration file")
	flags.StringVar(&opts.fields, "fields", "", "Comma-separated output fields (legacy defaults)")
	flags.StringVar(&opts.delimiter, "delimiter", ",", "Legacy output delimiter")
	flags.StringVarP(&opts.title, "title", "n", "", "Title/name regular expression")
	flags.StringVarP(&opts.folder, "folder", "f", "", "Folder title, or id:DRIVE_ID")
	flags.StringVar(&opts.format, "format", "", "Upload type or download export extension")
	flags.StringVar(&opts.destination, "dest", "", "Download destination")
	flags.StringVar(&opts.source, "src", "", "Upload filename or Calendar event text")
	flags.StringVar(&opts.calendar, "cal", "", "Calendar title or ID (default: primary)")
	flags.StringVarP(&opts.date, "date", "d", "", "Date or inclusive date range: YYYY-MM-DD[,YYYY-MM-DD]")
	flags.StringVarP(&opts.query, "query", "q", "", "Calendar full-text query")
	flags.StringVar(&opts.reminder, "reminder", "", "Reminder: minutes or 10m, 2h, 1d")
	flags.StringVar(&opts.id, "id", "", "Exact Drive file or Calendar event ID")
	flags.BoolVar(&opts.json, "json", false, "Emit JSON arrays instead of legacy text")
	flags.BoolVar(&opts.yes, "yes", false, "Confirm destructive operations without prompting")
	flags.BoolVar(&opts.quiet, "quiet", false, "Suppress progress messages, not list results")
	flags.BoolVar(&opts.noConvert, "no-convert", false, "Upload without Google document conversion")
	flags.BoolVar(&opts.literal, "literal", false, "Match literal titles rather than regular expressions")
	root.PersistentPreRunE = func(cmd *cobra.Command, args []string) error {
		if err := validateCommandFlags(cmd); err != nil {
			return err
		}
		settings, err := config.LoadSettings(opts.configPath)
		if err != nil {
			return err
		}
		opts.settings = settings
		service := cmd.Name()
		if cmd.Parent() != nil {
			service = cmd.Parent().Name()
		}
		// Authentication and API commands must resolve the same service profile.
		if service == "auth" {
			service, err = cmd.Flags().GetString("service")
			if err != nil {
				return err
			}
		}
		defaults := map[string]*string{"user": &opts.profile, "fields": &opts.fields, "delimiter": &opts.delimiter, "folder": &opts.folder, "cal": &opts.calendar}
		for key, target := range defaults {
			if !cmd.Flags().Changed(key) {
				*target = settings.Value(service, key, *target)
			}
		}
		if !cmd.Flags().Changed("literal") {
			regex, err := strconv.ParseBool(settings.Value(service, "regex", "true"))
			if err != nil {
				return fmt.Errorf("config regex must be true or false")
			}
			opts.literal = !regex
		}
		if opts.delimiter == "" {
			opts.delimiter = ","
		}
		return nil
	}
	root.AddCommand(newAuthCommand(opts), newDocsCommand(opts), newCalendarCommand(opts), newContactsCommand(opts))
	for _, service := range []string{"picasa", "finance", "youtube", "blogger", "gmail"} {
		root.AddCommand(&cobra.Command{Use: service, Short: "Unavailable in this alpha", DisableFlagParsing: true, RunE: func(cmd *cobra.Command, args []string) error {
			if cmd.Name() == "picasa" || cmd.Name() == "finance" {
				return fmt.Errorf("%s: the original Google API was retired; this service cannot be restored", cmd.Name())
			}
			return fmt.Errorf("%s is not implemented in this alpha; see docs/compatibility.md", cmd.Name())
		}})
	}
	// Historical spelling puts 'help' after the service rather than before it.
	for _, service := range root.Commands() {
		if !service.HasSubCommands() {
			continue
		}
		service.AddCommand(&cobra.Command{Use: "help", Short: "Show service help", RunE: func(cmd *cobra.Command, args []string) error { return cmd.Parent().Help() }})
	}
	return root
}

func (o *commandOptions) workspace(cmd *cobra.Command, service string) (*app.Workspace, error) {
	if o.deps.Workspace == nil {
		return nil, fmt.Errorf("API workspace is not configured")
	}
	return o.deps.Workspace(cmd.Context(), auth.LoginOptions{Profile: o.profile, Service: service, Credentials: o.credentials})
}

func (o *commandOptions) matchMode() app.MatchMode {
	if o.literal {
		return app.MatchLiteral
	}
	return app.MatchRegex
}

func (o *commandOptions) output(service string) (legacyOutput, error) {
	// JSON resources are independent of legacy text field/date settings.
	if o.json {
		return legacyOutput{json: true}, nil
	}
	defaults := map[string]string{"docs": "title,url-site", "calendar": "title,when", "contacts": "name,email"}
	fields := o.fields
	if fields == "" {
		fields = defaults[service]
	}
	allowed := map[string]string{"docs": "id,title,name,url,url-site,type", "calendar": "id,title,url,url-site,when,where,start,end", "contacts": "id,title,name,email,phone"}
	output := legacyOutput{fields: strings.Split(fields, ","), delimiter: o.delimiter, missing: o.settings.Value(service, "missing_field_value", "N/A"), json: o.json}
	for _, field := range output.fields {
		if !strings.Contains(","+allowed[service]+",", ","+field+",") {
			return output, fmt.Errorf("unsupported %s field %q; supported: %s", service, field, allowed[service])
		}
	}
	if service != "calendar" {
		return output, nil
	}
	layout, err := dateLayout(o.settings.Value(service, "date_print_format", "%b %d %H:%M"))
	if err != nil {
		return output, err
	}
	output.dateLayout = layout
	return output, nil
}

func (o *commandOptions) interactive() bool {
	file, ok := o.deps.Input.(*os.File)
	return ok && term.IsTerminal(int(file.Fd()))
}

func (o *commandOptions) required(value, name string) (string, error) {
	if value != "" {
		return value, nil
	}
	if !o.interactive() {
		return "", fmt.Errorf("--%s is required (non-interactive input)", name)
	}
	fmt.Fprintf(o.deps.Errors, "Please specify %s: ", name)
	line, err := o.input.ReadString('\n')
	if err != nil {
		return "", err
	}
	line = strings.TrimSpace(line)
	if line == "" {
		return "", fmt.Errorf("%s cannot be empty", name)
	}
	return line, nil
}

func (o *commandOptions) confirm(description string) error {
	if o.yes {
		return nil
	}
	if !o.interactive() {
		return fmt.Errorf("refusing %s without --yes in non-interactive mode", description)
	}
	fmt.Fprintf(o.deps.Errors, "%s? [y/N] ", description)
	answer, err := o.input.ReadString('\n')
	if err != nil {
		return err
	}
	answer = strings.ToLower(strings.TrimSpace(answer))
	if answer != "y" && answer != "yes" {
		return fmt.Errorf("operation canceled")
	}
	return nil
}

func (o *commandOptions) progress(format string, args ...any) {
	if !o.quiet {
		fmt.Fprintf(o.deps.Errors, format+"\n", args...)
	}
}

func nowLocal() time.Time { return time.Now() }
