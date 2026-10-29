# Releasing the Go alpha

Current development version: `1.0.0-alpha.1-dev`. GitHub Releases is primary.
Do not call an alpha release-ready until every gate below has recorded evidence
for its exact commit. Automated fixtures do not replace live-account validation.
Never push, tag, create/publish a release, or change issues without approval.

## Local and hosted gates

1. Use exactly Go 1.27.3 and GoReleaser v2.13.3. Confirm `go version` under
   `GOTOOLCHAIN=go1.27.3` and `goreleaser --version`.
2. Run `make tidy`, `make verify`, and `make build`. Inspect the tidy diff.
   Record race, vet, coverage, module verification, and govulncheck output.
   Reachable vulnerabilities block release. Review non-reachable findings and
   record their applicability; a clean reachable scan is not a clean dependency scan.
3. Run `goreleaser check` and `make snapshot`. Snapshots accept dirty trees and
   never publish; release builds must use a clean, approved, committed tree.
4. Run `bash scripts/verify-artifacts.sh dist`. Verify all six archives contain
   both names and documentation, all checksums match, and both binaries have
   identical bytes. Inspect both architectures' deb/rpm contents and metadata.
5. Test native execution for **Linux, macOS, and Windows, amd64 and arm64**.
   Check version/help, paths with spaces and Unicode, missing credentials, private
   storage, cancellation, download overwrite refusal, and both executable names.
   Cross-compilation proves none of these runtime behaviors. Install/uninstall
   deb/rpm in disposable matching Linux systems and inspect installed paths.
   macOS binaries are currently unsigned/unnotarized; Windows binaries unsigned.
   Qualify the resulting download/OS trust prompts before public distribution.
6. Require passing hosted `Go` workflow jobs: Ubuntu/macOS/Windows race tests,
   coverage, vet, formatting, module integrity, both-name smoke tests, security,
   and snapshot packaging. Runner architecture coverage is not all six targets;
   retain the separate native qualification in step 5.
7. Complete the live-account checklist below and record results without secrets.

## Live-account checklist

Use a dedicated test account, disposable Drive folder and Calendar, plus a second
account/profile. Restrict test mutations to their created resource IDs. Keep OAuth
client JSON outside the checkout. Set `GOOGLECL_CONFIG_DIR` to a private temporary
location outside Git. Use a unique test title, e.g. `GoogleCL alpha smoke DATE`.
Record OS, architecture, binary version/commit, command, outcome, and cleanup.
Do not capture authorization URLs, tokens, client secrets, or private contact data.

| Check | Procedure and pass condition |
| --- | --- |
| Login | For docs/calendar/contacts, log in with `--user alpha-a --credentials /private/path/client.json`. Confirm consent scopes, callback, and `auth status` using the same service/profile. Subsequent commands work without `--credentials`. |
| Cancellation | Cancel consent, use Ctrl-C while waiting, and exercise timeout. Confirm a nonzero exit, listener shutdown, and no newly saved token. Try `--no-browser` with the loopback browser on the same machine. |
| Refresh | Wait for the access token to expire, then list resources without login. Confirm successful refresh and persistence by running a second process. Do not edit/copy tokens into fixtures. Test revoked grants produce an actionable login error. |
| Profiles | Log in as `alpha-b` with the second account for each service. Confirm each lists its own resources and logout of alpha-a does not affect alpha-b or other services. Repeat with INI `[docs] user` and explicit `--user` overrides. Profile labels are not verified account identities. |
| Drive upload | Upload a disposable txt/docx with conversion and a binary using `--no-convert` into the test folder. Check content, title, parent, and MIME type. Record returned IDs. |
| Drive list | List by ID, folder, regex/literal title, legacy fields/delimiter, and JSON. Create enough test resources or use a prepared account to exercise real pagination. |
| Drive export | Export the native document as txt and pdf; inspect content. Check sheets xlsx and slides pptx with prepared disposable native files. Verify legacy xls/ppt export fails explicitly. |
| Drive download | Download the unchanged binary and compare bytes. Repeat to the same filename: it must fail without altering it. Interrupt/fail a transfer and confirm partial cleanup on handled cancellation. |
| Drive trash | Refuse the confirmation once; confirm the file remains. Then delete only the created ID with `--yes` and verify in Drive trash. Restore or permanently clean up through the account UI if appropriate. |
| Calendar add | In the disposable Calendar, add natural-language, explicit all-day, and RFC3339 timed events. Check timezone, exclusive all-day end, and zero/minute/day reminders in the UI. |
| Calendar list | Test list/today/date range/query, calendar selection, text heading, JSON, DST boundaries, and a recurring event's instances. Compare with the calendar UI in the documented local timezone. |
| Calendar delete | Refuse confirmation, then delete a created event ID with `--yes`. Delete a recurrence instance and verify siblings remain. Never use a master series ID unless deleting the series is intended. |
| Contacts | Prepare synthetic saved contacts in the test account. List name/email/phone, multiple values, missing values, name regex/literal, JSON and pagination. Directory/other contacts and groups are out of scope. |
| Logout/cleanup | Remove local tokens with auth logout for each service/profile; verify status. Logout does not revoke grants or remove saved client configuration. Revoke test grants and securely remove the private test config directory when finished. |

Run the service smoke suite on each supported OS; qualify each of the six native
architectures. Include Windows inherited ACL inspection and Unix file permissions.
Do not run concurrent refreshes of one profile/service: locking is not implemented.
If a bulk command fails, inspect earlier successful writes before retrying.

## Release workflow and approvals

`go.yml` supports `workflow_call`. On an approved `v1.*` tag, `release.yml` calls
that complete workflow and requires success before its release job can run.
The release job targets the GitHub environment `release`. Before enabling it:

- Configure required reviewers for that environment and restrict permitted tags.
- After all live/native gates pass for a commit, have a maintainer record the
  evidence and set environment variable `ALPHA_SMOKE_SHA` to that full commit SHA.
  The job refuses draft creation if the variable is missing or differs from the
  tagged commit. It is a maintainer attestation, not automated live testing.
- Require explicit approval for pushing the commit/tag and for draft creation.
  Environment protection must be configured in GitHub; YAML alone cannot install
  required reviewers. No repository settings are changed by local verification.

After approval, use a prerelease tag such as `v1.0.0-alpha.1`. GoReleaser creates a
**draft prerelease** with archives, Linux packages, and `checksums.txt`; the workflow
also generates build provenance attestations. Review actual uploaded assets,
checksums, version strings, compatibility notes, unsigned-binary limitations, and
live evidence before separately approving public publication. Never imply that a
queued workflow or a local snapshot proves the tagged workflow passed.

If any gate fails, leave the draft unpublished. Rebuild/retest from a new approved
commit/tag as needed; do not silently replace evidence from another revision.
No PyPI, Homebrew, Scoop, or Winget publishing is part of this alpha.
