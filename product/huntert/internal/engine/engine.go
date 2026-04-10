package engine

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"huntert/internal/config"
	"huntert/internal/httpclient"
	"huntert/internal/queue"
	"huntert/internal/sidecar"
)

type Predictor interface {
	PredictNext(tokens []string, topK int) (sidecar.Prediction, error)
}

type Discovery struct {
	Path          string  `json:"path"`
	URL           string  `json:"url"`
	StatusCode    int     `json:"status_code"`
	DurationMS    int64   `json:"duration_ms"`
	ContentLength int64   `json:"content_length"`
	Depth         int     `json:"depth"`
	Source        string  `json:"source"`
	Score         float64 `json:"score"`
}

type Report struct {
	OK            bool        `json:"ok"`
	Command       string      `json:"command"`
	Target        string      `json:"target"`
	Bundle        string      `json:"bundle"`
	BundleID      string      `json:"bundle_id"`
	OutputDir     string      `json:"output_dir"`
	DryRun        bool        `json:"dry_run"`
	Backend       string      `json:"backend"`
	Engine        string      `json:"engine"`
	Requests      int         `json:"requests"`
	Interesting   int         `json:"interesting"`
	Errors        int         `json:"errors"`
	DurationMS    int64       `json:"duration_ms"`
	Notes         []string    `json:"notes,omitempty"`
	Discoveries   []Discovery `json:"discoveries,omitempty"`
	OOVTokens     []string    `json:"oov_tokens,omitempty"`
	Stderr        string      `json:"stderr,omitempty"`
	ResumeState   string      `json:"resume_state,omitempty"`
	RequestsFile  string      `json:"requests_file,omitempty"`
	FindingsFile  string      `json:"discoveries_file,omitempty"`
	OOVTokensFile string      `json:"oov_tokens_file,omitempty"`
	SummaryFile   string      `json:"summary_file,omitempty"`
}

type requestEvent struct {
	Candidate   queue.Candidate `json:"candidate"`
	Result      requestResult   `json:"result"`
	Interesting bool            `json:"interesting"`
	Error       string          `json:"error,omitempty"`
}

type requestResult struct {
	URL           string `json:"url"`
	StatusCode    int    `json:"status_code"`
	DurationMS    int64  `json:"duration_ms"`
	ContentLength int64  `json:"content_length"`
	Error         string `json:"error,omitempty"`
}

type runState struct {
	Target      string            `json:"target"`
	Bundle      string            `json:"bundle"`
	OutputDir   string            `json:"output_dir"`
	Attempted   []string          `json:"attempted"`
	Pending     []queue.Candidate `json:"pending"`
	Discoveries []Discovery       `json:"discoveries"`
	OOVTokens   []string          `json:"oov_tokens,omitempty"`
	UpdatedAt   string            `json:"updated_at"`
}

type oovEvent struct {
	Token      string   `json:"token"`
	Context    []string `json:"context"`
	ObservedAt string   `json:"observed_at"`
}

