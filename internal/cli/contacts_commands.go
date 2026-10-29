package cli

import (
	"fmt"
	"github.com/spf13/cobra"
)

func newContactsCommand(opts *commandOptions) *cobra.Command {
	root := &cobra.Command{Use: "contacts", Short: "Read saved contacts through the People API"}
	root.AddCommand(&cobra.Command{Use: "list [NAME]", Short: "List contacts (name,email by default)", Args: cobra.MaximumNArgs(1), RunE: func(cmd *cobra.Command, args []string) error {
		title, err := opts.eventTitle(args)
		if err != nil {
			return err
		}
		output, err := opts.output("contacts")
		if err != nil {
			return err
		}
		workspace, err := opts.workspace(cmd, "contacts")
		if err != nil {
			return err
		}
		contacts, err := workspace.Contacts(cmd.Context(), title, opts.matchMode())
		if err != nil {
			return err
		}
		return output.contacts(opts.deps.Output, contacts)
	}})
	for _, task := range []string{"add", "delete", "list-groups", "add-groups", "delete-groups"} {
		root.AddCommand(&cobra.Command{Use: task, Short: "Not available in this alpha", RunE: func(cmd *cobra.Command, args []string) error {
			return fmt.Errorf("contacts %s is not implemented in this alpha; only contacts list is supported", cmd.Name())
		}})
	}
	return root
}
