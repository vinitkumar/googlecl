GO_VERSION := 1.27.3
export GOTOOLCHAIN := go$(GO_VERSION)
GO ?= go
GORELEASER ?= goreleaser
GOFMT = "$(shell $(GO) env GOROOT)/bin/gofmt"
EXE := $(if $(filter Windows_NT,$(OS)),.exe,)
.DEFAULT_GOAL := help
.PHONY: help toolchain build fmt tidy test race coverage vet security verify snapshot clean

help:
	@echo 'Targets: build fmt tidy test race coverage vet security verify snapshot clean'

toolchain:
	@test "$$($(GO) env GOVERSION)" = 'go$(GO_VERSION)' || (echo 'Go $(GO_VERSION) is required'; exit 1)

build: toolchain
	$(GO) build -trimpath -o build/google$(EXE) ./cmd/google
	cp build/google$(EXE) build/googlecl$(EXE)

fmt: toolchain
	$(GOFMT) -w cmd internal

tidy: toolchain
	$(GO) mod tidy
	$(GO) mod verify

test: toolchain
	$(GO) test ./...

race: toolchain
	$(GO) test -race ./...

coverage: toolchain
	$(GO) test -race -coverpkg=./internal/... -coverprofile=coverage.out ./...
	$(GO) tool cover -func=coverage.out

vet: toolchain
	$(GO) vet ./...

security: toolchain
	$(GO) run golang.org/x/vuln/cmd/govulncheck@latest ./...

verify: toolchain
	@test -z "$$( $(GOFMT) -l cmd internal)"
	$(GO) mod tidy -diff
	$(GO) mod verify
	$(GO) vet ./...
	$(GO) test -race -coverpkg=./internal/... -coverprofile=coverage.out ./...
	$(GO) run golang.org/x/vuln/cmd/govulncheck@latest ./...

snapshot: toolchain
	$(GORELEASER) check
	$(GORELEASER) release --snapshot --clean

clean:
	rm -rf build dist
	rm -f coverage.out coverage.html
