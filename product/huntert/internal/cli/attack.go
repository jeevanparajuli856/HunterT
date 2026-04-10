package cli

import (
	"bytes"
	"context"
	"flag"
	"fmt"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"syscall"
	"time"

	"huntert/internal/config"
	"huntert/internal/engine"
	"huntert/internal/output"
	"huntert/internal/sidecar"
)

type stringListFlag []string
type intListFlag []int

func (flagValue *stringListFlag) String() string {
	return fmt.Sprintf("%v", []string(*flagValue))
}

func (flagValue *stringListFlag) Set(value string) error {
	*flagValue = append(*flagValue, value)
	return nil
}

func (flagValue *intListFlag) String() string {
	return fmt.Sprintf("%v", []int(*flagValue))
}

func (flagValue *intListFlag) Set(value string) error {
	for _, part := range splitCommaList(value) {
		status, err := parseStatus(part)
		if err != nil {
			return err
		}
		*flagValue = append(*flagValue, status)
	}
	return nil
}

func runAttackCommand(args []string) int {
	if len(args) == 0 {
		fmt.Print(attackHelp())
		return 0
	}

	switch args[0] {
	case "help", "-h", "--help":
		fmt.Print(attackHelp())
		return 0
	case "run":
		return runAttack(args[1:])
	default:
		fmt.Fprintf(os.Stderr, "unknown attack command %q\n\n", args[0])
		fmt.Fprint(os.Stderr, attackHelp())
		return 1
	}
}

func runAttack(args []string) int {
	fs := flag.NewFlagSet("attack run", flag.ContinueOnError)
	var stderr bytes.Buffer
	fs.SetOutput(&stderr)

	var headers stringListFlag
	var includeStatuses intListFlag
	var excludeStatuses intListFlag

	target := fs.String("target", "", "target URL")
	threads := fs.Int("threads", 20, "number of concurrent workers")
	timeout := fs.Duration("timeout", 10*time.Second, "per-request timeout")
	rateLimit := fs.Float64("rate-limit", 0, "global request rate limit per second (0 disables)")
	fs.Var(&headers, "header", "repeatable HTTP header in 'Key: Value' form")
	userAgent := fs.String("user-agent", "HunterT/0.2.0-dev", "user-agent header")
	method := fs.String("method", "GET", "HTTP method: GET or HEAD")
	followRedirects := fs.Bool("follow-redirects", false, "follow HTTP redirects")
	insecure := fs.Bool("insecure", false, "skip TLS verification")
	extensions := fs.String("extensions", "", "comma-separated file extensions to try")
	maxDepth := fs.Int("max-depth", 3, "maximum recursive depth")
	predictionLimit := fs.Int("prediction-limit", 128, "top-k model predictions to consider per node")
	maxRequests := fs.Int("max-requests", 1000, "maximum unique requests to schedule")
	fs.Var(&includeStatuses, "status-include", "repeatable or comma-separated status codes considered interesting")
	fs.Var(&excludeStatuses, "status-exclude", "repeatable or comma-separated status codes to exclude")
	outputDir := fs.String("output-dir", "", "directory for run outputs")
	outputValue := fs.String("output", "text", "output mode: text|json")
	resume := fs.String("resume", "", "path to a previous state.json file")
	dryRun := fs.Bool("dry-run", false, "load the bundle and validate the sidecar without making HTTP requests")
	modelBundle := fs.String("model-bundle", "", "path to the runtime bundle directory")
	pythonBin := fs.String("python-bin", "python3", "python executable for the runtime sidecar")

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

	cfg := config.AttackRunConfig{
		Target:          *target,
		Threads:         *threads,
		Timeout:         *timeout,
		RateLimit:       *rateLimit,
		Headers:         []string(headers),
		UserAgent:       *userAgent,
		Method:          *method,
		FollowRedirects: *followRedirects,
		Insecure:        *insecure,
		Extensions:      splitCommaList(*extensions),
		MaxDepth:        *maxDepth,
		PredictionLimit: *predictionLimit,
		MaxRequests:     *maxRequests,
		StatusInclude:   []int(includeStatuses),
		StatusExclude:   []int(excludeStatuses),
		OutputDir:       *outputDir,
		Output:          mode,
		Resume:          *resume,
		DryRun:          *dryRun,
		ModelBundle:     *modelBundle,
		PythonBin:       *pythonBin,
	}
	if err := cfg.Normalize(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	if err := cfg.Validate(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}

	manifest, err := config.LoadBundleManifest(cfg.ModelBundle)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	sidecarCfg := config.BundleCommandConfig{
		ModelBundle: cfg.ModelBundle,
		PythonBin:   cfg.PythonBin,
		Output:      cfg.Output,
		RepoRoot:    cfg.RepoRoot,
		ProductRoot: cfg.ProductRoot,
	}
	client, err := sidecar.Start(sidecarCfg)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	defer client.Close()

	if _, err := client.LoadBundle(cfg.ModelBundle); err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}

	report, err := engine.Run(ctx, cfg, manifest, client)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	report.Stderr = client.Stderr()

	if err := output.RenderAttackReport(os.Stdout, cfg.Output, *report); err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	return 0
}

func attackHelp() string {
	return `HunterT attack commands

Usage:
  huntert attack run --target <url> [flags]

Key flags:
  --threads, --timeout, --rate-limit
  --header, --user-agent, --method
  --follow-redirects, --insecure
  --extensions, --max-depth, --prediction-limit, --max-requests
  --status-include, --status-exclude
  --output, --output-dir, --resume
  --model-bundle, --python-bin, --dry-run
`
}

func splitCommaList(value string) []string {
	if strings.TrimSpace(value) == "" {
		return nil
	}

	parts := strings.Split(value, ",")
	result := make([]string, 0, len(parts))
	for _, part := range parts {
		part = strings.TrimSpace(part)
		if part == "" {
			continue
		}
		result = append(result, part)
	}
	return result
}

func parseStatus(value string) (int, error) {
	status, err := strconv.Atoi(strings.TrimSpace(value))
	if err != nil {
		return 0, fmt.Errorf("invalid status code %q", value)
	}
	if status < 100 || status > 599 {
		return 0, fmt.Errorf("invalid status code %q", value)
	}
	return status, nil
}

func firstNonEmpty(values ...string) string {
	for _, value := range values {
		if strings.TrimSpace(value) != "" {
			return value
		}
	}
	return ""
}
