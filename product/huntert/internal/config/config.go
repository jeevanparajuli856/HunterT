package config

import (
	"encoding/json"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"slices"
	"strconv"
	"strings"
	"time"
)

type OutputMode string

const (
	OutputText OutputMode = "text"
	OutputJSON OutputMode = "json"
)

var defaultStatuses = []int{200, 204, 301, 302, 307, 308, 401, 403}

type VersionInfo struct {
	Tool    string `json:"tool"`
	Version string `json:"version"`
	Backend string `json:"backend"`
	Bridge  string `json:"bridge"`
	Engine  string `json:"engine"`
}

type BundleManifest struct {
	ID      string                     `json:"id"`
	Name    string                     `json:"name"`
	Version string                     `json:"version"`
	Backend string                     `json:"backend"`
	Model   BundleModel                `json:"model"`
	Files   BundleFiles                `json:"files"`
	Default BundleDefaults             `json:"defaults"`
	Raw     map[string]any             `json:"-"`
	Extra   map[string]json.RawMessage `json:"-"`
}

type BundleModel struct {
	Backend     string  `json:"backend"`
	Checkpoint  string  `json:"checkpoint"`
	SourceName  string  `json:"source_name"`
	MaxDepth    int     `json:"max_depth"`
	MinFreq     int     `json:"min_freq"`
	Embedding   int     `json:"embedding_size"`
	NumLayers   int     `json:"num_layers"`
	DropoutRate float64 `json:"dropout_rate"`
	VocabSize   int     `json:"vocab_size"`
}

type BundleFiles struct {
	Model    string `json:"model"`
	Vocab    string `json:"vocab"`
	Wordlist string `json:"wordlist"`
}

type BundleDefaults struct {
	PredictionLimit int    `json:"prediction_limit"`
	MaxDepth        int    `json:"max_depth"`
	Method          string `json:"method"`
	UserAgent       string `json:"user_agent"`
	Statuses        []int  `json:"statuses"`
}

type BundleInfo struct {
	ID            string         `json:"id"`
	BundleDir     string         `json:"bundle_dir"`
	Manifest      BundleManifest `json:"manifest"`
	VocabSize     int            `json:"vocab_size"`
	WordlistCount int            `json:"wordlist_count"`
}

type BundleCommandConfig struct {
	ModelBundle string
	PythonBin   string
	Output      OutputMode
	RepoRoot    string
	ProductRoot string
}

type AttackRunConfig struct {
	Target          string
	Threads         int
	Timeout         time.Duration
	RateLimit       float64
	Headers         []string
	UserAgent       string
	Method          string
	FollowRedirects bool
	Insecure        bool
	Extensions      []string
	MaxDepth        int
	PredictionLimit int
	MaxRequests     int
	StatusInclude   []int
	StatusExclude   []int
	OutputDir       string
	Output          OutputMode
	Resume          string
	DryRun          bool
	ModelBundle     string
	PythonBin       string
	RepoRoot        string
	ProductRoot     string
}

func ParseOutputMode(value string) (OutputMode, error) {
	mode := OutputMode(strings.ToLower(strings.TrimSpace(value)))
	switch mode {
	case OutputText, OutputJSON:
		return mode, nil
	default:
		return "", fmt.Errorf("unsupported output mode %q", value)
	}
}

func ParseCSVList(value string) []string {
	if strings.TrimSpace(value) == "" {
		return nil
	}

	raw := strings.Split(value, ",")
	parts := make([]string, 0, len(raw))
	for _, item := range raw {
		item = strings.TrimSpace(item)
		if item == "" {
			continue
		}
		parts = append(parts, item)
	}
	return parts
}

func ParseStatusList(value string) ([]int, error) {
	if strings.TrimSpace(value) == "" {
		return nil, nil
	}

	parts := ParseCSVList(value)
	statuses := make([]int, 0, len(parts))
	for _, part := range parts {
		status, err := strconv.Atoi(part)
		if err != nil {
			return nil, fmt.Errorf("parse status %q: %w", part, err)
		}
		statuses = append(statuses, status)
	}
	return statuses, nil
}

func (cfg *BundleCommandConfig) Normalize() error {
	cfg.applyDefaults()

	repoRoot, err := ResolveRepoRoot()
	if err != nil {
		return err
	}
	productRoot, err := ResolveProductRoot(repoRoot)
	if err != nil {
		return err
	}

	cfg.RepoRoot = repoRoot
	cfg.ProductRoot = productRoot
	cfg.PythonBin = preferRepoPython(repoRoot, cfg.PythonBin)
	cfg.ModelBundle = resolveBundlePath(cfg.ModelBundle, productRoot)

	if cfg.ModelBundle, err = filepath.Abs(cfg.ModelBundle); err != nil {
		return fmt.Errorf("resolve bundle path: %w", err)
	}
	return nil
}

