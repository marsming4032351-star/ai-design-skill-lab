# Design Harness System Architecture Proposal

Date: 2026-05-08
Status: Proposal
Scope: Upgrade path from Design Data Factory v6 to a long-running, evaluable, reusable, auditable Agent Runtime.

## 1. 当前 v6 架构总结

当前仓库是一个以设计知识实体为中心的 Design Data Factory v6。它已经把设计工作拆成可被 Agent 操作的闭环：

```text
ingest -> run -> critic -> archive -> pattern reuse
                -> generate -> future critic-visual -> archive
```

主要结构如下：

- `scripts/`: CLI 执行入口，包括 `scan_inbox.py`、`run_design.py`、`critic_design.py`、`archive_design.py`、`generate_design.py`。
- `shared/`: 共享运行库，包括 frontmatter、schema、prompt/rule/project/plan/critique/pattern loaders、prompt rendering、weighted rule/rubric/recommendation engines、manifest、entity update、Lovart adapter。
- `references/`: 版本化知识库，包括 Project、Pattern、Rule、Prompt、Run、schema 文档。
- `tests/`: 当前聚焦于 `design-run` 依赖链、Pattern 推荐、manual hook protocol。
- `docs/`: v6 架构说明、Codex 操作指南、设计决策、研究文档。
- `.codex/skills/karpathy-guidelines/`: 当前仓库的工程约束，强调小步、可验证、少改动。

v6 的核心设计不是“调用一次大模型”，而是把一次设计行为拆成可审计的数据变换：

```text
raw files -> Asset -> Plan -> Critique -> Pattern
                      -> Visual
```

每个阶段都尽量产生结构化实体、JSONL、Markdown note、Run log，并保留 prompt、rule、assets、patterns 等输入线索。

## 2. 当前架构已经具备哪些 Harness 能力

v6 已经具备 Harness System 的一部分基础能力：

- 可执行入口: 每个阶段都有明确 CLI，参数显式，适合被更高层 runtime 编排。
- Dry-run first: `--llm dry-run` 让核心流程无需真实 API 也可测试。
- Hook 隔离: `--llm hook --llm-hook <path>` 把 provider、密钥、网络调用隔离在主 pipeline 外。
- 结构化实体: Asset、Run、Plan、Critique、Pattern、Visual 使用 Markdown frontmatter 和 schema validator。
- Prompt 版本化: Prompt 作为 `references/50_Prompts/*.md` 实体存在，可独立演进。
- Rule 版本化: classification、scoring、recommendation rules 独立存放，可被 loader 和 engine 使用。
- Run audit: Run 记录 inputs、inputs_hash、outputs、entities_created、metrics、errors、next_eligible_skill。
- Critic 基础: `critic_design.py` 用 rubric rule + weighted engine 输出 decision。
- Pattern reuse 闭环: `archive_design.py` 生成 Pattern，`run_design.py` 推荐 Pattern 并写入 `consumed_patterns`。
- Prompt snapshot: `run_design.py` 输出 prompt snapshot，便于复盘模型输入。
- Human relay 基础: `hooks/manual_relay_hook.py` 支持人工把 prompt 发给外部模型并回填响应。
- 最小测试面: 当前测试能守住 `run_design.py --help` 依赖链、推荐 rule 加载、reuse_count 自增、manual hook mode。

这些能力说明 v6 已经不是脚本集合，而是一个轻量级、文件系统原生的 agent workflow substrate。

## 3. 当前缺失哪些 Harness 能力

要升级为 Design Harness System，当前缺口主要在“编排、评估、治理、长期运行”：

