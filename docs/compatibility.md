# Alpha compatibility

Version `1.0.0-alpha.1-dev` preserves a bounded subset of historical GoogleCL
syntax and text output. It is not a seamless replacement for the Python release.
`google` and `googlecl` run the same program; help still calls it `google`.

## Commands and flags

All implemented leaf commands accept `--user/-u`, `--config`, and `--help`.
API commands and `auth login` accept `--credentials`. Flags may precede the
service or follow the command. Unknown or inapplicable explicit flags fail.
`--quiet` applies to commands with progress messages, not list/status commands.
`--yes` applies only to delete commands. With `--json`, explicit `--fields` and
`--delimiter` are rejected because they cannot change JSON output.

| Command | Positional form | Additional supported flags |
| --- | --- | --- |
| `docs list` | `[TITLE]` | `--title/-n`, `--folder/-f`, `--id`, `--literal`, `--fields`, `--delimiter`, `--json` |
| `docs get` | `[TITLE] [DEST]` | `--title/-n`, `--folder/-f`, `--id`, `--literal`, `--dest`, `--format`, `--quiet` |
| `docs upload` | `[FILE...]` | `--src`, `--title/-n`, `--folder/-f`, `--format`, `--no-convert`, `--json`, `--quiet` |
| `docs delete` | `[TITLE]` | `--title/-n`, `--folder/-f`, `--id`, `--literal`, `--yes`, `--quiet` |
| `calendar list` | `[TITLE]` | `--title/-n`, `--query/-q`, `--date/-d`, `--cal`, `--literal`, `--fields`, `--delimiter`, `--json` |
| `calendar today` | `[TITLE]` | Same as list except `--date` |
| `calendar add` | `[EVENT...]` | `--src`, `--date/-d`, `--cal`, `--reminder`, `--json`, `--quiet` |
| `calendar delete` | `[TITLE]` | `--title/-n`, `--query/-q`, `--date/-d`, `--cal`, `--id`, `--literal`, `--yes`, `--quiet` |
| `calendar calendars` | None | `--delimiter`, `--json` |
| `contacts list` | `[NAME]` | `--title/-n`, `--literal`, `--fields`, `--delimiter`, `--json` |
| `auth login` | None | `--service` (default `docs`), `--credentials`, `--no-browser`, `--quiet` |
| `auth status` | None | `--service` |
| `auth logout` | None | `--service`, `--quiet` |

`google --version`, `google SERVICE help`, and `google help SERVICE` work offline.
No arguments show help; there is no interactive command shell. Missing required
upload sources, download destinations/titles, or event text prompt only on a TTY.
Noninteractive deletes require `--yes`. Other legacy flags, such as editor,
owner, access, tags, groups, and debug options, are not implemented.

Titles/names use case-sensitive Go regular expressions; `--literal` selects
exact matching. Go regex syntax differs from Python (no lookaround or
backreferences). Folder names and calendar titles match exactly and must resolve
uniquely. Use `--folder id:FILE_ID` and a calendar ID for stable scripts.
`--id` cannot be combined with document title/folder selectors or Calendar
text/query/date selectors. `--src` prepends a source to positional inputs.
Quote each event's complete text; separate arguments create separate events.

## Output

| Resource | Default text fields | Supported fields |
| --- | --- | --- |
| Docs | `title,url-site` | `id,title,name,url,url-site,type` |
| Events | `title,when` | `id,title,url,url-site,when,where,start,end` |
| Contacts | `name,email` | `id,title,name,email,phone` |
| Calendars | Title, ID | Fixed pair; no `--fields` |

Text rows have no column header. Events have a blank line and `[Calendar title]`
heading. The default delimiter is a comma; embedded delimiters become spaces,
not CSV quoting. Missing values default to `N/A`. Multiple contact emails/phones
use semicolons with a comma delimiter, otherwise commas. `type` is a Drive MIME
type. JSON emits full resource arrays, including `[]` for empty results, with no
Calendar heading. Upload/add produce progress on stderr and arrays only with
`--json`; downloads and deletions produce progress on stderr. Errors return a
nonzero exit status. Many historical fields and exact old date-rendering details
are unsupported. JSON resource shapes are defined in `internal/model/resources.go`.

## Drive behavior

List excludes trashed files and folders. `docs get --folder NAME DEST` downloads
that folder's files; add a positional title and destination to filter them.
Folder selection is not recursive. Explicit file IDs fetch that file directly.
Shared-drive enumeration and Drive shortcuts are not qualified for this alpha.

Uploads create new files, never replace a matching title. Conversion is requested
for txt/md/html/htm/doc/docx/odt/rtf, csv/tsv/xls/xlsx/ods, and ppt/pptx/odp;
Google decides whether the input is convertible. `--format` overrides the input
extension used for MIME/conversion selection. `--no-convert` preserves binary
content. Unknown extensions use the OS MIME registry or application/octet-stream.