func (cfg *BundleCommandConfig) Validate() error {
	cfg.applyDefaults()

	mode, err := ParseOutputMode(string(cfg.Output))
	if err != nil {
		return err
	}
	cfg.Output = mode

	if strings.TrimSpace(cfg.ModelBundle) == "" {
		return fmt.Errorf("--bundle is required")
	}
	if _, err := LoadBundleManifest(cfg.ModelBundle); err != nil {
		return err
	}
	return nil
}

func (cfg *BundleCommandConfig) applyDefaults() {
	if cfg.PythonBin == "" {
		cfg.PythonBin = "python3"
	}
	if cfg.Output == "" {
		cfg.Output = OutputText
	}
}

func (cfg *AttackRunConfig) Normalize() error {
	cfg.applyDefaults()

	repoRoot, err := ResolveRepoRoot()
	if err != nil {
		return err
	}
	productRoot, err := ResolveProductRoot(repoRoot)
	if err != nil {
		return err
	}

	cfg.RepoRoot = repoRoot
	cfg.ProductRoot = productRoot
	cfg.PythonBin = preferRepoPython(repoRoot, cfg.PythonBin)
	cfg.ModelBundle = resolveBundlePath(cfg.ModelBundle, productRoot)
	if cfg.ModelBundle, err = filepath.Abs(cfg.ModelBundle); err != nil {
		return fmt.Errorf("resolve bundle path: %w", err)
	}

	if cfg.Resume != "" {
		if cfg.Resume, err = filepath.Abs(cfg.Resume); err != nil {
			return fmt.Errorf("resolve resume path: %w", err)
		}
	}

	if strings.TrimSpace(cfg.OutputDir) == "" {
		if cfg.Resume != "" {
			cfg.OutputDir = filepath.Dir(cfg.Resume)
		} else {
			cfg.OutputDir = filepath.Join(productRoot, "runtime", "output")
		}
	}
	if cfg.OutputDir, err = filepath.Abs(cfg.OutputDir); err != nil {
		return fmt.Errorf("resolve output dir: %w", err)
	}

	cfg.Method = strings.ToUpper(strings.TrimSpace(cfg.Method))
	cfg.Extensions = normalizeExtensions(cfg.Extensions)
	cfg.StatusInclude = normalizeStatuses(cfg.StatusInclude)
	cfg.StatusExclude = normalizeStatuses(cfg.StatusExclude)

	mode, err := ParseOutputMode(string(cfg.Output))
	if err != nil {
		return err
	}
	cfg.Output = mode
	return nil
}

func (cfg *AttackRunConfig) Validate() error {
	cfg.applyDefaults()

	if strings.TrimSpace(cfg.Target) == "" {
		return fmt.Errorf("--target is required")
	}
	if _, err := url.ParseRequestURI(cfg.Target); err != nil {
		return fmt.Errorf("target must be a valid URL: %w", err)
	}
	if cfg.Threads <= 0 {
		return fmt.Errorf("--threads must be greater than zero")
	}
	if cfg.Timeout <= 0 {
		return fmt.Errorf("--timeout must be greater than zero")
	}
	if cfg.MaxDepth <= 0 {
		return fmt.Errorf("--max-depth must be greater than zero")
	}
	if cfg.PredictionLimit <= 0 {
		return fmt.Errorf("--prediction-limit must be greater than zero")
	}
	if cfg.MaxRequests <= 0 {
		return fmt.Errorf("--max-requests must be greater than zero")
	}
	if cfg.RateLimit < 0 {
		return fmt.Errorf("--rate-limit cannot be negative")
	}
	if cfg.Method != "GET" && cfg.Method != "HEAD" {
		return fmt.Errorf("--method must be GET or HEAD")
	}
	if _, err := LoadBundleManifest(cfg.ModelBundle); err != nil {
		return err
	}
	return nil
}

func (cfg *AttackRunConfig) applyDefaults() {
	if cfg.Threads == 0 {
		cfg.Threads = 20
	}
	if cfg.Timeout == 0 {
		cfg.Timeout = 10 * time.Second
	}
	if cfg.UserAgent == "" {
		cfg.UserAgent = "HunterT/0.2.0-dev"
	}
	if cfg.Method == "" {
		cfg.Method = "GET"
	}
	if cfg.MaxDepth == 0 {
		cfg.MaxDepth = 3
	}
	if cfg.PredictionLimit == 0 {
		cfg.PredictionLimit = 128
	}
	if cfg.MaxRequests == 0 {
		cfg.MaxRequests = 1000
	}
	if cfg.Output == "" {
		cfg.Output = OutputText
	}
	if cfg.PythonBin == "" {
		cfg.PythonBin = "python3"
	}
	if len(cfg.StatusInclude) == 0 {
		cfg.StatusInclude = append([]int{}, defaultStatuses...)
	}
}

func ResolveRepoRoot() (string, error) {
	if root := strings.TrimSpace(os.Getenv("HUNTERT_REPO_ROOT")); root != "" {
		return filepath.Abs(root)
	}

	if cwd, err := os.Getwd(); err == nil {
		if root, ok := findRepoRoot(cwd); ok {
			return root, nil
		}
	}
	if exe, err := os.Executable(); err == nil {
		if root, ok := findRepoRoot(filepath.Dir(exe)); ok {
			return root, nil
		}
	}
	return "", fmt.Errorf("could not locate repo root; set HUNTERT_REPO_ROOT")
}