- 缺少 Workflow Runtime: 还没有一个统一 command 表达 `ingest -> run -> critic -> archive` 的状态机、暂停点、重试策略。
- 缺少 Run Store 索引: Run 记录存在，但没有统一查询、聚合、回放、diff、失败诊断视图。
- 缺少 Evaluation Harness: 规则文件有 `test_cases`，但没有统一 runner 把 prompt/rule/pattern/golden cases 跑成报告。
- 缺少 Model Output Contract 层: hook 返回 JSON 后由各脚本各自处理，还没有统一的 output parsing、repair、schema violation 分类。
- 缺少 Approval Policy: 目前人工确认隐含在 CLI 使用方式里，没有声明哪些动作必须人工批准。
- 缺少 Tool Registry: scripts、hooks、skills、external connectors 还没有统一的 registry、capability metadata、risk level。
- 缺少 Skill Registry: `.codex/skills`、prototype skills、repo skills 和外部 skill references 没有形成可检索的 runtime catalog。
- 缺少 Memory 分层: Project/Pattern/Run 都存在，但尚未区分 working memory、episodic memory、semantic memory、procedural memory。
- 缺少 Artifact Promotion Policy: staging output、references promotion、vault write、archive 的边界还不够显式。
- 缺少 Visual Critic: `design-generate` 已有 Visual 实体，但 `critic_visual.py` 仍是未来能力。
- 缺少 Provider Abstraction: 文本 LLM 有 hook 隔离，生图目前有 Lovart adapter，但没有统一 provider contract。
- 缺少 Observability: 没有统一 event log、duration breakdown、token/cost metadata、tool call trace、approval trace。
- 缺少 Replay/Reproduce: inputs_hash 已有，但还没有一键从 Run record 复现该次运行的命令。

## 4. Harness System 的目标定义

Design Harness System 的目标是：围绕大模型建立一个可长期运行、可评估、可复用、可审计的 Agent Runtime，用来承载设计生产与设计知识沉淀。

它应该满足六个约束：

1. 可运行: 每个 agent action 都能通过明确 runtime command 执行，而不是只存在于对话中。
2. 可评估: prompt、rule、critic、pattern recommendation、model output 都能用固定用例回归。
3. 可复用: 成功经验沉淀为 Pattern、Skill、Prompt、Rule，并能进入后续上下文。
4. 可审计: 每次运行都有 Run log、输入快照、输出实体、决策记录、人工审批记录。
5. 可治理: 高风险动作必须经过 approval loop，低风险动作默认 dry-run 或 staging。
6. 可演进: 新 agent、新工具、新 provider 能通过 registry 接入，而不是改动核心脚本。

一句话定义：

```text
Design Harness System = Agent Runtime + Evaluation Harness + Memory System + Tool/Skill Registry + Human Governance Loop
```

## 5. 未来目录结构建议

短期不要重构现有 `scripts/` 和 `shared/`。建议用增量目录承载 Harness 层：

```text
.
├── harness/
│   ├── README.md
│   ├── agents/
│   │   ├── design_run.yaml
│   │   ├── design_critic.yaml
│   │   ├── design_archive.yaml
│   │   └── design_generate.yaml
│   ├── runtime/
│   │   ├── workflows/
│   │   │   └── design_concept_loop.yaml
│   │   ├── approvals/
│   │   │   └── policies.yaml
│   │   └── providers/
│   │       └── hooks.yaml
│   ├── evaluators/
│   │   ├── suites/
│   │   │   ├── rules.yaml
│   │   │   ├── prompts.yaml
│   │   │   └── pattern_recommendation.yaml
│   │   └── reports/
│   ├── registry/
│   │   ├── tools.yaml
│   │   ├── skills.yaml
│   │   └── capabilities.yaml
│   └── memory/
│       ├── indexes/
│       └── promotion_policies.yaml
├── scripts/
├── shared/
├── references/
├── tests/
└── docs/
```

保留原则：

- `scripts/` 继续做阶段级 executor。
- `shared/` 继续做低层纯函数、loader、validator、engine。
- `harness/` 只做描述、编排、评估、治理、registry，不搬迁现有业务逻辑。
- `references/` 继续是长期知识库。

## 6. Agent 分层设计

建议把 Agent 分成四层：

| 层级 | 责任 | 当前对应 | 未来增强 |
|---|---|---|---|
| Domain Agent | 完成一个设计阶段 | `design-run`, `design-critic`, `design-archive`, `design-generate` scripts | 用 `harness/agents/*.yaml` 声明输入、输出、副作用、风险 |
| Evaluator Agent | 评估输出质量 | `critic_design.py`, `rubric_engine.py` | 增加 visual critic、prompt eval、golden case runner |
| Memory Agent | 管理沉淀与检索 | `pattern_loader.py`, `recommendation_engine.py` | 增加 memory indexes、promotion/demotion、anti-pattern |
| Orchestrator Agent | 负责任务状态机 | 目前缺失 | 编排阶段、approval gate、retry、resume、run replay |

Agent manifest 建议包含：

```yaml
id: design-run
kind: domain-agent
entrypoint: scripts/run_design.py
inputs:
  - project
  - manifest
  - prompts_dir
  - patterns_dir
outputs:
  - plan
  - run
side_effects:
  - writes_output_dir
  - optional_pattern_reuse_count_update
risk_level: medium
approval_required_for:
  - hook_llm
  - update_project
  - update_pattern_counts
```

