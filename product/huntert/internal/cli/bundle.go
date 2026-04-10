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

type bundleVerifyResult struct {
	OK      bool              `json:"ok"`
	Command string            `json:"command"`
	Bundle  config.BundleInfo `json:"bundle"`
	Notes   []string          `json:"notes,omitempty"`
}

func runBundleCommand(args []string) int {
	if len(args) == 0 {
		fmt.Print(bundleHelp())
		return 0
	}

	switch args[0] {
	case "help", "-h", "--help":
		fmt.Print(bundleHelp())
		return 0
	case "verify":
		return runBundleVerify(args[1:])
	default:
		fmt.Fprintf(os.Stderr, "unknown bundle command %q\n\n", args[0])
		fmt.Fprint(os.Stderr, bundleHelp())
		return 1
	}
}

func runBundleVerify(args []string) int {
	fs := flag.NewFlagSet("bundle verify", flag.ContinueOnError)
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

	info, err := client.LoadBundle(cfg.ModelBundle)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}

	result := bundleVerifyResult{
		OK:      true,
		Command: "bundle verify",
		Bundle:  *info,
		Notes: []string{
			"bundle manifest loaded successfully",
			"python sidecar loaded the bundled LSTM checkpoint",
		},
	}

	if err := output.RenderBundleVerify(os.Stdout, cfg.Output, result); err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	return 0
}

func bundleHelp() string {
	return `HunterT bundle commands

Usage:
  huntert bundle verify [flags]
`
}
