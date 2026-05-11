# Open Source Security Audit

Date: 2026-05-09
Repository: `ai-design-skill-lab`
Branch: `feature/design-harness-runtime`

## Audit Scope

This audit checks whether the current repository is suitable to push to a public GitHub repository.

Checked categories:

- token / key / secret
- Feishu / Lark workspace information
- local absolute paths
- shell output logs
- generated `output` files
- Python cache files
- zip files
- docs that may expose auth information
- `.gitignore` coverage

Constraints followed:

- No auth commands were run.
- No tokens were regenerated.
- No runtime behavior was changed.
- No files were deleted.
- Nothing was staged, committed, or pushed.

## Summary

No committed `.env` file, real access token, refresh token, bearer token, API key, app secret, webhook URL, cookie, `userOpenId`, or concrete Feishu `appId` pattern was found in tracked repository files during this scan.

The repository is not yet ideal for immediate public release because it still contains public-facing metadata and personal/local context that should be reviewed before opening:

- Feishu document URLs in `README.md` and `demo/runtime_cockpit.html`.
- Local absolute paths under `/Users/ming/...` in documentation and import logs.
- Historical import snapshots under `imports/`.
- Ignored local cache files currently present in the working tree.
- `.gitignore` is missing several recommended secret/cache patterns.

Current open-source readiness: **conditionally suitable after cleanup review**.

Open-source risk level: **Medium**.

Risk would become **Low** after redacting local paths, deciding whether Feishu doc links are intended to be public, and tightening `.gitignore`.

## Publicly Safe Content

These areas appear safe to publish from a secrets perspective:

- Harness runtime source under `harness/`.
- Core scripts under `scripts/`, based on the scan.
- Shared modules under `shared/`, with credentials read from environment variables rather than committed values.
- Tests under `tests/`.
- Harness design docs under `docs/HARNESS_*`, `docs/RUNTIME_*`, `docs/ARCHITECTURE_OVERVIEW.md`.
- Demo files, except for Feishu doc links that may reveal workspace/document metadata.

Environment variable names such as `LOVART_ACCESS_KEY` and `LOVART_SECRET_KEY` are not secrets by themselves. No actual Lovart key value was found.

## Not Recommended For Public Release Without Review

| File or path | Reason | Suggested action |
|---|---|---|
| `README.md` | Contains Feishu document URLs. These reveal document tokens and may expose internal workspace entry points if sharing permissions are broad. | Keep only if these documents are meant to be public; otherwise replace with placeholders or private setup instructions. |
| `demo/runtime_cockpit.html` | Contains Feishu document URLs in the mobile entry section. | Same as above: confirm public intent or replace with placeholders. |
| `docs/available-skills-guide.md` | Contains local skill root paths under `/Users/ming/...`. | Redact to generic paths such as `$CODEX_HOME/skills` before public release. |
| `docs/available-skills-guide-lark.md` | Contains local skill root paths under `/Users/ming/...`. | Redact to generic paths. |
| `imports/claude_20260504/IMPORT_LOG.md` | Contains source path `/Users/ming/Downloads/files` and local repo paths. | Redact local paths or remove historical import logs from public release. |
| `docs/superpowers/specs/2026-05-07-juxiantang-brand-fusion-design.md` | Contains local Desktop file paths and likely private project context. | Review for client/private content before public release. |
| `references/90_Runs/run_run_20260504_153521_5473.md` | Contains `/tmp/...` runtime paths. Not secret, but looks like local execution metadata. | Consider redacting runtime paths or marking as sample output. |
| `imports/**/run_run_20260504_153521_5473.md` | Contains duplicated `/tmp/...` runtime paths. | Consider removing import snapshots or redacting paths. |
| `docs/LARK_CLI_SETUP.md` | Contains auth workflow notes and historical blocked auth state. No real token was found, but it documents local Lark CLI state. | Keep only if this operational note is intended for public readers; otherwise move to private docs or sanitize. |
| `imports/` | Historical backup/import area. It may duplicate old run logs and private context. | Review manually before public release; consider excluding from open-source branch. |
| `repos/anthropics-skills`, `repos/openai-skills`, `repos/awesome-agent-skills` | These are gitlinks/nested repositories. They are not secret by themselves, but public consumers may see broken submodule-like entries if `.gitmodules` is absent. | Decide whether to publish as proper submodules, vendor them intentionally, or remove from public branch. |

## Must Gitignore Before Public Push

The current `.gitignore` already covers:

```gitignore
__pycache__/
*.pyc
.DS_Store
output/
playwright-cli/
.playwright-cli/
*.zip
/tmp/v6_*
/tmp/v6r*
/tmp/llm_*.json
/tmp/*_hook.py
```

Recommended additions before public release:

```gitignore
# Local environment and secrets
.env
.env.*
*.env
*.local

# Logs
logs/
*.log

# Auth and token caches
.lark-cli/
.auth/
.tokens/
*.token
*.credentials
*.secret

# Local tool caches
.pytest_cache/
.claude/
```

Use narrow patterns for secrets where possible. Avoid an overly broad rule like `*token*` if the repository intentionally contains documentation about token concepts.

## Suggested Deletions

Do not delete these automatically without owner review. Recommended candidates:

| Path | Reason | Suggested operation |
|---|---|---|
| local `__pycache__/` directories | Ignored generated Python bytecode. | Delete locally before release checks if desired. |
| local `docs/.DS_Store` | Ignored macOS metadata. | Delete locally before packaging or publishing. |
| `imports/` | Historical import snapshots may contain private context and duplicate old run logs. | Remove from public branch or sanitize before open source. |
| `docs/superpowers/specs/2026-05-07-juxiantang-brand-fusion-design.md` | Likely private brand/client planning material with local file paths. | Move to private notes or redact. |

## Suggested Local-Only Content

Keep these local or private unless there is a deliberate reason to publish them:

- Lark / Feishu auth setup notes with local CLI state.
- Feishu document URLs for private mobile workspace docs.
- Historical import logs and run snapshots.
- Client, brand, or project-specific design source paths.
- Local skill inventory paths under `/Users/ming/...`.
- Nested external skill repositories under `repos/` unless published as formal submodules.

## Scan Notes

Tracked-file scan did not find:

- `.env`
- committed `.pyc`
- committed `.DS_Store`
- committed `output/`
- committed `logs/`
- committed `*.zip`
- real `access_token`
- real `refresh_token`
- bearer token
- OpenAI / Anthropic API key patterns
- concrete Feishu `userOpenId`
- concrete Feishu `appId`
- webhook URL
- cookie value

Ignored local files found:

- `.claude/`
- `.obsidian/`
- `.pytest_cache/`
- `docs/.DS_Store`
- `harness/__pycache__/`
- `shared/__pycache__/`
- `tests/__pycache__/`

These are ignored and not tracked, but should not be copied into release archives.

## Current Open Source Decision

The repository is **not blocked by discovered live secrets**, but it should not be pushed public as-is without a human review of metadata and private-context files.

Recommended decision:

1. Keep runtime source, tests, and Harness documentation.
2. Redact local absolute paths.
3. Decide whether Feishu document links should remain public.
4. Move or sanitize private/client planning documents.
5. Tighten `.gitignore`.
6. Re-run this audit before pushing.

Final assessment: **Medium risk, cleanup recommended before public GitHub push**.