## 7. Runtime 分层设计

Runtime 不应该一开始写成复杂框架。建议分三层：

| 层级 | 责任 | M1 做法 |
|---|---|---|
| Stage Runtime | 调用单个已有 script | 读取 agent manifest，生成等价 CLI command |
| Workflow Runtime | 串联多个 stage | YAML workflow + 手动执行/半自动执行 |
| Governance Runtime | 审批、重试、resume、replay | 先记录 approval intent，不做复杂 UI |

运行状态建议建模为：

```text
pending -> ready -> running -> waiting_for_approval -> succeeded
                                      -> failed -> retryable
                                      -> rejected
```

Run log 需要逐步扩展字段：

- `runtime_id`: 哪个 harness workflow 启动。
- `agent_id`: 哪个 agent manifest。
- `approval_events`: 谁在何时批准了什么。
- `provider`: 模型或生成器 provider。
- `cost`: token、image count、estimated cost。
- `replay_command`: 可复现命令。
- `artifact_policy`: 输出是 staging、reference promotion 还是 vault write。

## 8. Evaluator / Critic 的升级方向

当前 Critic 是单点 rubric scoring。升级方向是从“评审一次输出”变成“评估一类能力”：

1. Rule test runner
   - 读取 `references/40_Rules/*.md` 中的 `test_cases`。
   - 对 `rul_score_concept_direction` 和 `rul_recommend_pattern` 跑 deterministic engine 测试。
   - 输出 eval report 到 `harness/evaluators/reports/`。

2. Prompt contract eval
   - 对 `references/50_Prompts/*.md` 的 required inputs、template placeholders、output schema 做静态检查。
   - 对 dry-run output 做 schema validation。

3. Critic calibration
   - 保存少量 golden Plan/Critique pairs。
   - 检查 weighted_score、decision、feedback 是否稳定。

4. Visual critic
   - 新增 `critic_visual.py` 之前，先定义 Visual rubric。
   - 维度建议：brief fit、brand consistency、composition、readability、asset fidelity、craft、reuse potential。

5. Meta critic
   - 评估 Critique 自身是否有证据、是否可执行、是否过度宽松。

## 9. Memory / Pattern / Run Log 的升级方向

建议把 memory 分成四类：

| Memory 类型 | 当前载体 | 未来职责 |
|---|---|---|
| Working Memory | CLI inputs、prompt context | 单次运行临时上下文 |
| Episodic Memory | `references/90_Runs/*.md` | 每次执行的事件、输入、输出、审批 |
| Semantic Memory | `references/30_Patterns/*.md` | 可复用设计知识、反例、适用条件 |
| Procedural Memory | Prompt、Rule、Skill、Agent manifests | 如何执行、如何评估、如何调用工具 |

升级建议：

- Pattern 增加 lifecycle: `draft -> active -> validated -> deprecated -> replaced`。
- Pattern 增加 negative applicability: 当前已有 `not_applicable_when`，后续应参与推荐过滤。
- Run 增加 index: 用 JSONL 或 markdown index 汇总 run_id、agent、project、outcome、decision、cost。
- Run 增加 replay: 每个 Run 存生成它的 normalized command。
- Memory promotion: 只有 Critique pass 且人工确认后才能把 staging Pattern promotion 到 `references/30_Patterns/`。
- Memory demotion: 低质量、重复、过时 Pattern 可标记 deprecated，不直接删除。

## 10. Tool / Skill Registry 的设计方向

Tool Registry 负责回答三个问题：

1. 有什么工具可以用？
2. 工具会读写什么？
3. 工具风险等级和审批要求是什么？

建议初始 registry：

```yaml
tools:
  - id: design-run-cli
    entrypoint: scripts/run_design.py
    kind: local-cli
    reads: [project, manifest, prompts, patterns, rules]
    writes: [plan, run, prompt_snapshot, optional_project, optional_pattern]
    risk_level: medium
  - id: manual-llm-relay
    entrypoint: hooks/manual_relay_hook.py
    kind: hook
    reads: [prompt_json]
    writes: [request_file, stdout_json]
    risk_level: medium
```

Skill Registry 负责把 `.codex/skills/`、`prototypes/`、外部 skill references 和未来 first-party design skills 纳入 catalog。

建议字段：

