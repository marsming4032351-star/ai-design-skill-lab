# AI Native Design Runtime Workspace

## 1. 这是什么

AI Native Design Runtime Workspace 是当前 `ai-design-skill-lab` 的展示层升级。

它把原本只在 CLI 里输出的 Harness Runtime 生命周期，整理成可展示、可理解、可观察、可操作的工作台：

- Runtime Timeline：看一次 run 如何从 goal 走到 archive。
- Runtime Dashboard：看当前状态、latest run、critic、review queue、metrics。
- Runtime Lifecycle：用 Mermaid 表达 retry loop、blocked state、human boundary。
- Runtime Governance：解释为什么 review_required、blocked state、Git review 是必要治理。
- Runtime Company：把 Echo、Henry、Planner、Critic、Runtime OS 放进同一个组织结构里理解。

## 2. Runtime Timeline

本地打开：

```bash
open demo/runtime_timeline.html
```

Timeline 展示：

- Goal -> Planner -> Generator -> Critic -> Retry -> Review -> Archive
- step_history
- event_log
- review_required
- retry_count / max_retries
- blocked_state
- archive 状态
- Runtime OS 架构图

它适合演示给合伙人、技术朋友和投资人看：这个项目不是单次生成工具，而是有生命周期、有反馈、有边界、有归档的 AI Runtime。

## 3. Runtime Dashboard

本地打开：

```bash
open demo/runtime_dashboard.html
```

Dashboard 展示：

- 当前 runtime state
- latest run
- retry count
- critic result
- blocked state
- event log
- step history
- review queue
- runtime metrics
- runtime company structure

其中 Runtime Company 结构包括：

- Echo：Human executive boundary
- Henry：Operator
- Planner：Goal decomposition
- Critic：Quality gate
- Runtime OS：Lifecycle, event log, review queue, archive memory

## 4. Runtime Lifecycle

核心生命周期：

```text
Human Goal
-> TaskSpec
-> HarnessRuntime
-> RunContext
-> Planner
-> Generator
-> Critic
-> Retry Loop
-> Human Review Boundary
-> Archive
-> Pattern Memory
```

这条链路把 AI 输出变成可检查的过程。

CLI demo：

```bash
python3 scripts/run_harness_demo.py examples/harness_goal.yaml
```

运行结果里重点看：

- `run_id`
- `final_state`
- `step_history`
- `event_log`
- `review_required`
- `retry_count`
- `max_retries`

## 5. Runtime Governance

Runtime Governance 的目标是：AI 可以自动执行，但不能绕过关键边界。

当前治理点包括：

- Review Loop：critic 不通过时必须反馈并重试。
- Retry Loop：retry_count 受 max_retries 限制，不能无限循环。
- Blocked State：遇到 OAuth、Keychain、权限、人工确认时暂停，而不是假装能自动修复。
- Human Review Boundary：发布、归档、外部系统同步前，需要人类确认。
- Git Governance：commit 是本地 milestone，push 是外部 publish。

## 6. Git Workflow

当前推荐流程：

```text
Human Goal
↓
Codex 修改
↓
pytest
↓
git status
↓
Security Audit
↓
git add 指定文件
↓
git commit
↓
Human Review
↓
git push
↓
GitHub
```

原则：

- 不默认 `git add .`
- commit 可以由 AI 执行
- push 前必须 review
- push 前检查 token、output、logs、pycache、docs、auth cache

## 7. Human Review Boundary

Human Review Boundary 是整个 Runtime 的安全阀。

它表示：

- AI 可以计划、生成、评价、重试、整理文档。
- 但遇到外部授权、公开发布、GitHub push、飞书发布、架构性变更时，需要人类边界。
- Runtime 应该记录这个边界，而不是无限 retry。

这就是 `review_required` 的核心思想。

## 8. Runtime Company

Runtime Company 是把 AI Runtime 当成一个小型公司来设计：

```text
Echo gives direction.
Henry operates the workspace.
Codex executes.
Planner decomposes.
Generator produces.
Critic reviews.
Harness records lifecycle.
Git keeps memory.
Feishu explains.
Obsidian remembers.
```

这个模型的价值是让 AI 协作从“聊天式工具使用”升级为“组织化执行系统”。

## 9. 当前 Workspace 文件

本次新增：

- `demo/runtime_timeline.html`
- `demo/runtime_dashboard.html`
- `docs/visuals/runtime_flow.md`

相关已有入口：

- `demo/runtime_cockpit.html`
- `docs/feishu/GIT_WORKFLOW_GUIDE.md`
- `docs/feishu/AI_NATIVE_DESIGN_RUNTIME_USER_GUIDE.md`
- `docs/feishu/CODEX_WORKFLOW_GUIDE.md`

## 10. Runtime Workspace Summary

当前 `ai-design-skill-lab` 已经从 Design Data Factory 升级成 AI Native Design Runtime Workspace。

它现在具备：

- 可运行：Harness demo 可以本地执行。
- 可观察：event_log 和 step_history 可以解释 run。
- 可治理：review_required、blocked_state、retry_count 控制边界。
- 可展示：Cockpit、Timeline、Dashboard 可以直接打开演示。
- 可沉淀：GitHub 记录代码，飞书承载移动端文档，Obsidian 可作为长期记忆。