func Run(
	ctx context.Context,
	cfg config.AttackRunConfig,
	manifest config.BundleManifest,
	predictor Predictor,
) (*Report, error) {
	report := &Report{
		OK:        true,
		Command:   "attack run",
		Target:    cfg.Target,
		Bundle:    cfg.ModelBundle,
		BundleID:  manifest.ID,
		OutputDir: cfg.OutputDir,
		DryRun:    cfg.DryRun,
		Backend:   manifest.Backend,
		Engine:    "go-http",
	}

	wordlist, err := loadWordlist(manifest.WordlistPath(cfg.ModelBundle))
	if err != nil {
		return nil, err
	}
	report.Notes = append(report.Notes, fmt.Sprintf("loaded bundle %s", manifest.ID))
	report.Notes = append(report.Notes, fmt.Sprintf("loaded %d wordlist entries", len(wordlist)))

	if cfg.DryRun {
		rootPrediction, err := predictor.PredictNext([]string{"<sos>"}, min(cfg.PredictionLimit, 10))
		if err != nil {
			return nil, err
		}
		report.OOVTokens = rootPrediction.OOVTokens
		report.Notes = append(report.Notes, fmt.Sprintf("sidecar returned %d root candidates", len(rootPrediction.Candidates)))
		return report, nil
	}

	if err := os.MkdirAll(cfg.OutputDir, 0o755); err != nil {
		return nil, fmt.Errorf("create output dir: %w", err)
	}

	requestsPath := filepath.Join(cfg.OutputDir, "requests.jsonl")
	discoveriesPath := filepath.Join(cfg.OutputDir, "discoveries.jsonl")
	oovTokensPath := filepath.Join(cfg.OutputDir, "oov_tokens.jsonl")
	statePath := filepath.Join(cfg.OutputDir, "state.json")
	summaryPath := filepath.Join(cfg.OutputDir, "summary.json")
	report.ResumeState = statePath
	report.RequestsFile = requestsPath
	report.FindingsFile = discoveriesPath
	report.OOVTokensFile = oovTokensPath
	report.SummaryFile = summaryPath

	requestsFile, err := os.OpenFile(requestsPath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0o644)
	if err != nil {
		return nil, fmt.Errorf("open requests file: %w", err)
	}
	defer requestsFile.Close()

	discoveriesFile, err := os.OpenFile(discoveriesPath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0o644)
	if err != nil {
		return nil, fmt.Errorf("open discoveries file: %w", err)
	}
	defer discoveriesFile.Close()

	oovTokensFile, err := os.OpenFile(oovTokensPath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0o644)
	if err != nil {
		return nil, fmt.Errorf("open oov tokens file: %w", err)
	}
	defer oovTokensFile.Close()

	pq := queue.New()
	seen := map[string]struct{}{}
	attempted := []string{}
	seenOOVTokens := map[string]struct{}{}
	recordOOV := func(contextTokens []string, prediction sidecar.Prediction) error {
		return recordOOVTokens(oovTokensFile, report, seenOOVTokens, contextTokens, prediction.OOVTokens)
	}

	if cfg.Resume != "" {
		state, err := loadState(cfg.Resume)
		if err != nil {
			return nil, err
		}
		if err := validateResumeState(cfg, state); err != nil {
			return nil, err
		}
		for _, path := range state.Attempted {
			seen[path] = struct{}{}
			attempted = append(attempted, path)
		}
		for _, pending := range state.Pending {
			pendingCopy := pending
			queue.PushCandidate(pq, &pendingCopy)
			seen[pending.Path] = struct{}{}
		}
		report.Discoveries = append(report.Discoveries, state.Discoveries...)
		for _, token := range state.OOVTokens {
			if _, ok := seenOOVTokens[token]; ok {
				continue
			}
			seenOOVTokens[token] = struct{}{}
			report.OOVTokens = append(report.OOVTokens, token)
		}
		report.Notes = append(report.Notes, fmt.Sprintf("loaded resume state from %s", cfg.Resume))
	}

	if pq.Len() == 0 {
		if err := seedRootCandidates(pq, seen, predictor, cfg, wordlist, recordOOV); err != nil {
			return nil, err
		}
	}

	client, err := httpclient.New(cfg)
	if err != nil {
		return nil, err
	}

	type resultEnvelope struct {
		candidate *queue.Candidate
		result    requestResult
	}
	workCh := make(chan *queue.Candidate)
	resultCh := make(chan resultEnvelope)
	for idx := 0; idx < cfg.Threads; idx++ {
		go func() {
			for candidate := range workCh {
				response := client.Request(ctx, candidate.Path)
				result := requestResult{
					URL:           response.URL,
					StatusCode:    response.StatusCode,
					DurationMS:    response.DurationMS,
					ContentLength: response.ContentLength,
					Error:         response.Error,
				}
				resultCh <- resultEnvelope{
					candidate: candidate,
					result:    result,
				}
			}
		}()
	}

	started := time.Now()
	inFlight := 0
	cancelled := false
	limiter := newDispatchLimiter(cfg.RateLimit)

	for {
		for !cancelled && inFlight < cfg.Threads && pq.Len() > 0 {
			candidate := queue.PopCandidate(pq)
			if candidate == nil {
				break
			}
			if !limiter.Wait(ctx) {
				cancelled = true
				break
			}
			workCh <- candidate
			inFlight++
		}

		if inFlight == 0 {
			break
		}
		if ctx.Err() != nil {
			cancelled = true
		}

		event := <-resultCh
		inFlight--
		attempted = append(attempted, event.candidate.Path)
		report.Requests++

		interesting := isInteresting(event.result.StatusCode, cfg.StatusInclude, cfg.StatusExclude)
		request := requestEvent{
			Candidate:   *event.candidate,
			Result:      event.result,
			Interesting: interesting,
		}
		if event.result.Error != "" {
			report.Errors++
			request.Error = event.result.Error
		}
		if err := writeJSONLine(requestsFile, request); err != nil {
			return nil, err
		}

		if interesting {
			discovery := Discovery{
				Path:          event.candidate.Path,
				URL:           event.result.URL,
				StatusCode:    event.result.StatusCode,
				DurationMS:    event.result.DurationMS,
				ContentLength: event.result.ContentLength,
				Depth:         event.candidate.Depth,
				Source:        event.candidate.Source,
				Score:         event.candidate.Score,
			}
			report.Interesting++
			report.Discoveries = append(report.Discoveries, discovery)
			if err := writeJSONLine(discoveriesFile, discovery); err != nil {
				return nil, err
			}

			if !cancelled && shouldRecurse(*event.candidate, cfg) {
				if err := enqueueChildren(pq, seen, *event.candidate, predictor, cfg, wordlist, recordOOV); err != nil {
					return nil, err
				}
			}
		}
	}

	close(workCh)
	report.DurationMS = time.Since(started).Milliseconds()
	if cancelled {
		report.Notes = append(report.Notes, "run interrupted; pending queue saved for resume")
	}

	if err := saveState(statePath, runState{
		Target:      cfg.Target,
		Bundle:      cfg.ModelBundle,
		OutputDir:   cfg.OutputDir,
		Attempted:   attempted,
		Pending:     queue.Snapshot(pq),
		Discoveries: report.Discoveries,
		OOVTokens:   report.OOVTokens,
		UpdatedAt:   time.Now().UTC().Format(time.RFC3339),
	}); err != nil {
		return nil, err
	}
	if err := writeJSONFile(summaryPath, report); err != nil {
		return nil, err
	}

	return report, nil
}