- `id`
- `path`
- `trigger`
- `capabilities`
- `entrypoints`
- `references`
- `assets`
- `risk_level`
- `approval_required`
- `last_verified_at`

M1 不需要做自动发现。先维护 YAML registry，避免过早引入复杂依赖。

## 11. Human Review / Approval Loop 的设计方向

当前系统已经有隐含审批点：hook 调用、project 更新、pattern reuse_count 更新、archive promotion、真实 Lovart live 调用。Harness 需要把它们显式化。

建议审批等级：

| 等级 | 动作 | 默认策略 |
|---|---|---|
| Low | dry-run、写 staging output、读 references | 自动允许 |
| Medium | hook LLM、更新 project.run_history、更新 reuse_count | 需要命令行确认或 policy 允许 |
| High | live provider、上传客户素材、写真实 vault、promotion 到 references | 必须人工确认 |
| Critical | 删除历史记录、覆盖 Pattern、force rewrite | 默认禁止 |

审批记录应进入 Run log：

```yaml
approval_events:
  - action: hook_llm
    risk_level: medium
    requested_at: 2026-05-08T10:00:00Z
    approved_by: human
    approved_at: 2026-05-08T10:01:00Z
    note: manual relay via local files
```

## 12. 最小可落地版本 M1

M1 目标：不重构现有 pipeline，只把它包成 Harness 可描述、可评估、可审计的最小外壳。

范围：

- 新增 `harness/registry/tools.yaml`。
- 新增 `harness/agents/*.yaml` 描述现有 scripts。
- 新增 `harness/runtime/workflows/design_concept_loop.yaml` 描述 ingest/run/critic/archive 顺序和人工 gate。
- 新增 `harness/runtime/approvals/policies.yaml` 描述风险等级。
- 新增一个轻量 eval runner，优先只跑 Rule test cases 和 prompt placeholder static checks。
- 新增 tests 覆盖 registry YAML 可解析、agent entrypoint 存在、workflow stage 指向已注册 agent。
- 不改 `scripts/` 和 `shared/` 的执行逻辑。

M1 成功标准：

- `python3 -m pytest -q` 通过。
- `harness/` 中的 registry 能解释当前所有核心 stage。
- 至少能生成一份 evaluator report，说明 `rul_recommend_pattern` 和 `rul_score_concept_direction` 的 test cases 是否通过。

## 13. 中期版本 M2

M2 目标：把 Harness 从“描述层”升级为“半自动 runtime”。

范围：

- 新增 `scripts/harness_run.py` 或 `harness/runtime/runner.py`。
- 支持读取 workflow YAML，逐步执行 stage。
- 每个 stage 执行前显示 inputs、outputs、side effects、approval requirement。
- 支持 `--dry-run-plan` 只打印将执行的命令。
- 支持 `--resume-from <run_id>` 或 `--resume-stage <stage_id>`。
- Run log 写入 `runtime_id`、`agent_id`、`replay_command`、`approval_events`。
- 增加 visual critic 的 schema/rubric/prompt，并把 `generate -> critic-visual -> archive` 纳入 workflow。
- Pattern recommendation 增加 `not_applicable_when` 和 deprecated/replaced filter。

M2 成功标准：

- 一条 workflow 可以从已有 staging manifest 开始跑 `run -> critic`。
- 每个真实 LLM/provider 调用前都有 approval gate。
- evaluator report 可在每次改 prompt/rule 后作为回归检查运行。

## 14. 长期版本 M3

M3 目标：成为长期运行的 Design Agent Operating System。

范围：

- Run Store: 支持查询、聚合、失败诊断、replay、diff。
- Memory Index: 支持 Pattern embedding 或 hybrid retrieval，但仍保留 deterministic fallback。
- Multi-provider Runtime: 文本模型、生图模型、Figma、Obsidian、Lark/GitHub 等 connector 统一成 capability registry。
- Continuous Evaluation: 每次 prompt/rule/skill 变更自动跑 eval suite。
- Human Review UI: 用本地报告或轻量 Web UI 展示 pending approval、run lineage、artifact promotion。
- Governance: provider cost limits、敏感素材策略、vault write policy、audit export。
- Skill Packaging: 把稳定 agent 能力打包为 first-party design skills，可被 Codex/Claude Code 复用。

M3 成功标准：

