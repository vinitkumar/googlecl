package cli

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/vinitkumar/googlecl/internal/auth"
)

func newAuthCommand(opts *commandOptions) *cobra.Command {
	service := "docs"
	root := &cobra.Command{Use: "auth", Short: "Authenticate a Google account profile"}
	root.PersistentFlags().StringVar(&service, "service", "docs", "Service to authorize: docs, calendar, contacts")
	login := &cobra.Command{Use: "login", Short: "Authorize with a browser and loopback callback", Args: cobra.NoArgs, RunE: func(cmd *cobra.Command, args []string) error {
		if err := auth.Login(cmd.Context(), auth.LoginOptions{Profile: opts.profile, Service: service, Credentials: opts.credentials, NoBrowser: opts.noBrowser}, opts.deps.Errors); err != nil {
			return err
		}
		opts.progress("Authenticated %s for %s.", opts.profile, service)
		return nil
	}}
	login.Flags().BoolVar(&opts.noBrowser, "no-browser", false, "Print the authorization URL without opening a browser")
	root.AddCommand(login, &cobra.Command{Use: "status", Short: "Inspect saved credentials without network access", Args: cobra.NoArgs, RunE: func(cmd *cobra.Command, args []string) error {
		status, err := auth.TokenStatus(opts.profile, service)
		if err != nil {
			return err
		}
		_, err = fmt.Fprintf(opts.deps.Output, "%s (%s): %s\n", opts.profile, service, status)
		return err
	}}, &cobra.Command{Use: "logout", Short: "Remove local credentials (does not revoke Google's grant)", Args: cobra.NoArgs, RunE: func(cmd *cobra.Command, args []string) error {
		if err := auth.Logout(opts.profile, service); err != nil {
			return err
		}
		opts.progress("Removed local %s credentials for %s.", service, opts.profile)
		return nil
	}})
	return root
}
