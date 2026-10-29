# GoogleCL

A Go command-line client for Google services. This alpha keeps the historical
`google` command and supported legacy argument forms. Release archives also
contain an identical `googlecl` executable. No Python runtime is required.

**Alpha scope:** Docs/Drive list, upload, download/export, and trash; Calendar
list, today, add, and delete; Contacts list. This is **not yet a drop-in replacement
for every old GoogleCL workflow**. See [compatibility](docs/compatibility.md).

## Install

Download the archive for your OS and architecture from
[GitHub Releases](https://github.com/vinitkumar/googlecl/releases), when published.
Verify it against `checksums.txt`, extract it, and put `google` or `google.exe` on
`PATH`. Each archive includes `googlecl` as an alternative executable name.
Linux releases also include `.deb` and `.rpm` packages.

Before replacing an old installation, check which executable your shell uses:

```sh
command -v google     # Linux/macOS
# where.exe google    # Windows
```

The alpha is not published to PyPI. Homebrew, Scoop, and Winget publication are
follow-up work; do not install the historical Python package expecting this alpha.

### Build from source

**The module minimum is Go 1.27.3.** Use exactly Go 1.27.3 for builds,
tests, CI, and releases; `make` pins `GOTOOLCHAIN=go1.27.3`.

```sh
GOTOOLCHAIN=go1.27.3 go build -trimpath -o build/google ./cmd/google
./build/google --version
```

On Windows, use `-o build/google.exe`. Or install the primary command with:

```sh
GOTOOLCHAIN=go1.27.3 go install github.com/vinitkumar/googlecl/cmd/google@latest
```

The module installation command requires a published Go revision; until then,
build from this checkout. `make build` builds both executable names on Unix.

## Authenticate

Create your own Google **Desktop app** OAuth client, enable the required APIs,
and download its client JSON. See the [authentication guide](docs/authentication.md)
for consent-screen setup and troubleshooting. Old OAuth tokens cannot be reused.

```sh
google auth login --service docs --credentials client_secret.json
google auth login --service calendar --credentials client_secret.json
google auth login --service contacts --credentials client_secret.json
```

Credentials are stored separately for each service. A successful login remembers
the client configuration, so later commands do not need `--credentials`.
Use `--user alice@example.com` on login **and subsequent commands** to select a
named profile. The profile name is a label/login hint, not proof of the signed-in
account's identity.

## Legacy commands

```sh
google docs list
google docs list --title '^Report' --fields title,url-site
google docs upload report.docx --folder Reports
google docs upload photo.jpg --no-convert
google docs get 'Quarterly report' . --format pdf
google docs get --id FILE_ID --dest report.pdf --format pdf

google calendar today
google calendar list --date 2026-11-01,2026-11-07 --cal Work
google calendar add 'Lunch tomorrow at noon'
google calendar add 'Release day' --date 2026-11-15 --reminder 1d

google contacts list john
```

Titles are case-sensitive regular expressions by default, as in historical
GoogleCL. Use `--literal` or `[GENERAL] regex = false` for exact matching.
Folder and calendar titles must resolve unambiguously; immutable IDs are safer
for scripts. Use `--folder id:FILE_ID` or `--cal CALENDAR_ID`.

Listing commands retain headerless, delimiter-separated legacy rows. Calendar
text listings also retain the calendar heading. `--fields` and `--delimiter`
control text output; `--json` returns resource arrays without headings.
Progress and errors go to stderr, leaving stdout available for scripts.

```sh
google docs list --json
google contacts list --fields name,email --delimiter '|'
google calendar calendars --json
```

Deletion requires confirmation, or `--yes` for scripts:

```sh
google docs delete --id FILE_ID --yes       # moves to Drive trash
google calendar delete --id EVENT_ID --cal CALENDAR_ID --yes
```

Downloads never overwrite existing files. An interrupted transfer removes its
partial file. Bulk operations stop at the first error; earlier successful writes
are not rolled back.

## Configuration and help

```sh
google --help
google docs help
google help calendar
google auth status --service docs
google docs list --config /path/to/legacy/config
```

Existing INI settings are read without modification. Supported settings and known
migration differences are listed in [compatibility](docs/compatibility.md).

## Development and releases

```sh
make verify
make snapshot
```

Tests use local HTTP servers, not real Google credentials. Before publishing, run
the [live-account release checklist](docs/releasing.md). Snapshot builds produce
six archives for Linux/macOS/Windows on amd64/arm64, plus Linux packages.
An approved `v1.*` tag can create a **draft** GitHub release only after the full
OS/security/package checks and recorded live smoke evidence pass. Public release
publication remains a separate approval. See the release guide for environment setup.

See [contributing](CONTRIBUTING.md) for architecture and test conventions.
The previous Python implementation remains in Git history and the
[`revival-poc` branch](https://github.com/vinitkumar/googlecl/tree/revival-poc).

## License

Apache-2.0. See [LICENSE](LICENSE) and [AUTHORS.rst](AUTHORS.rst).
GoogleCL is an independent project, not an official Google product.
