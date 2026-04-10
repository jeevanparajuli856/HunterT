package config

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestAttackRunConfigValidateDefaults(t *testing.T) {
	bundleDir := t.TempDir()
	writeBundleFixture(t, bundleDir)

	cfg := AttackRunConfig{
		Target:      "https://example.com",
		ModelBundle: bundleDir,
		Timeout:     5 * time.Second,
	}

	if err := cfg.Validate(); err != nil {
		t.Fatalf("Validate() returned error: %v", err)
	}

	if cfg.Threads != 20 {
		t.Fatalf("expected default threads 20, got %d", cfg.Threads)
	}
	if cfg.PythonBin != "python3" {
		t.Fatalf("expected default python3, got %q", cfg.PythonBin)
	}
	if cfg.Output != "text" {
		t.Fatalf("expected default text output, got %q", cfg.Output)
	}
}

func TestAttackRunConfigNormalizePrefersRepoPython(t *testing.T) {
	repoRoot := t.TempDir()
	productRoot := filepath.Join(repoRoot, "product", "huntert")
	repoPython := filepath.Join(repoRoot, ".venv", "bin", "python3")
	defaultBundle := filepath.Join(productRoot, "runtime", "bundles", "default")

	for _, dir := range []string{
		filepath.Join(productRoot, "python", "huntert_runtime"),
		filepath.Dir(repoPython),
		defaultBundle,
	} {
		if err := os.MkdirAll(dir, 0o755); err != nil {
			t.Fatalf("mkdir %s: %v", dir, err)
		}
	}
	if err := os.WriteFile(filepath.Join(repoRoot, "AGENTS.md"), []byte("huntert"), 0o644); err != nil {
		t.Fatalf("write AGENTS.md: %v", err)
	}
	if err := os.WriteFile(filepath.Join(productRoot, "go.mod"), []byte("module huntert\n"), 0o644); err != nil {
		t.Fatalf("write go.mod: %v", err)
	}
	if err := os.WriteFile(repoPython, []byte("#!/usr/bin/env python3\n"), 0o755); err != nil {
		t.Fatalf("write repo python: %v", err)
	}
	writeBundleFixture(t, defaultBundle)

	wd, err := os.Getwd()
	if err != nil {
		t.Fatalf("getwd: %v", err)
	}
	t.Cleanup(func() { _ = os.Chdir(wd) })
	if err := os.Chdir(productRoot); err != nil {
		t.Fatalf("chdir product root: %v", err)
	}

	cfg := AttackRunConfig{
		Target:  "https://example.com",
		Timeout: 5 * time.Second,
	}
	if err := cfg.Normalize(); err != nil {
		t.Fatalf("Normalize() returned error: %v", err)
	}
	if cfg.PythonBin != repoPython {
		t.Fatalf("expected repo python %q, got %q", repoPython, cfg.PythonBin)
	}
	if cfg.ProductRoot != productRoot {
		t.Fatalf("expected product root %q, got %q", productRoot, cfg.ProductRoot)
	}
	if cfg.ModelBundle != defaultBundle {
		t.Fatalf("expected default bundle %q, got %q", defaultBundle, cfg.ModelBundle)
	}
}

