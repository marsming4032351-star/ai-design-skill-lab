# Lark CLI Setup

Date: 2026-05-09
Status: Current channel is configured partially, but not yet usable

## Purpose

The goal is to make `lark-cli` a long-lived working channel for Codex and Harness outputs.

Reports, usage guides, architecture notes, project summaries, and future Harness run artifacts should be publishable to Feishu Docs or Feishu Wiki without repeating full authorization every time.

The important rule is:

```text
Check existing config first. Do not start with lark-cli config init --new.
```

## Current Configuration State

Current local inspection showed:

| Check | Result |
|---|---|
| `lark-cli` installed | Yes |
| Version | `1.0.0` |
| Config file | Present at `~/.lark-cli/config.json` |
| Brand | `feishu` |
| Default identity | `auto` |
| Known user | `mars ming` |
| Auth token status | `no_token` |
| App secret in keychain | Missing |
| User token in keychain | Missing |
| `lark-cli doctor` | Fails at app resolution |
| Default drive/wiki/space config | No separate default space, drive, or wiki config found in `~/.lark-cli` |

The current channel is therefore not ready for document creation.

Observed failure:

```text
keychain entry not found: lark-cli/appsecret:<app-id>
```

This means the config file still points to an app whose secret should be stored in macOS Keychain, but the keychain item is missing.

## How To Check Whether Lark CLI Is Ready

Use these commands before creating documents:

```bash
command -v lark-cli
lark-cli --version
lark-cli config show
lark-cli config default-as
lark-cli auth list
lark-cli auth status
lark-cli doctor
```

Expected healthy signs:

- `config show` returns the app configuration.
- `config default-as` is known, preferably `user` or `auto`.
- `auth list` shows the intended user with a usable token status.
- `auth status` succeeds.
- `doctor` passes config and auth checks.

Do not print access tokens, refresh tokens, app secrets, or Authorization headers into logs.

## Identity Mode

For Codex publishing documents into the user's workspace, prefer user identity:

```bash
lark-cli docs +create --as user --title "Title" --markdown "Content"
```

Bot identity is useful for app-owned resources, but it may not see or manage the user's personal cloud space in the expected way.

The current default identity is:

```text
auto
```

For predictable document publishing, use explicit `--as user` in automation.

## How To Create A Feishu Document

Once auth is healthy, create a document with:

```bash
lark-cli docs +create \
  --as user \
  --title "Codex 飞书 CLI 连通性测试" \
  --markdown "这是一份由 Codex 通过 lark-cli 创建的测试文档。
如果你能看到这份文档，说明飞书 CLI 已经可以作为长期工作通道使用。"
```

Successful output should include a document token and document URL.

If creating inside a specific Feishu folder later, add:

```bash
--folder-token <folder_token>
```

If creating inside a Wiki space later, use the relevant `--wiki-space` or `--wiki-node` option.

## How To Avoid Repeated Authorization

Do not run `lark-cli config init --new` as the first step.

Use this decision flow:

```text
1. Run lark-cli doctor.
2. If doctor passes, create the document directly.
3. If config exists but auth is missing, inspect auth status/list.
4. If only user token is missing, run scoped auth login instead of full config init.
5. If app secret keychain entry is missing, repair app config/keychain once.
6. After repair, verify with doctor.
7. Only then publish documents.
```

For missing user authorization, prefer scoped login:

```bash
lark-cli auth login --scope "<required_scope>"
```

For missing app config or missing app secret keychain entry, `config init --new` may be required, but it should be treated as a one-time setup action.

## Repairing The Current Keychain State

The current local failure is not only a missing user token. The app itself cannot be resolved because the app secret keychain entry is missing.

If the existing app should be reused and the app secret is known, repair the app config non-interactively instead of creating another app:

```bash
printf '<app-secret>' | lark-cli config init \
  --app-id '<app-id>' \
  --app-secret-stdin \
  --brand feishu
```

Do not paste the real app secret into chat, shell history, logs, or committed files. Use a local secret source or paste it directly into the terminal command when you are operating the machine yourself.

After app config is repaired, verify:

```bash
lark-cli doctor
```

If the app resolves but the user token is still missing, run a bounded user login. Prefer `--no-wait` so the CLI returns the verification information instead of blocking indefinitely:

```bash
lark-cli auth login --domain docs,drive,wiki --no-wait --json
```

Then complete the browser authorization and finish with the returned device code:

```bash
lark-cli auth login --device-code '<device-code>'
```

Finally verify again:

```bash
lark-cli auth status
lark-cli doctor
```

## What To Do If Authorization Gets Stuck

Authorization may require browser login, QR scan, OAuth consent, or app configuration in Feishu.

Runtime behavior should be:

```text
detect auth boundary -> show required user action -> stop waiting -> enter WAITING_AUTH
```

Do not keep retrying.

Do not launch multiple authorization flows.

Do not leave an agent blocked indefinitely on `lark-cli config init --new`.

Recommended operator behavior:

1. Start one bounded init or login flow.
2. Copy the browser URL or QR instruction to the user.
3. Wait for a bounded period.
4. If not completed, stop the process.
5. Record the state as `WAITING_AUTH` or `BLOCKED_EXTERNAL`.
6. Resume only after the user confirms authorization is complete.

This matches the Harness blocked-state design: external auth is not an agent-repairable failure.

## Current Attempt Notes

A bounded `lark-cli config init --new` was attempted once after checking the existing config.

Result:

- First sandboxed attempt failed because network DNS lookup for `accounts.feishu.cn` was blocked.
- One escalated bounded attempt was allowed.
- It timed out after 90 seconds and was stopped.
- No reusable auth token or app secret keychain entry was created.
- The Feishu test document was not created because the CLI channel is still not authenticated.

Current blocked state:

```text
WAITING_AUTH / BLOCKED_EXTERNAL
```

Required human action:

```text
Complete Feishu app config and OAuth authorization once, then rerun lark-cli doctor.
```

## Future Harness Publishing Flow

Harness should eventually publish reports to Feishu through a dedicated publish stage.

Suggested flow:

```text
Harness run finishes
  -> produce markdown report
  -> check lark-cli doctor
  -> if healthy, publish with docs +create or docs +update
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

## Next Command Pattern

When the channel is healthy, use:

```bash
lark-cli docs +create --as user --title "<title>" --markdown "<markdown>"
```

Before each publishing session, use:

```bash
lark-cli doctor
```

If `doctor` fails with missing keychain or auth, fix that state first instead of repeatedly creating documents or rerunning full initialization.
