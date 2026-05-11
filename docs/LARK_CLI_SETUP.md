# Lark CLI Setup

Date: 2026-05-09
Status: app secret restored in macOS Keychain; Feishu document creation verified outside the Codex sandbox

## Purpose

The goal is to make `lark-cli` a long-lived publishing channel for Codex, Harness Runtime, and Runtime Workspace outputs.

Reports, usage guides, architecture notes, project summaries, and future Harness run artifacts should be publishable to Feishu Docs or Feishu Wiki without repeating full authorization every time.

Important operating rule:

```text
Check existing config and auth state first. Do not start with lark-cli config init.
```

## Current Problem And Resolution

Codex could inspect the existing `lark-cli` auth state, but document creation was blocked because the app secret was missing from the credential store that `lark-cli` uses for app resolution.

Observed current state:

| Check | Result |
|---|---|
| `lark-cli` version | `1.0.0` |
| Config file | Present at `~/.lark-cli/config.json` |
| Brand | `feishu` |
| Default identity | `auto` |
| User identity | Present |
| `lark-cli auth status` | Returns user auth metadata and `tokenStatus=valid` |
| `lark-cli doctor` outside Codex sandbox | Passes config, app resolution, token, and endpoint checks |
| `lark-cli doctor` inside Codex sandbox | May fail to read Keychain, depending on sandbox permissions |
| App secret storage | Expected in macOS Keychain |
| App secret keychain item | Restored manually by the human owner |

The original failing check was:

```text
app_resolved: fail
keychain entry not found: lark-cli/appsecret:<app-id>
```

The app secret, token, and complete user open id are intentionally not copied into this repository document.

Verified result after repair:

```text
lark-cli doctor -> ok=true
lark-cli auth status -> tokenStatus=valid
lark-cli docs +create -> document created successfully
```

## Why `auth status` Is Visible But `docs create` Fails

`lark-cli auth status` and `lark-cli docs +create` do not prove the same thing.

`auth status` can read local user auth metadata:

- configured brand
- configured app id
- default identity
- known user
- granted scopes
- token expiry metadata
- token status

That metadata can exist even when the app secret cannot be resolved.

`docs +create` needs a working app context before it can call Feishu document APIs. In this setup, the app context is split across two stores:

- `~/.lark-cli/config.json`: non-secret app/user configuration
- macOS Keychain: secret material such as the app secret

The config file still pointed to an app, but the matching Keychain item was missing:

```text
lark-cli/appsecret:<app-id>
```

Therefore `auth status` can still print useful metadata, while `docs +create` fails before creating a document because the CLI cannot resolve the app secret.

## Current Credential Source Model

Current local sources:

```text
~/.lark-cli/config.json
~/.lark-cli/cache/remote_meta.meta.json
macOS Keychain
```

The config file is present and `lark-cli config show` redacts `appSecret` as `****`.

That redaction does not prove the secret is available. It only means the CLI knows the field is secret and should not print it. `lark-cli doctor` is the stronger check because it actually attempts app resolution.

## Safe Repair Strategy

Do not put `app_secret` into:

- this repository
- README
- docs
- shell history
- committed logs
- chat messages
- command output
- `.env` files that might be committed

The required repair is to restore the app secret into the local secure credential store that `lark-cli` expects.

### Preferred Manual Repair: Keychain Prompt

Use macOS Keychain and let `security` prompt for the secret instead of writing the secret in the command line.

Correct Keychain shape:

```bash
security add-generic-password \
  -U \
  -s 'lark-cli' \
  -a 'appsecret:<app-id>' \
  -w
```

Keep `-w` as the final option. macOS will prompt for the password value. Paste the app secret into that prompt, not into a file, not into the shell command itself, and not into chat.

Important detail:

```text
service = lark-cli
account = appsecret:<app-id>
```

Do not put the full `lark-cli/appsecret:<app-id>` string into the Keychain service field. `lark-cli` reports missing credentials as `service/account`, so the error text can look like a single path even though the Keychain fields are separate.

After writing the Keychain item, verify:

```bash
lark-cli doctor
lark-cli auth status
```

If the user token is expired or needs refresh after the app resolves, handle that as a separate user authorization boundary. Codex should not start a new auth flow unless explicitly instructed.

### Codex Sandbox Note

The repaired Keychain entry is visible when `lark-cli doctor` runs outside the Codex sandbox. Inside the default sandbox, `lark-cli doctor` may still report a missing Keychain item.

For Feishu publishing from Codex, run `lark-cli doctor`, `lark-cli auth status`, and `lark-cli docs +create` with the permissions required to access the user's macOS Keychain. Do not treat a sandbox-only Keychain failure as proof that the human repair failed.

### Alternative Manual Repair: CLI Stdin Mode

If the installed `lark-cli` version provides a dedicated repair command that accepts app secret from stdin, use that instead of putting the secret in an argument.

Safe shape:

```bash
<secure local secret source> | lark-cli <repair-command> --app-id '<app-id>' --app-secret-stdin
```

Only use a stdin-based CLI command if it does not reinitialize unrelated config and does not print the secret.

Avoid:

```bash
lark-cli config init
```

unless the human owner intentionally chooses a one-time full repair outside Codex. Codex should not run it for routine publishing.

## Correct Codex Flow For Creating Feishu Documents

Codex should use this flow:

```text
1. Run lark-cli auth status.
2. Run lark-cli doctor.
3. If doctor passes and tokenStatus is valid, create or update the Feishu document.
4. If doctor fails with missing app secret, stop.
5. Record BLOCKED_EXTERNAL / WAITING_AUTH.
6. Ask the human to repair Keychain securely.
7. Resume only after the human confirms doctor passes.
```

The publishing command, only after checks pass:

```bash
lark-cli docs +create --as user --title "<title>" --markdown "<markdown>"
```

Do not repeatedly run `docs +create` when `doctor` is failing. The failure is not retryable by the Runtime.

## Runtime Blocked State

Before repair, this issue should be classified as:

```text
BLOCKED_EXTERNAL
```

Reason:

```text
Configured app id exists, but the local secure credential store is missing the corresponding app secret.
```

Required human action:

```text
Restore the app secret to macOS Keychain or another lark-cli-supported secure credential store.
```

Codex action:

```text
Stop publishing attempts, document the state, and wait for human repair.
```

After repair, verified publishing can continue.

Test document created:

```text
Codex Feishu Keychain Connected
```

## Future Harness Publishing Flow

Harness should publish reports to Feishu through a dedicated publish stage.

Suggested flow:

```text
Harness run finishes
  -> produce markdown report
  -> run lark-cli auth status
  -> run lark-cli doctor
  -> if tokenStatus valid and doctor passes, publish with docs +create or docs +update
  -> record doc_url in RunContext state
  -> append publish event to event_log
  -> if auth/config blocked, enter WAITING_AUTH or BLOCKED_EXTERNAL
```

Suggested event types:

- `publish_requested`
- `publish_started`
- `publish_succeeded`
- `publish_failed`
- `auth_required`
- `blocked_detected`
- `runtime_paused`
- `runtime_resumed`

The publish stage should never hide auth failure as a normal retryable error. Feishu publishing is an external boundary, so it needs explicit blocked-state handling.

## Quick Diagnostic Commands

Use these commands before publishing:

```bash
lark-cli auth status
lark-cli doctor
lark-cli config show
lark-cli config default-as
lark-cli auth list
```

Expected healthy state:

```text
tokenStatus=valid
lark-cli doctor ok=true
app_resolved pass
```

If `doctor` fails, do not create documents yet.
