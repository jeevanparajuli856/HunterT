package cli

import (
	"bytes"
	"flag"
	"fmt"
	"os"

	"huntert/internal/config"
	"huntert/internal/output"
	"huntert/internal/sidecar"
)

func runModelsCommand(args []string) int {
	if len(args) == 0 {
		fmt.Print(modelsHelp())
		return 0
	}

	switch args[0] {
	case "help", "-h", "--help":
		fmt.Print(modelsHelp())
		return 0
	case "inspect":
		return runModelsInspect(args[1:])
	default:
		fmt.Fprintf(os.Stderr, "unknown models command %q\n\n", args[0])
		fmt.Fprint(os.Stderr, modelsHelp())
		return 1
	}
}

func runModelsInspect(args []string) int {
	fs := flag.NewFlagSet("models inspect", flag.ContinueOnError)
	var stderr bytes.Buffer
	fs.SetOutput(&stderr)

	bundle := fs.String("bundle", "", "path to the runtime bundle")
	pythonBin := fs.String("python-bin", "python3", "python executable for the runtime sidecar")
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

	cfg := config.BundleCommandConfig{
		ModelBundle: *bundle,
		PythonBin:   *pythonBin,
		Output:      mode,
	}
	if err := cfg.Normalize(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	if err := cfg.Validate(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}

	client, err := sidecar.Start(cfg)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	defer client.Close()

	if _, err := client.LoadBundle(cfg.ModelBundle); err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	info, err := client.InspectBundle("")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}

	if err := output.RenderBundleInfo(os.Stdout, cfg.Output, *info); err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	return 0
}

func modelsHelp() string {
	return `HunterT model commands

Usage:
  huntert models inspect [flags]
`
}
