package output

import (
	"encoding/json"
	"fmt"
	"io"
	"strings"

	"huntert/internal/config"
	"huntert/internal/engine"
)

type bundleVerifyResult interface {
	GetCommand() string
}

func RenderVersion(w io.Writer, mode config.OutputMode, info config.VersionInfo) error {
	if mode == config.OutputJSON {
		return writeJSON(w, info)
	}

	_, err := fmt.Fprintf(
		w,
		"%s %s (backend=%s, bridge=%s, engine=%s)\n",
		info.Tool,
		info.Version,
		info.Backend,
		info.Bridge,
		info.Engine,
	)
	return err
}

func RenderBundleInfo(w io.Writer, mode config.OutputMode, info config.BundleInfo) error {
	if mode == config.OutputJSON {
		return writeJSON(w, info)
	}

	lines := []string{
		fmt.Sprintf("bundle: %s", info.Manifest.Name),
		fmt.Sprintf("id: %s", info.ID),
		fmt.Sprintf("path: %s", info.BundleDir),
		fmt.Sprintf("backend: %s", info.Manifest.Backend),
		fmt.Sprintf("model: %s", info.Manifest.Model.SourceName),
		fmt.Sprintf("model sha256: %s", valueOrUnavailable(info.Manifest.Model.SHA256)),
		fmt.Sprintf("vocab size: %d", info.VocabSize),
		fmt.Sprintf("wordlist entries: %d", info.WordlistCount),
	}
	_, err := fmt.Fprintln(w, strings.Join(lines, "\n"))
	return err
}

func RenderBundleVerify(w io.Writer, mode config.OutputMode, result any) error {
	if mode == config.OutputJSON {
		return writeJSON(w, result)
	}

	type verifyShape struct {
		Command string            `json:"command"`
		Bundle  config.BundleInfo `json:"bundle"`
		Notes   []string          `json:"notes"`
	}
	typed, ok := result.(verifyShape)
	if !ok {
		payload, err := json.Marshal(result)
		if err != nil {
			return err
		}
		if err := json.Unmarshal(payload, &typed); err != nil {
			return err
		}
	}

	lines := []string{
		typed.Command,
		"status: ok",
		fmt.Sprintf("bundle: %s", typed.Bundle.Manifest.Name),
		fmt.Sprintf("path: %s", typed.Bundle.BundleDir),
		fmt.Sprintf("model: %s", typed.Bundle.Manifest.Model.SourceName),
		fmt.Sprintf("model sha256: %s", valueOrUnavailable(typed.Bundle.Manifest.Model.SHA256)),
		fmt.Sprintf("vocab size: %d", typed.Bundle.VocabSize),
		fmt.Sprintf("wordlist entries: %d", typed.Bundle.WordlistCount),
	}
	for _, note := range typed.Notes {
		lines = append(lines, fmt.Sprintf("note: %s", note))
	}
	_, err := fmt.Fprintln(w, strings.Join(lines, "\n"))
	return err
}

func RenderAttackReport(w io.Writer, mode config.OutputMode, report engine.Report, findingsOnly bool) error {
	if mode == config.OutputJSON {
		return writeJSON(w, report)
	}
	if findingsOnly {
		for _, discovery := range report.Discoveries {
			if _, err := fmt.Fprintf(w, "%s %d\n", discovery.URL, discovery.StatusCode); err != nil {
				return err
			}
		}
		return nil
	}

	lines := []string{
		report.Command,
		"status: ok",
		fmt.Sprintf("target: %s", report.Target),
		fmt.Sprintf("bundle: %s", report.BundleID),
		fmt.Sprintf("requests: %d", report.Requests),
		fmt.Sprintf("interesting: %d", report.Interesting),
		fmt.Sprintf("errors: %d", report.Errors),
		fmt.Sprintf("oov_tokens: %d", len(report.OOVTokens)),
		fmt.Sprintf("duration_ms: %d", report.DurationMS),
		fmt.Sprintf("output_dir: %s", report.OutputDir),
	}
	if report.OOVTokensFile != "" {
		lines = append(lines, fmt.Sprintf("oov_tokens_file: %s", report.OOVTokensFile))
	}
	if report.DryRun {
		lines = append(lines, "mode: dry-run")
	}
	for _, note := range report.Notes {
		lines = append(lines, fmt.Sprintf("note: %s", note))
	}
	limit := min(len(report.Discoveries), 10)
	for idx := 0; idx < limit; idx++ {
		discovery := report.Discoveries[idx]
		lines = append(
			lines,
			fmt.Sprintf(
				"hit: %s status=%d source=%s duration_ms=%d",
				discovery.Path,
				discovery.StatusCode,
				discovery.Source,
				discovery.DurationMS,
			),
		)
	}
	if limit < len(report.Discoveries) {
		lines = append(lines, fmt.Sprintf("note: %d additional hits written to %s", len(report.Discoveries)-limit, report.FindingsFile))
	}
	_, err := fmt.Fprintln(w, strings.Join(lines, "\n"))
	return err
}

func writeJSON(w io.Writer, value any) error {
	encoder := json.NewEncoder(w)
	encoder.SetIndent("", "  ")
	return encoder.Encode(value)
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func valueOrUnavailable(value string) string {
	value = strings.TrimSpace(value)
	if value == "" {
		return "unavailable"
	}
	return value
}
