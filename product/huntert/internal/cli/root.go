package cli

import (
	"bytes"
	"flag"
	"fmt"
	"os"

	"huntert/internal/config"
	"huntert/internal/output"
)

const (
	versionValue = "0.2.0-dev"
	backendMode  = "python-lstm"
	bridgeMode   = "stdio-sidecar"
	engineMode   = "go-http"
)

func Execute(args []string) int {
	if len(args) == 0 {
		fmt.Print(rootHelp())
		return 0
	}

	switch args[0] {
	case "help", "-h", "--help":
		fmt.Print(rootHelp())
		return 0
	case "version":
		return runVersion(args[1:])
	case "attack":
		return runAttackCommand(args[1:])
	case "models":
		return runModelsCommand(args[1:])
	case "bundle":
		return runBundleCommand(args[1:])
	default:
		fmt.Fprintf(os.Stderr, "unknown command %q\n\n", args[0])
		fmt.Fprint(os.Stderr, rootHelp())
		return 1
	}
}

func runVersion(args []string) int {
	fs := flag.NewFlagSet("version", flag.ContinueOnError)
	var stderr bytes.Buffer
	fs.SetOutput(&stderr)

	outputValue := fs.String("output", "text", "output mode: text|json")
	if err := fs.Parse(args); err != nil {
		fmt.Fprint(os.Stderr, stderr.String())
		return 1
	}

	mode, err := config.ParseOutputMode(*outputValue)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}

	info := config.VersionInfo{
		Tool:    "huntert",
		Version: versionValue,
		Backend: backendMode,
		Bridge:  bridgeMode,
		Engine:  engineMode,
	}
	if err := output.RenderVersion(os.Stdout, mode, info); err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	return 0
}

func rootHelp() string {
	return `HunterT

Usage:
  huntert <command> [flags]

Commands:
  version            Print CLI version and runtime metadata
  models inspect     Inspect the configured runtime bundle
  bundle verify      Verify the runtime bundle and sidecar wiring
  attack run         Execute a live dirbuster-style enumeration run

Examples:
  huntert version
  huntert models inspect --output json
  huntert bundle verify
  huntert attack run --target https://example.com --dry-run
`
}
