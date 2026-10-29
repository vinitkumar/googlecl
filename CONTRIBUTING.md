# Contributing

Use exactly Go 1.27.3. The module minimum, CI, Makefile, and GoReleaser agree on
that version. GitHub Releases is the distribution channel; there is no PyPI
publishing workflow. Keep the alpha scoped to [supported commands](docs/compatibility.md).

## Architecture

`cmd/google` is the composition root: it supplies signal cancellation, connects
OAuth to the API adapter, and runs the CLI. Both executable names use this entry.

- `internal/cli`: Cobra arguments, config defaults, confirmations, text/JSON output.
- `internal/app`: workflows, selectors, dates, safe local file operations; calls
  the `Backend` interface, never the generated Google clients.
- `internal/googleapi`: Drive v3, Calendar v3, People API adapters, pagination,
  and bounded safe-read retries. Converts API responses into domain resources.
- `internal/model`: API-independent resource structs shared across boundaries.
- `internal/auth`: desktop OAuth, PKCE/state, cancellation, private token files,
  and refresh persistence. It does not own workflow logic.
- `internal/config`: read-only legacy INI lookup and platform config directories.

Keep service behavior behind the app/backend boundary. Keep SDK types inside the
adapter. CLI parsing and credential construction belong outside domain workflows.
Do not add a second implementation for the `googlecl` executable name.

## Tests and checks

```sh
make build
make test
make coverage
make verify
make snapshot
```

`make verify` checks formatting, tidy state, module checksums, vet, race/coverage,
and govulncheck. GoReleaser v2.13.3 is required for snapshots. Build outputs go to
`build/`, snapshots to `dist/`, and coverage to `coverage.out`. `make clean` removes
those generated artifacts. On Windows without Make, use the equivalent workflow
commands with `GOTOOLCHAIN=go1.27.3` and `.exe` output names.

For bugs, first write a regression, run it and observe the intended failure, then
fix it and observe the pass. Use table tests for pure rules and local HTTP servers
for API/CLI integration. Use temporary directories and isolate both config lookup
and token storage. Never copy credentials or tokens into tests, logs, issues, or
fixtures; synthetic values must be obvious test data. Tests must not call Google
or open a real browser. Loopback listeners require permission in some sandboxes.

Test errors as well as success: no mutation before validation/confirmation, no
partial-success result on pagination failure, no overwrite on download failure,
no repeated write on retry, and cancellation of OAuth/API work. Use the race
detector for concurrency; coverage is a gap-finding tool, not proof of correctness.
Live-account testing remains separate and mandatory before release.

## Change discipline

Read repository/global instructions and the working tree first. Preserve unrelated
edits and staged changes. Keep patches narrow, functions small, and comments short;
explain non-obvious safety decisions. Keep members private unless required.
Request approval before increasing a private member's visibility.

Commit subjects use imperative mood, start with a capital, have no final period,
and target 50 characters (72 maximum). Separate the body with a blank line; wrap
at 72 columns and explain what and why. Do not commit, push, tag, publish, or change
issues without the task's authorization. See [releasing](docs/releasing.md) for
artifact checks, live tests, and approval gates.

The old Python implementation remains in Git history and `revival-poc`.
`AUTHORS.rst` and `HISTORY.rst` preserve attribution and the historical release
record. Python cache directories may remain locally but are ignored.