func TestAttackRunConfigNormalizeResolvesRelativeBundleFromProductRoot(t *testing.T) {
	repoRoot := t.TempDir()
	productRoot := filepath.Join(repoRoot, "product", "huntert")
	repoPython := filepath.Join(repoRoot, ".venv", "bin", "python3")
	relativeBundle := filepath.Join("runtime", "bundles", "default")
	expectedBundle := filepath.Join(productRoot, relativeBundle)

	for _, dir := range []string{
		filepath.Join(productRoot, "python", "huntert_runtime"),
		filepath.Dir(repoPython),
		expectedBundle,
	} {
		if err := os.MkdirAll(dir, 0o755); err != nil {
			t.Fatalf("mkdir %s: %v", dir, err)
		}
	}
	if err := os.WriteFile(filepath.Join(repoRoot, "AGENTS.md"), []byte("huntert"), 0o644); err != nil {
		t.Fatalf("write AGENTS.md: %v", err)
	}
	if err := os.WriteFile(filepath.Join(productRoot, "go.mod"), []byte("module huntert\n"), 0o644); err != nil {
		t.Fatalf("write go.mod: %v", err)
	}
	if err := os.WriteFile(repoPython, []byte("#!/usr/bin/env python3\n"), 0o755); err != nil {
		t.Fatalf("write repo python: %v", err)
	}
	writeBundleFixture(t, expectedBundle)

	wd, err := os.Getwd()
	if err != nil {
		t.Fatalf("getwd: %v", err)
	}
	t.Cleanup(func() { _ = os.Chdir(wd) })
	if err := os.Chdir(filepath.Join(repoRoot)); err != nil {
		t.Fatalf("chdir repo root: %v", err)
	}

	cfg := AttackRunConfig{
		Target:      "https://example.com",
		Timeout:     5 * time.Second,
		ModelBundle: relativeBundle,
	}
	if err := cfg.Normalize(); err != nil {
		t.Fatalf("Normalize() returned error: %v", err)
	}
	if cfg.ModelBundle != expectedBundle {
		t.Fatalf("expected relative bundle to resolve to %q, got %q", expectedBundle, cfg.ModelBundle)
	}
}

func TestNormalizeExtensions(t *testing.T) {
	values := normalizeExtensions([]string{"php, txt", ".php", "bak"})
	expected := []string{"bak", "php", "txt"}
	for idx, value := range expected {
		if values[idx] != value {
			t.Fatalf("expected %q at %d, got %q", value, idx, values[idx])
		}
	}
}

func TestVerifyModelSHA256(t *testing.T) {
	bundleDir := t.TempDir()
	writeBundleFixture(t, bundleDir)

	modelPath := filepath.Join(bundleDir, "model.pt")
	hash, err := FileSHA256(modelPath)
	if err != nil {
		t.Fatalf("FileSHA256(): %v", err)
	}

	manifest := BundleManifest{
		Files: BundleFiles{Model: "model.pt"},
		Model: BundleModel{SHA256: hash},
	}
	actual, err := VerifyModelSHA256(bundleDir, manifest)
	if err != nil {
		t.Fatalf("VerifyModelSHA256() returned error: %v", err)
	}
	if actual != hash {
		t.Fatalf("expected sha %q, got %q", hash, actual)
	}
}

func TestVerifyModelSHA256Mismatch(t *testing.T) {
	bundleDir := t.TempDir()
	writeBundleFixture(t, bundleDir)

	manifest := BundleManifest{
		Files: BundleFiles{Model: "model.pt"},
		Model: BundleModel{SHA256: "deadbeef"},
	}
	if _, err := VerifyModelSHA256(bundleDir, manifest); err == nil {
		t.Fatalf("VerifyModelSHA256() returned nil error for mismatched hash")
	}
}

func writeBundleFixture(t *testing.T, bundleDir string) {
	t.Helper()

	manifest := `{"id":"default","name":"HunterT Default","version":"0.2.0-dev","backend":"python-lstm","model":{"backend":"python-lstm","checkpoint":"model.pt","source_name":"model.pt","max_depth":10,"min_freq":5,"embedding_size":128,"num_layers":2,"dropout_rate":0.2,"vocab_size":10},"files":{"model":"model.pt","vocab":"vocab.json","wordlist":"wordlist.txt"},"defaults":{"prediction_limit":128,"max_depth":3,"method":"GET","user_agent":"HunterT/0.2.0-dev","statuses":[200]}}`
	if err := os.WriteFile(filepath.Join(bundleDir, "manifest.json"), []byte(manifest), 0o644); err != nil {
		t.Fatalf("write manifest: %v", err)
	}
	for _, name := range []string{"model.pt", "vocab.json", "wordlist.txt"} {
		if err := os.WriteFile(filepath.Join(bundleDir, name), []byte("x"), 0o644); err != nil {
			t.Fatalf("write bundle file %s: %v", name, err)
		}
	}
}