func ResolveProductRoot(repoRoot string) (string, error) {
	if root := strings.TrimSpace(os.Getenv("HUNTERT_PRODUCT_ROOT")); root != "" {
		return filepath.Abs(root)
	}

	productRoot := filepath.Join(repoRoot, "product", "huntert")
	if _, err := os.Stat(filepath.Join(productRoot, "go.mod")); err != nil {
		return "", fmt.Errorf("product root not found at %s", productRoot)
	}
	return productRoot, nil
}

func PythonModulePath(productRoot string) string {
	return filepath.Join(productRoot, "python")
}

func MergePythonPath(existing, modulePath string) string {
	if strings.TrimSpace(existing) == "" {
		return modulePath
	}
	return modulePath + string(os.PathListSeparator) + existing
}

func LoadBundleManifest(bundleDir string) (BundleManifest, error) {
	manifestPath := bundleDir
	if info, err := os.Stat(bundleDir); err == nil && info.IsDir() {
		manifestPath = filepath.Join(bundleDir, "manifest.json")
		bundleDir = filepath.Dir(manifestPath)
	} else if err == nil {
		bundleDir = filepath.Dir(bundleDir)
	}
	data, err := os.ReadFile(manifestPath)
	if err != nil {
		return BundleManifest{}, fmt.Errorf("read bundle manifest: %w", err)
	}

	var manifest BundleManifest
	if err := json.Unmarshal(data, &manifest); err != nil {
		return BundleManifest{}, fmt.Errorf("decode bundle manifest: %w", err)
	}
	if manifest.ID == "" {
		return BundleManifest{}, fmt.Errorf("bundle manifest missing id")
	}

	for _, relPath := range []string{manifest.Files.Model, manifest.Files.Vocab, manifest.Files.Wordlist} {
		if strings.TrimSpace(relPath) == "" {
			return BundleManifest{}, fmt.Errorf("bundle manifest contains an empty file path")
		}
		if _, err := os.Stat(filepath.Join(bundleDir, relPath)); err != nil {
			return BundleManifest{}, fmt.Errorf("bundle file missing: %s", filepath.Join(bundleDir, relPath))
		}
	}
	return manifest, nil
}

func VerifyBundle(bundlePath string) (*BundleManifest, string, error) {
	resolved := bundlePath
	if info, err := os.Stat(bundlePath); err == nil && !info.IsDir() {
		resolved = filepath.Dir(bundlePath)
	}
	manifest, err := LoadBundleManifest(bundlePath)
	if err != nil {
		return nil, "", err
	}
	absResolved, err := filepath.Abs(resolved)
	if err != nil {
		return nil, "", fmt.Errorf("resolve bundle path: %w", err)
	}
	return &manifest, absResolved, nil
}

func (manifest BundleManifest) WordlistPath(bundleDir string) string {
	return filepath.Join(bundleDir, manifest.Files.Wordlist)
}

func preferRepoPython(repoRoot, current string) string {
	if strings.TrimSpace(current) != "python3" {
		return current
	}

	candidate := filepath.Join(repoRoot, ".venv", "bin", "python3")
	if _, err := os.Stat(candidate); err == nil {
		return candidate
	}
	return current
}

func resolveBundlePath(value, productRoot string) string {
	if strings.TrimSpace(value) != "" {
		return value
	}
	return filepath.Join(productRoot, "runtime", "bundles", "default")
}

func findRepoRoot(start string) (string, bool) {
	current, err := filepath.Abs(start)
	if err != nil {
		return "", false
	}

	for {
		if fileExists(filepath.Join(current, "AGENTS.md")) && fileExists(filepath.Join(current, "product", "huntert", "go.mod")) {
			return current, true
		}
		parent := filepath.Dir(current)
		if parent == current {
			return "", false
		}
		current = parent
	}
}

func fileExists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}

func normalizeExtensions(values []string) []string {
	var out []string
	seen := map[string]struct{}{}
	for _, value := range values {
		for _, part := range strings.Split(value, ",") {
			part = strings.TrimSpace(strings.ToLower(part))
			if part == "" {
				continue
			}
			if !strings.HasPrefix(part, ".") {
				part = "." + strings.TrimPrefix(part, ".")
			}
			if _, ok := seen[part]; ok {
				continue
			}
			seen[part] = struct{}{}
			out = append(out, part)
		}
	}
	slices.Sort(out)
	return out
}

func normalizeStatuses(values []int) []int {
	if len(values) == 0 {
		return nil
	}

	seen := map[int]struct{}{}
	out := make([]int, 0, len(values))
	for _, value := range values {
		if value < 100 || value > 599 {
			continue
		}
		if _, ok := seen[value]; ok {
			continue
		}
		seen[value] = struct{}{}
		out = append(out, value)
	}
	slices.Sort(out)
	return out
}
