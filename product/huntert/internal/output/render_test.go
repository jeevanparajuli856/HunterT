package output

import (
	"bytes"
	"testing"

	"huntert/internal/config"
	"huntert/internal/engine"
)

func TestRenderAttackReportFindingsOnly(t *testing.T) {
	report := engine.Report{
		Discoveries: []engine.Discovery{
			{URL: "https://example.com/admin", StatusCode: 200},
			{URL: "https://example.com/login", StatusCode: 403},
		},
	}

	var buffer bytes.Buffer
	if err := RenderAttackReport(&buffer, config.OutputText, report, true); err != nil {
		t.Fatalf("RenderAttackReport() returned error: %v", err)
	}

	expected := "https://example.com/admin 200\nhttps://example.com/login 403\n"
	if buffer.String() != expected {
		t.Fatalf("expected findings-only output %q, got %q", expected, buffer.String())
	}
}
