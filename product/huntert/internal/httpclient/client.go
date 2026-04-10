package httpclient

import (
	"context"
	"crypto/tls"
	"fmt"
	"net/http"
	"net/url"
	"path"
	"strings"
	"time"

	"huntert/internal/config"
)

type Result struct {
	URL           string `json:"url"`
	StatusCode    int    `json:"status_code"`
	ContentLength int64  `json:"content_length"`
	DurationMS    int64  `json:"duration_ms"`
	Error         string `json:"error,omitempty"`
}

type Client struct {
	base   *url.URL
	method string
	http   *http.Client
	header http.Header
}

func New(cfg config.AttackRunConfig) (*Client, error) {
	base, err := url.Parse(cfg.Target)
	if err != nil {
		return nil, fmt.Errorf("parse target URL: %w", err)
	}

	transport := http.DefaultTransport.(*http.Transport).Clone()
	transport.TLSClientConfig = &tls.Config{InsecureSkipVerify: cfg.Insecure} //nolint:gosec

	client := &http.Client{
		Timeout:   cfg.Timeout,
		Transport: transport,
	}
	if !cfg.FollowRedirects {
		client.CheckRedirect = func(_ *http.Request, _ []*http.Request) error {
			return http.ErrUseLastResponse
		}
	}

	header := make(http.Header)
	for _, item := range cfg.Headers {
		key, value, ok := strings.Cut(item, ":")
		if !ok {
			continue
		}
		header.Add(strings.TrimSpace(key), strings.TrimSpace(value))
	}
	if strings.TrimSpace(cfg.UserAgent) != "" {
		header.Set("User-Agent", cfg.UserAgent)
	}

	return &Client{
		base:   base,
		method: cfg.Method,
		http:   client,
		header: header,
	}, nil
}

func (c *Client) Request(ctx context.Context, relativePath string) Result {
	targetURL := buildURL(c.base, relativePath)
	req, err := http.NewRequestWithContext(ctx, c.method, targetURL, nil)
	if err != nil {
		return Result{URL: targetURL, Error: err.Error()}
	}
	req.Header = c.header.Clone()

	started := time.Now()
	resp, err := c.http.Do(req)
	if err != nil {
		return Result{URL: targetURL, Error: err.Error(), DurationMS: time.Since(started).Milliseconds()}
	}
	defer resp.Body.Close()

	return Result{
		URL:           targetURL,
		StatusCode:    resp.StatusCode,
		ContentLength: resp.ContentLength,
		DurationMS:    time.Since(started).Milliseconds(),
	}
}

func buildURL(base *url.URL, relativePath string) string {
	cloned := *base
	basePath := cloned.Path
	if basePath == "" {
		basePath = "/"
	}

	if relativePath == "" {
		cloned.Path = basePath
		return cloned.String()
	}

	relativePath = strings.TrimLeft(relativePath, "/")
	if basePath == "/" {
		cloned.Path = "/" + relativePath
		return cloned.String()
	}

	cloned.Path = path.Join(basePath, relativePath)
	if !strings.HasPrefix(cloned.Path, "/") {
		cloned.Path = "/" + cloned.Path
	}
	return cloned.String()
}
