GO ?= /usr/local/go/bin/go
BINARY_DIR ?= bin
BINARY_NAME ?= HunterT

.PHONY: build test install run verify

build:
	mkdir -p $(BINARY_DIR)
	$(GO) build -o $(BINARY_DIR)/$(BINARY_NAME) ./cmd/huntert

test:
	$(GO) test ./...

install:
	bash ./install.sh

run:
	$(GO) run ./cmd/huntert

verify:
	$(BINARY_DIR)/$(BINARY_NAME) bundle verify --model-bundle runtime/bundles/default
