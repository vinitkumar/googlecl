# Authentication

GoogleCL uses OAuth 2.0 for installed desktop applications, with a loopback
callback, state validation, and PKCE. It does not collect your Google password
or use the retired copy/paste authorization-code flow.

## Set up a Google Cloud project

1. Create or select a project in [Google Cloud Console](https://console.cloud.google.com/).
2. Enable **Google Drive API**, **Google Calendar API**, and/or **People API**,
   depending on the commands you intend to use.
3. Configure the OAuth consent screen / Google Auth Platform branding and audience.
   For a personal external app in Testing, add your Google account as a test user.
4. Create an OAuth client with application type **Desktop app**. A web client or
   service-account key will not work with this alpha.
5. Download the JSON client configuration. Do not commit it or token files.
6. Run the login command for each service you need:

   ```sh
   google auth login --service docs --credentials /path/to/client_secret.json
   google auth login --service calendar --credentials /path/to/client_secret.json
   google auth login --service contacts --credentials /path/to/client_secret.json
   ```

The command opens your browser and waits up to five minutes. The callback
listener binds only to `127.0.0.1` on a randomly allocated port. Successful login
persists both the token and the desktop client configuration for that profile
and service. Subsequent commands do not need the original JSON file.

## Permissions

| Service | OAuth scope | Reason |
|---|---|---|
| `docs` | `https://www.googleapis.com/auth/drive` | Legacy commands must find existing files and upload/download/trash them |
| `calendar` | `https://www.googleapis.com/auth/calendar` | List calendars and create/delete their events |
| `contacts` | `https://www.googleapis.com/auth/contacts.readonly` | Read saved contacts through People API |

These are **per-service**, not per-command scopes. Docs and Calendar logins grant
write access even if you only run list commands. A narrow `drive.file` grant
cannot support arbitrary existing-file discovery, so this alpha does not pretend
it can. A project-owned OAuth client and public consent verification are not
included; users supply their own clients.

Google's external Testing mode can expire refresh tokens after seven days for
these scopes. Workspace administrators can also restrict app access. These are
Google policy constraints, not problems solved by reinstalling GoogleCL.

## Account profiles

```sh
google auth login --service docs --user alice@example.com --credentials client_secret.json
google docs list --user alice@example.com
google auth status --service docs --user alice@example.com
```

Use a distinct `--user` value for each account. It selects a local token namespace
and supplies a browser login hint. Check the account selected in Google's consent
screen: GoogleCL does not verify that its email matches the local profile label.
The default profile is named `default`; an existing INI `user` option may select
a different profile for legacy service commands.

## Storage

The default directory is:

- Linux: `$XDG_CONFIG_HOME/googlecl`, or `~/.config/googlecl`.
- macOS: `~/Library/Application Support/googlecl`.
- Windows: `%AppData%\googlecl`.

Set `GOOGLECL_CONFIG_DIR` to use a different directory. Tokens are isolated by a
hash of profile and service under `tokens/`; raw profile names never become file
paths. A shared initial `credentials.json` may also be placed in the config
directory. Legacy `--config` changes the INI file, **not** credential storage.

This alpha uses local JSON files, **not encrypted OS-keychain storage**. Files
are created with mode `0600` and directories with `0700` on Unix, then atomically
replaced. On Windows they inherit the directory's ACL: keep the directory private
to your Windows account. Do not use a shared/synced directory. Separate processes
should not refresh the same profile/service concurrently; cross-process locking
is not implemented.

```sh
google auth logout --service docs
```

Logout removes the local token. It does not revoke Google's server-side grant or
remove the saved desktop client configuration. To revoke access, use your
[Google account connections](https://myaccount.google.com/connections).

## Remote terminals

`--no-browser` prints the URL without launching a browser:

```sh
google auth login --service docs --credentials client_secret.json --no-browser
```

This still requires the loopback callback. In SSH, forward the printed callback
port from your browser machine to `127.0.0.1` on the remote host before following
the authorization URL. There is no device-code or OOB fallback. In WSL, ensure the
Windows browser can reach the WSL loopback listener; otherwise use a browser in
the same environment or an explicit port forward.

## Failures

- **Client JSON missing:** supply `--credentials` at login, or install the desktop
  JSON as `credentials.json` in the config directory.
- **Access blocked:** add your account as a test user and check administrator policy.
- **API disabled / 403:** enable the API in the same project as the OAuth client.
- **Refresh revoked/expired:** repeat `auth login` for that service/profile.
- **Wrong profile:** pass the same `--user` value used during login.
- **Browser did not open:** use the printed URL; the command still waits for the callback.
- **Login times out:** check loopback/firewall access and repeat login.

API commands never unexpectedly launch an authorization browser. Missing
credentials produce an error directing you to log in first.
