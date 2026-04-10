package engine

import (
	"context"
	"os"
	"path/filepath"
	"testing"
	"time"

	"net/http"
	"net/http/httptest"

	"huntert/internal/config"
	"huntert/internal/sidecar"
)

type stubPredictor struct{}

func (stubPredictor) PredictNext(tokens []string, topK int) ([]sidecar.Candidate, error) {
	if len(tokens) == 1 && tokens[0] == "<sos>" {
		return []sidecar.Candidate{
			{Token: "admin", Prob: 0.9},
			{Token: "story", Prob: 0.8},
		}, nil
	}
	return nil, nil
}

func TestExpandTokenVariantsAddsDotSeparatedExtensions(t *testing.T) {
	variants := expandTokenVariants("admin", []string{"php", "txt"})
	expected := map[string]struct{}{
		"admin":     {},
		"admin.php": {},
		"admin.txt": {},
	}
	for _, variant := range variants {
		delete(expected, variant)
	}
	if len(expected) != 0 {
		t.Fatalf("missing expected variants: %v", expected)
	}
}

func TestValidateResumeStateRejectsMismatchedInputs(t *testing.T) {
	cfg := config.AttackRunConfig{
		Target:      "https://example.com",
		ModelBundle: "/tmp/bundle-a",
	}
	state := &runState{
		Target: "https://other.example.com",
		Bundle: "/tmp/bundle-b",
	}
	if err := validateResumeState(cfg, state); err == nil {
		t.Fatalf("validateResumeState() returned nil error for mismatched target and bundle")
	}
}

func TestRunCreatesOutputsAndFindsInterestingPaths(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/admin.php":
			w.WriteHeader(http.StatusOK)
			_, _ = w.Write([]byte("admin"))
		case "/story":
			w.WriteHeader(http.StatusOK)
			_, _ = w.Write([]byte("story"))
		default:
			w.WriteHeader(http.StatusNotFound)
		}
	}))
	defer server.Close()

	bundleDir := t.TempDir()
	writeEngineBundleFixture(t, bundleDir)
	outputDir := filepath.Join(t.TempDir(), "run")

	cfg := config.AttackRunConfig{
		Target:          server.URL,
		Threads:         2,
		Timeout:         2 * time.Second,
		UserAgent:       "HunterT-Test",
		Method:          "GET",
		Extensions:      []string{"php"},
		MaxDepth:        2,
		PredictionLimit: 10,
		MaxRequests:     10,
		StatusInclude:   []int{200},
		OutputDir:       outputDir,
		ModelBundle:     bundleDir,
	}
	manifest := config.BundleManifest{
		ID:      "default",
		Name:    "HunterT Test Bundle",
		Backend: "python-lstm",
		Files:   config.BundleFiles{Wordlist: "wordlist.txt"},
	}

	report, err := Run(context.Background(), cfg, manifest, stubPredictor{})
	if err != nil {
		t.Fatalf("Run() returned error: %v", err)
	}
	if report.Requests == 0 {
		t.Fatalf("expected requests to be issued")
	}
	if report.Interesting < 2 {
		t.Fatalf("expected at least 2 interesting hits, got %d", report.Interesting)
	}

	seen := map[string]struct{}{}
	for _, discovery := range report.Discoveries {
		seen[discovery.Path] = struct{}{}
	}
	for _, path := range []string{"admin.php", "story"} {
		if _, ok := seen[path]; !ok {
			t.Fatalf("expected discovery for %q, got %v", path, seen)
		}
	}

	for _, path := range []string{
		report.ResumeState,
		report.RequestsFile,
		report.FindingsFile,
		report.SummaryFile,
	} {
		if _, err := os.Stat(path); err != nil {
			t.Fatalf("expected output file %s: %v", path, err)
		}
	}
}

func writeEngineBundleFixture(t *testing.T, bundleDir string) {
	t.Helper()

	if err := os.WriteFile(filepath.Join(bundleDir, "wordlist.txt"), []byte("\n"), 0o644); err != nil {
		t.Fatalf("write wordlist: %v", err)
	}
}