- 多项目、多轮运行后，系统仍能回答“某个 Pattern 为什么被推荐”、“某个 Visual 来自哪个 prompt 和素材”、“某个规则变更影响了哪些历史结果”。
- Agent 可以长期运行，但所有高风险动作都有审批记录和可回放证据。

## 15. 不建议现在做的事情

- 不建议现在重构 `scripts/` 和 `shared/`。当前 pipeline 可运行，先在外层加 Harness 描述和评估。
- 不建议现在引入数据库。文件系统 + YAML/JSONL 足够支撑 M1。
- 不建议现在上复杂 workflow engine。先用 declarative YAML + 小 runner。
- 不建议现在做 embeddings。Pattern 推荐已有 deterministic baseline，先补 eval，再考虑混合检索。
- 不建议现在把 provider SDK 深度耦合进核心脚本。文本继续 hook，视觉 provider 先通过 adapter 隔离。
- 不建议现在自动写真实 Obsidian Vault。先把 staging、promotion、approval policy 做清楚。
- 不建议现在把所有目录迁移到 `harness/`。这会破坏 v6 已有认知和测试面。
- 不建议现在追求全自动 archive。Pattern promotion 应保留人工 gate。

## 16. 下一步真正写代码时的任务拆分

建议创建 git branch：是。建议分支名：

```bash
git checkout -b feat/design-harness-m1
```

原因：M1 会新增 `harness/`、测试和可能的 evaluator runner，虽然不重构业务代码，但会形成一组可审查的结构性变更。

| 步骤 | 目标 | 修改文件 | 测试方式 | 风险点 |
|---|---|---|---|---|
| 1 | 建立 Harness registry 骨架 | Create `harness/README.md`, `harness/registry/tools.yaml`, `harness/registry/capabilities.yaml` | `python3 -m pytest -q`；新增 YAML parse test | YAML schema 过度设计 |
| 2 | 为现有 stage 写 Agent manifests | Create `harness/agents/design_ingest.yaml`, `design_run.yaml`, `design_critic.yaml`, `design_archive.yaml`, `design_generate.yaml` | 测试 entrypoint 文件存在，declared outputs 非空 | manifest 与真实 CLI 参数漂移 |
| 3 | 写 M1 workflow 描述 | Create `harness/runtime/workflows/design_concept_loop.yaml`, `harness/runtime/approvals/policies.yaml` | 测试 workflow stage 都引用已注册 agent，risk level 合法 | approval gate 写得太抽象 |
| 4 | 增加 registry validator | Create `shared/harness_registry.py` 或 `harness/runtime/registry.py`; Create `tests/test_harness_registry.py` | `python3 -m pytest tests/test_harness_registry.py -q` | 若放进 `shared/` 会扩大共享库职责，M1 更建议放 `harness/runtime/` |
| 5 | 增加 rule evaluator runner | Create `scripts/evaluate_rules.py` 或 `harness/evaluators/rule_cases.py`; Create `tests/test_rule_evaluator.py` | 跑 `python3 -m pytest tests/test_rule_evaluator.py -q`；手动跑 evaluator 生成 report | 解析 rule `test_cases` 时不要重新实现复杂 YAML parser，复用 frontmatter |
| 6 | 增加 prompt static checker | Create `harness/evaluators/prompt_contracts.py`; Create `tests/test_prompt_contracts.py` | 检查 prompt inputs 覆盖 template placeholders，`python3 -m pytest -q` | placeholder synthesizer 与 `prompt_render.py` 规则不一致 |
| 7 | 写 M1 文档和使用说明 | Modify `docs/HARNESS_ARCHITECTURE_PROPOSAL.md`; Create or modify `harness/README.md` | 检查命令示例可执行；`git diff --check` | 文档与实际命令不一致 |

推荐提交节奏：

1. `docs: add design harness architecture proposal`
2. `feat: add harness registry and agent manifests`
3. `test: validate harness registry and workflow manifests`
4. `feat: add rule evaluator baseline`
5. `test: cover prompt contract checks`

## 17. 当前文档结论

Design Data Factory v6 已经完成了从“设计对话”到“设计数据工厂”的关键跃迁：实体化、规则化、dry-run、prompt/rule 版本化、run log、critic、pattern reuse 都已存在。

下一步不应该推倒重写，而应该加一层 Harness：先声明 agent、tool、workflow、approval、eval，再逐步让 runtime 执行这些声明。这样能保留 v6 的稳定闭环，同时把系统升级成可长期运行、可评估、可复用、可审计的 Design Agent Runtime。
