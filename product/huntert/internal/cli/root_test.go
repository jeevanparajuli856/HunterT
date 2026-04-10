package cli

import (
	"os"
	"testing"
)

func TestHelpFlagsReturnSuccess(t *testing.T) {
	withCapturedStdoutAndStderr(t, func() {
		if code := runVersion([]string{"--help"}); code != 0 {
			t.Fatalf("runVersion(--help) returned %d, want 0", code)
		}
		if code := runAttack([]string{"--help"}); code != 0 {
			t.Fatalf("runAttack(--help) returned %d, want 0", code)
		}
		if code := runModelsInspect([]string{"--help"}); code != 0 {
			t.Fatalf("runModelsInspect(--help) returned %d, want 0", code)
		}
		if code := runBundleVerify([]string{"--help"}); code != 0 {
			t.Fatalf("runBundleVerify(--help) returned %d, want 0", code)
		}
	})
}

func withCapturedStdoutAndStderr(t *testing.T, fn func()) {
	t.Helper()

	originalStdout := os.Stdout
	originalStderr := os.Stderr

	stdoutFile, err := os.CreateTemp(t.TempDir(), "stdout")
	if err != nil {
		t.Fatalf("create stdout capture: %v", err)
	}
	stderrFile, err := os.CreateTemp(t.TempDir(), "stderr")
	if err != nil {
		t.Fatalf("create stderr capture: %v", err)
	}
	defer stdoutFile.Close()
	defer stderrFile.Close()

	os.Stdout = stdoutFile
	os.Stderr = stderrFile
	t.Cleanup(func() {
		os.Stdout = originalStdout
		os.Stderr = originalStderr
	})

	fn()
}
