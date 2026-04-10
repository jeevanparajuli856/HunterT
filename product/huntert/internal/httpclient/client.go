package httpclient

import (
	"context"
	"crypto/tls"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"time"

	"huntert/internal/config"
)

type Result struct {
	URL           string `json:"url"`
	StatusCode    int    `json:"status_code"`
	DurationMS    int64  `json:"duration_ms"`
	ContentLength int64  `json:"content_length"`
	Error         string `json:"error,omitempty"`
}

type Client struct {
	baseURL   *url.URL
	client    *http.Client
	method    string
	headers   http.Header
	userAgent string
	limiter   *limiter
}

func New(cfg config.AttackRunConfig) (*Client, error) {
	baseURL, err := url.Parse(cfg.Target)
	if err != nil {
		return nil, fmt.Errorf("parse target: %w", err)
	}

	transport := &http.Transport{
		TLSClientConfig: &tls.Config{InsecureSkipVerify: cfg.Insecure}, //nolint:gosec
	}
	client := &http.Client{
		Timeout:   cfg.Timeout,
		Transport: transport,
	}
	if !cfg.FollowRedirects {
		client.CheckRedirect = func(*http.Request, []*http.Request) error {
			return http.ErrUseLastResponse
		}
	}

	headers := make(http.Header)
	for _, rawHeader := range cfg.Headers {
		parts := strings.SplitN(rawHeader, ":", 2)
		if len(parts) != 2 {
			continue
		}
		headers.Add(strings.TrimSpace(parts[0]), strings.TrimSpace(parts[1]))
	}

	return &Client{
		baseURL:   baseURL,
		client:    client,
		method:    cfg.Method,
		headers:   headers,
		userAgent: cfg.UserAgent,
		limiter:   newLimiter(cfg.RateLimit),
	}, nil
}

func (client *Client) Request(ctx context.Context, relativePath string) Result {
	if err := client.limiter.Wait(ctx); err != nil {
		return Result{Error: err.Error()}
	}

	targetURL := client.resolveURL(relativePath)
	started := time.Now()

	req, err := http.NewRequestWithContext(ctx, client.method, targetURL, nil)
	if err != nil {
		return Result{URL: targetURL, Error: err.Error()}
	}
	for key, values := range client.headers {
		for _, value := range values {
			req.Header.Add(key, value)
		}
	}
	if client.userAgent != "" && req.Header.Get("User-Agent") == "" {
		req.Header.Set("User-Agent", client.userAgent)
	}

	resp, err := client.client.Do(req)
	if err != nil {
		return Result{
			URL:        targetURL,
			Error:      err.Error(),
			DurationMS: time.Since(started).Milliseconds(),
		}
	}
	defer resp.Body.Close()

	contentLength := resp.ContentLength
	if resp.Body != nil && client.method != "HEAD" {
		written, copyErr := io.Copy(io.Discard, io.LimitReader(resp.Body, 1<<20))
		if copyErr == nil && contentLength < 0 {
			contentLength = written
		}
	}

	return Result{
		URL:           targetURL,
		StatusCode:    resp.StatusCode,
		DurationMS:    time.Since(started).Milliseconds(),
		ContentLength: contentLength,
	}
}

func (client *Client) resolveURL(relativePath string) string {
	path := strings.TrimLeft(relativePath, "/")
	baseCopy := *client.baseURL
	basePath := strings.TrimRight(baseCopy.Path, "/")
	if basePath == "" {
		baseCopy.Path = "/" + path
	} else {
		baseCopy.Path = basePath + "/" + path
	}
	return baseCopy.String()
}

type limiter struct {
	interval time.Duration
	mu       sync.Mutex
	next     time.Time
}

func newLimiter(rate float64) *limiter {
	if rate <= 0 {
		return &limiter{}
	}
	return &limiter{interval: time.Duration(float64(time.Second) / rate)}
}

func (limiter *limiter) Wait(ctx context.Context) error {
	if limiter.interval <= 0 {
		return nil
	}

	limiter.mu.Lock()
	defer limiter.mu.Unlock()

	now := time.Now()
	if limiter.next.IsZero() || now.After(limiter.next) {
		limiter.next = now.Add(limiter.interval)
		return nil
	}

	timer := time.NewTimer(time.Until(limiter.next))
	defer timer.Stop()
	select {
	case <-ctx.Done():
		return ctx.Err()
	case <-timer.C:
		limiter.next = time.Now().Add(limiter.interval)
		return nil
	}
}