Native Google files export using txt/pdf/html/csv/tsv/docx/xlsx/pptx/odt/ods/odp/
rtf/png/jpg/svg, subject to the source type's supported Google export formats.
Defaults are txt (documents), xlsx (sheets), pptx (slides), and png (drawings).
Legacy xls/ppt exports are unsupported. Ordinary files download unchanged;
`--format` only affects native Google exports.

Downloads require an existing directory when multiple files match. They refuse
existing files and symlinks at the target filename. Unsafe remote names (path
separators, control characters, Windows device/stream aliases) require an explicit
safe destination filename. Failed transfers remove the partial file; process
termination or power loss may leave it. The destination directory must be trusted.
Drive delete moves files to trash; it never permanently deletes them.

## Calendar dates and deletion

`--date` accepts YYYY-MM-DD, RFC3339 with offset, today/tomorrow/yesterday, or
comma-separated boundaries. List date-only end boundaries are inclusive; either
list boundary can be empty. With no title/query/date, list starts at today's local
midnight. `today` covers the local day, including daylight-saving transitions.
Date-only input and formatted text use the machine's local timezone, which may
differ from the selected calendar's timezone. RFC3339 input carries its own offset.

Explicit event dates use an **exclusive** end. A single date creates a one-day
all-day event; a single timestamp creates a one-hour event. All-day and timed
boundaries cannot be mixed. Without `--date`, Google's Quick Add interprets the
text in the calendar's context. Reminders accept integer minutes or s/m/h/d/w;
seconds truncate to whole minutes, within 0–40320 minutes.

List expands recurring instances. Deleting a matched instance deletes that
instance. An explicitly supplied recurring series master ID can delete the
whole series: use an instance ID if that is your intent. Quick Add plus a reminder
requires two API writes; failure of the second can leave an event without the
requested reminder. Do not blindly repeat the add command.

## Configuration

INI sections and keys are case-insensitive. Precedence is explicit flag, service
section (`docs`, `calendar`, `contacts`), `[GENERAL]`, then built-in default.
Auth commands use the selected `--service` section for the profile too.

| Setting | Applies to | Default / meaning |
| --- | --- | --- |
| `user` | Service commands and corresponding auth commands | `default` local profile label |
| `fields` | Text list commands | Per-service defaults above |
| `delimiter` | Text output | `,`; empty value falls back to comma |
| `regex` | Title/name selectors | `true`; false selects literal matching |
| `folder` | Docs selectors/upload | No folder; conflicts with explicit `--id` |
| `cal` | Calendar event commands | Primary calendar |
| `missing_field_value` | Text fields | `N/A` |
| `date_print_format` | Calendar text | `%b %d %H:%M` |
| `document_format` | Docs get, native documents | `txt` |
| `spreadsheet_format` | Docs get, native sheets | `xlsx` |
| `presentation_format` | Docs get, native slides | `pptx` |
| `drawing_format` | Docs get, native drawings | `png` |

Supported date directives: `%Y %y %m %b %B %d %e %H %I %M %S %p %a %A %z %Z %%`.
Other INI keys are retained on disk but ignored; config files are never rewritten.
Unknown explicit command flags fail rather than inheriting this INI behavior.
A legacy setting for xls/ppt export must be changed or overridden with `--format`.
Text output settings do not project/filter JSON fields.

`--config PATH` selects an explicit INI file and errors if unreadable. Otherwise,
read `config` inside the platform configuration directory described in
[authentication](authentication.md). If absent, try
`$XDG_CONFIG_HOME/googlecl/config` or `~/.config/googlecl/config` for old installs.
When `GOOGLECL_CONFIG_DIR` is set, that directory is isolated: no legacy fallback.
It changes storage and default INI lookup; `--config` changes only INI lookup.

## Not implemented

| Area | Alpha status |
| --- | --- |
| Docs edit | Unsupported; get/upload creates a new file, not an edit |
| Contacts mutations and groups | Unsupported; saved contacts list only |
| Gmail, Blogger, YouTube | Unsupported |
| Picasa, Finance | Original APIs retired; original services cannot be restored |
| Interactive shell, Python plugins | Unsupported |
| Legacy OAuth tokens | Not reusable; desktop OAuth login required |
| OS keychain, cross-process token locking | Not implemented |
| Bulk transactions | Stop at first failure; earlier writes remain |

Automatic reads have up to three attempts for selected transient HTTP statuses
and up to 1000 pages. Hitting a page limit fails without returning partial rows.
Writes are not automatically replayed by the retry transport. No live Google
account or six-platform runtime qualification is implied by automated tests.
