package cli

import (
	"fmt"
	"strings"

	"github.com/spf13/cobra"
	"github.com/spf13/pflag"
)

func validateCommandFlags(cmd *cobra.Command) error {
	if cmd.Parent() == nil {
		return nil
	}
	name := cmd.Parent().Name() + " " + cmd.Name()
	allowed, ok := map[string]string{
		"docs list":          "title,folder,id,fields,delimiter,json,literal",
		"docs get":           "title,folder,id,dest,format,literal",
		"docs upload":        "src,title,folder,format,no-convert,json",
		"docs delete":        "title,folder,id,literal",
		"calendar list":      "title,query,date,cal,fields,delimiter,json,literal",
		"calendar today":     "title,query,cal,fields,delimiter,json,literal",
		"calendar add":       "src,date,cal,reminder,json",
		"calendar delete":    "title,query,date,cal,id,literal",
		"calendar calendars": "json,delimiter",
		"contacts list":      "title,fields,delimiter,json,literal",
		"auth login":         "service,no-browser",
		"auth logout":        "service",
		"auth status":        "service",
	}[name]
	if !ok {
		return nil
	}
	allowed += ",user,config,help"
	if name != "auth status" && name != "auth logout" {
		allowed += ",credentials"
	}
	if strings.HasSuffix(name, " delete") {
		allowed += ",yes"
	}
	if strings.HasSuffix(name, " delete") || name == "docs upload" || name == "docs get" || name == "calendar add" || name == "auth login" || name == "auth logout" {
		allowed += ",quiet"
	}
	// JSON emits complete resources; text formatting flags cannot affect it.
	jsonOutput, _ := cmd.Flags().GetBool("json")
	var invalid []string
	cmd.Flags().Visit(func(flag *pflag.Flag) {
		if !strings.Contains(","+allowed+",", ","+flag.Name+",") || (jsonOutput && (flag.Name == "fields" || flag.Name == "delimiter")) {
			invalid = append(invalid, "--"+flag.Name)
		}
	})
	if len(invalid) > 0 {
		return fmt.Errorf("%s does not support %s; flags are never silently ignored", name, strings.Join(invalid, ", "))
	}
	return nil
}
