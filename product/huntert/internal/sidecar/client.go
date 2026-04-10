package sidecar

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"os/exec"
	"strings"
	"sync"

	"huntert/internal/config"
)

type Config struct {
	ProductRoot string
	PythonBin   string
	RepoRoot    string
}

type Candidate struct {
	Token string  `json:"token"`
	Prob  float64 `json:"prob"`
}

type BundleInfo struct {
	BundleDir     string                `json:"bundle_dir"`
	Manifest      config.BundleManifest `json:"manifest"`
	VocabSize     int                   `json:"vocab_size"`
	WordlistCount int                   `json:"wordlist_count"`
}

type response struct {
	Ok         bool        `json:"ok"`
	Error      string      `json:"error,omitempty"`
	Bundle     *BundleInfo `json:"bundle,omitempty"`
	Candidates []Candidate `json:"candidates,omitempty"`
}

type Client struct {
	cmd      *exec.Cmd
	stdin    io.WriteCloser
	stdout   *bufio.Reader
	stderr   *bytes.Buffer
	mu       sync.Mutex
	shutdown bool
}

func Start(ctx context.Context, cfg Config) (*Client, error) {
	args := []string{"-m", "huntert_runtime", "serve"}
	cmd := exec.CommandContext(ctx, cfg.PythonBin, args...)
	cmd.Dir = cfg.ProductRoot
	cmd.Env = buildEnv(config.PythonModulePath(cfg.ProductRoot))

	stdin, err := cmd.StdinPipe()
	if err != nil {
		return nil, fmt.Errorf("create sidecar stdin: %w", err)
	}
	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return nil, fmt.Errorf("create sidecar stdout: %w", err)
	}
	stderr := &bytes.Buffer{}
	cmd.Stderr = stderr

	client := &Client{
		cmd:    cmd,
		stdin:  stdin,
		stdout: bufio.NewReader(stdout),
		stderr: stderr,
	}
	if err := cmd.Start(); err != nil {
		return nil, fmt.Errorf("start sidecar: %w", err)
	}
	return client, nil
}

func (c *Client) LoadBundle(bundlePath string) (*BundleInfo, error) {
	resp, err := c.call(map[string]any{
		"op":          "load_bundle",
		"bundle_path": bundlePath,
	})
	if err != nil {
		return nil, err
	}
	return resp.Bundle, nil
}

func (c *Client) InspectBundle() (*BundleInfo, error) {
	resp, err := c.call(map[string]any{"op": "inspect_bundle"})
	if err != nil {
		return nil, err
	}
	return resp.Bundle, nil
}

func (c *Client) PredictNext(tokens []string, topK int) ([]Candidate, error) {
	resp, err := c.call(map[string]any{
		"op":     "predict_next",
		"tokens": tokens,
		"top_k":  topK,
	})
	if err != nil {
		return nil, err
	}
	return resp.Candidates, nil
}

func (c *Client) Close() error {
	c.mu.Lock()
	if c.shutdown {
		c.mu.Unlock()
		return nil
	}
	c.shutdown = true
	c.mu.Unlock()

	_, _ = c.call(map[string]any{"op": "shutdown"})
	_ = c.stdin.Close()
	if err := c.cmd.Wait(); err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok && exitErr.ExitCode() == 0 {
			return nil
		}
		return fmt.Errorf("wait for sidecar: %w: %s", err, strings.TrimSpace(c.stderr.String()))
	}
	return nil
}

func (c *Client) call(payload map[string]any) (*response, error) {
	c.mu.Lock()
	defer c.mu.Unlock()

	encoded, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("encode sidecar payload: %w", err)
	}
	encoded = append(encoded, '\n')
	if _, err := c.stdin.Write(encoded); err != nil {
		return nil, fmt.Errorf("write sidecar payload: %w", err)
	}

	line, err := c.stdout.ReadBytes('\n')
	if err != nil {
		return nil, fmt.Errorf("read sidecar response: %w: %s", err, strings.TrimSpace(c.stderr.String()))
	}

	var resp response
	if err := json.Unmarshal(line, &resp); err != nil {
		return nil, fmt.Errorf("decode sidecar response: %w: %s", err, string(line))
	}
	if !resp.Ok {
		return nil, fmt.Errorf("sidecar error: %s", resp.Error)
	}
	return &resp, nil
}

func buildEnv(pythonPath string) []string {
	env := os.Environ()
	existing := os.Getenv("PYTHONPATH")
	merged := config.MergePythonPath(existing, pythonPath)

	result := make([]string, 0, len(env)+1)
	for _, entry := range env {
		if len(entry) >= len("PYTHONPATH=") && entry[:len("PYTHONPATH=")] == "PYTHONPATH=" {
			continue
		}
		result = append(result, entry)
	}
	result = append(result, "PYTHONPATH="+merged)
	return result
}
