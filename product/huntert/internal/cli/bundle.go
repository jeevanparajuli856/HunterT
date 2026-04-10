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

	modelBundle := fs.String("model-bundle", "", "path to the runtime bundle")
	legacyBundle := fs.String("bundle", "", "deprecated alias for --model-bundle")
	pythonBin := fs.String("python-bin", "python3", "python executable for the runtime sidecar")
	outputValue := fs.String("output", "text", "output mode: text|json")

	if err := fs.Parse(args); err != nil {
		if handled := handleFlagParseError(os.Stdout, os.Stderr, &stderr, err); handled {
			return 0
		}
		fmt.Fprint(os.Stderr, stderr.String())
		return 1
	}

	mode, err := config.ParseOutputMode(*outputValue)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}

	cfg := config.BundleCommandConfig{
		ModelBundle: firstNonEmpty(*modelBundle, *legacyBundle),
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

	manifest, bundleDir, err := config.VerifyBundle(cfg.ModelBundle)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	actualSHA, err := config.VerifyModelSHA256(bundleDir, *manifest)
	if err != nil {
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
		Bundle: config.BundleInfo{
			ID:            info.ID,
			BundleDir:     info.BundleDir,
			Manifest:      info.Manifest,
			VocabSize:     info.VocabSize,
			WordlistCount: info.WordlistCount,
		},
		Notes: []string{
			"bundle manifest loaded successfully",
			"python sidecar loaded the bundled LSTM checkpoint",
		},
	}
	if result.Bundle.Manifest.Model.SHA256 == "" {
		result.Bundle.Manifest.Model.SHA256 = actualSHA
		result.Notes = append(result.Notes, "model sha256 computed from packaged artifact")
	} else {
		result.Notes = append(result.Notes, "packaged model sha256 matches the bundle manifest")
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
  huntert bundle verify [--model-bundle <path>] [--output text|json]
`
}