type dispatchLimiter struct {
	interval time.Duration
	last     time.Time
}

func newDispatchLimiter(rateLimit float64) *dispatchLimiter {
	if rateLimit <= 0 {
		return nil
	}

	interval := time.Duration(float64(time.Second) / rateLimit)
	if interval <= 0 {
		interval = time.Nanosecond
	}
	return &dispatchLimiter{interval: interval}
}

func (limiter *dispatchLimiter) Wait(ctx context.Context) bool {
	if limiter == nil {
		return true
	}
	if limiter.last.IsZero() {
		limiter.last = time.Now()
		return true
	}

	waitFor := time.Until(limiter.last.Add(limiter.interval))
	if waitFor > 0 {
		timer := time.NewTimer(waitFor)
		defer timer.Stop()

		select {
		case <-ctx.Done():
			return false
		case <-timer.C:
		}
	}
	limiter.last = time.Now()
	return true
}

func seedRootCandidates(
	pq *queue.PriorityQueue,
	seen map[string]struct{},
	predictor Predictor,
	cfg config.AttackRunConfig,
	wordlist []string,
	recordOOV func([]string, sidecar.Prediction) error,
) error {
	contextTokens := []string{"<sos>"}
	prediction, err := predictor.PredictNext(contextTokens, cfg.PredictionLimit)
	if err != nil {
		return fmt.Errorf("predict root candidates: %w", err)
	}
	if recordOOV != nil {
		if err := recordOOV(contextTokens, prediction); err != nil {
			return err
		}
	}

	for _, candidate := range prediction.Candidates {
		enqueueCandidate(pq, seen, cfg, "", candidate.Token, candidate.Prob, "model")
	}
	for _, token := range wordlist {
		enqueueCandidate(pq, seen, cfg, "", token, 0.000001, "wordlist")
	}
	return nil
}

func enqueueChildren(
	pq *queue.PriorityQueue,
	seen map[string]struct{},
	parent queue.Candidate,
	predictor Predictor,
	cfg config.AttackRunConfig,
	wordlist []string,
	recordOOV func([]string, sidecar.Prediction) error,
) error {
	contextTokens := append([]string{"<sos>"}, parent.Tokens...)
	prediction, err := predictor.PredictNext(contextTokens, cfg.PredictionLimit)
	if err != nil {
		return fmt.Errorf("predict children for %s: %w", parent.Path, err)
	}
	if recordOOV != nil {
		if err := recordOOV(contextTokens, prediction); err != nil {
			return err
		}
	}

	for _, candidate := range prediction.Candidates {
		score := candidate.Prob
		if parent.Score > 0 {
			score = parent.Score * candidate.Prob
		}
		enqueueCandidate(pq, seen, cfg, parent.Path, candidate.Token, score, "model")
	}
	for _, token := range wordlist {
		score := 0.000001
		if parent.Score > 0 {
			score = parent.Score * score
		}
		enqueueCandidate(pq, seen, cfg, parent.Path, token, score, "wordlist")
	}
	return nil
}

func enqueueCandidate(
	pq *queue.PriorityQueue,
	seen map[string]struct{},
	cfg config.AttackRunConfig,
	parentPath string,
	token string,
	score float64,
	source string,
) {
	if len(seen) >= cfg.MaxRequests {
		return
	}

	for _, variant := range expandTokenVariants(token, cfg.Extensions) {
		path := joinPath(parentPath, variant)
		if path == "" {
			continue
		}
		if _, ok := seen[path]; ok {
			continue
		}
		candidate := &queue.Candidate{
			Path:   path,
			Tokens: strings.Split(path, "/"),
			Depth:  strings.Count(path, "/") + 1,
			Score:  score,
			Source: source,
		}
		seen[path] = struct{}{}
		queue.PushCandidate(pq, candidate)
		if len(seen) >= cfg.MaxRequests {
			return
		}
	}
}

