// GoogleCL preserves the historical google command without a Python runtime.
package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"

	"github.com/vinitkumar/googlecl/internal/app"
	"github.com/vinitkumar/googlecl/internal/auth"
	"github.com/vinitkumar/googlecl/internal/cli"
	"github.com/vinitkumar/googlecl/internal/googleapi"
	_ "time/tzdata" // Calendar date handling must work without system zoneinfo on Windows.
)

var version = "1.0.0-alpha.1-dev"

func main() {
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt)
	defer stop()
	command := cli.NewCommand(version, cli.Dependencies{Input: os.Stdin, Output: os.Stdout, Errors: os.Stderr, Workspace: newWorkspace})
	if err := command.ExecuteContext(ctx); err != nil {
		fmt.Fprintln(os.Stderr, "google:", err)
		os.Exit(1)
	}
}

func newWorkspace(ctx context.Context, opts auth.LoginOptions) (*app.Workspace, error) {
	client, err := auth.AuthorizedClient(ctx, opts)
	if err != nil {
		return nil, err
	}
	backend, err := googleapi.NewClient(ctx, opts.Service, client)
	if err != nil {
		return nil, err
	}
	return app.NewWorkspace(backend), nil
}