func loadWordlist(path string) ([]string, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read wordlist: %w", err)
	}

	lines := strings.Split(string(data), "\n")
	result := make([]string, 0, len(lines))
	seen := map[string]struct{}{}
	for _, line := range lines {
		value := strings.TrimSpace(line)
		if value == "" {
			continue
		}
		if _, ok := seen[value]; ok {
			continue
		}
		seen[value] = struct{}{}
		result = append(result, value)
	}
	return result, nil
}

func loadState(path string) (*runState, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read state: %w", err)
	}
	var state runState
	if err := json.Unmarshal(data, &state); err != nil {
		return nil, fmt.Errorf("decode state: %w", err)
	}
	return &state, nil
}

func recordOOVTokens(
	file *os.File,
	report *Report,
	seen map[string]struct{},
	contextTokens []string,
	tokens []string,
) error {
	for _, token := range tokens {
		token = strings.TrimSpace(token)
		if token == "" {
			continue
		}
		if _, ok := seen[token]; ok {
			continue
		}
		seen[token] = struct{}{}
		report.OOVTokens = append(report.OOVTokens, token)
		if err := writeJSONLine(file, oovEvent{
			Token:      token,
			Context:    append([]string{}, contextTokens...),
			ObservedAt: time.Now().UTC().Format(time.RFC3339),
		}); err != nil {
			return err
		}
	}
	return nil
}

func validateResumeState(cfg config.AttackRunConfig, state *runState) error {
	if state == nil {
		return nil
	}
	if strings.TrimSpace(state.Target) != "" && state.Target != cfg.Target {
		return fmt.Errorf("resume state target %q does not match --target %q", state.Target, cfg.Target)
	}
	if strings.TrimSpace(state.Bundle) != "" && filepath.Clean(state.Bundle) != filepath.Clean(cfg.ModelBundle) {
		return fmt.Errorf("resume state bundle %q does not match --model-bundle %q", state.Bundle, cfg.ModelBundle)
	}
	return nil
}

func saveState(path string, state runState) error {
	return writeJSONFile(path, state)
}

func writeJSONFile(path string, value any) error {
	data, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal %s: %w", path, err)
	}
	data = append(data, '\n')
	if err := os.WriteFile(path, data, 0o644); err != nil {
		return fmt.Errorf("write %s: %w", path, err)
	}
	return nil
}

func writeJSONLine(file *os.File, value any) error {
	data, err := json.Marshal(value)
	if err != nil {
		return fmt.Errorf("marshal jsonl: %w", err)
	}
	data = append(data, '\n')
	if _, err := file.Write(data); err != nil {
		return fmt.Errorf("write jsonl: %w", err)
	}
	return nil
}

func isInteresting(status int, include, exclude []int) bool {
	if status == 0 {
		return false
	}
	if len(include) > 0 && !contains(include, status) {
		return false
	}
	if contains(exclude, status) {
		return false
	}
	return true
}

func shouldRecurse(candidate queue.Candidate, cfg config.AttackRunConfig) bool {
	if candidate.Depth >= cfg.MaxDepth {
		return false
	}
	last := candidate.Path
	if idx := strings.LastIndex(last, "/"); idx >= 0 {
		last = last[idx+1:]
	}
	return !strings.Contains(last, ".")
}

func expandTokenVariants(token string, extensions []string) []string {
	token = strings.TrimSpace(token)
	if token == "" || strings.HasPrefix(token, "<") {
		return nil
	}

	baseTokens := []string{token}
	if token == "YEAR" {
		currentYear := time.Now().Year()
		baseTokens = []string{
			strconv.Itoa(currentYear),
			strconv.Itoa(currentYear - 1),
			strconv.Itoa(currentYear - 2),
		}
	}

	seen := map[string]struct{}{}
	result := make([]string, 0, len(baseTokens)*(len(extensions)+1))
	for _, base := range baseTokens {
		if _, ok := seen[base]; !ok {
			seen[base] = struct{}{}
			result = append(result, base)
		}
		if strings.Contains(base, ".") {
			continue
		}
		for _, extension := range extensions {
			variant := base + "." + extension
			if _, ok := seen[variant]; ok {
				continue
			}
			seen[variant] = struct{}{}
			result = append(result, variant)
		}
	}
	return result
}

func joinPath(parent, child string) string {
	parent = strings.Trim(parent, "/")
	child = strings.Trim(child, "/")
	if parent == "" {
		return child
	}
	if child == "" {
		return parent
	}
	return parent + "/" + child
}

func contains(values []int, target int) bool {
	for _, value := range values {
		if value == target {
			return true
		}
	}
	return false
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
