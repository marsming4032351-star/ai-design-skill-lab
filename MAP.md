# MAP.md — 仓库导航地图

> 这是给**人和 AI agent**进入仓库时的第一站。
> 目标：30 秒知道仓库在做什么，2 分钟知道我要做的事走哪条路。
> 如果你是 AI agent，**先读完本文件再读 AGENTS.md / CLAUDE.md**。
>
> 本文件由 `scripts/lint_map.py` 自动校验（路径存在性、CLI 可用性、待补项数量、措辞一致性）。
> CI 不强制，本地提交前手动跑：`python3 scripts/lint_map.py`。

---

## 1. 这个仓库是什么

`ai-design-skill-lab` 是一个 **AI 原生设计工作流的操作系统**，把设计过程中产生的资料、Prompt、规则、运行记录、成品图文，沉淀为**可复用、可校验、可被 AI 消费的工程资产**。

它由两套**目前相互独立**的系统组成：

- **Design Data Factory Pipeline**（`scripts/` + `shared/`）：偏**资产生产链路**——把原始素材逐步加工成 Pattern、Prompt、Rule、Run 记录。每个阶段独立 CLI，可单步调用。
- **AI Native Design Harness Runtime**（`harness/`）：偏**任务生命周期**——以 Goal → Plan → Generate → Critic → Review → Archive 的状态机，运行一次确定性的 AI 设计任务。**当前为 mock lifecycle，不调用 Pipeline CLI，也不实际共享 `shared/` 的资产层**。

两者关系详见第 3 节。

当前阶段：**实验中**（Harness M1–M3 完成，下一步 M4 Memory / M5 Evaluator / M6 Multi-Agent Runtime）。

---

## 2. 路由表：我要做 X，该走哪条路？

| 我想做的事 | 入口命令 / 文件 | 该读的文档 |
|---|---|---|
| **收集**一篇文章 / 链接 / Prompt 候选 | `scripts/capture.sh` 或 `scripts/obsidian_capture.py` | `docs/obsidian-staging-workflow/` |
| **盘点**一批设计素材，生成 manifest | `scripts/scan_inbox.py` | `prototypes/design-ingest/SKILL.md` |
| **生成** Plan（从素材 → 设计方向） | `scripts/run_design.py` | `docs/ARCHITECTURE_OVERVIEW.md` |
| **评价**一个设计方向 | `scripts/critic_design.py` | `references/40_Rules/`、`shared/rubric_engine.py` |
| **归档**通过评价的方向为 Pattern | `scripts/archive_design.py` | `references/30_Patterns/` |
| **生成** 设计产物（render） | `scripts/generate_design.py` | `docs/ARCHITECTURE_OVERVIEW.md` |
| **跑一次 Harness 任务**（mock lifecycle） | `scripts/run_harness_demo.py` 或直接 `harness/runtime.py` | `docs/HARNESS_USAGE.md`、`docs/HARNESS_M2_RUNTIME.md` |
| **生成小红书图文**（HTML → Playwright → PNG） | 入口待定位 ⚠️ | `docs/xiaohongshu-*/`（按子目录索引） |
| **运行测试** | `python3 -m pytest -q` | `tests/`、`AGENTS.md` 提交规则一节 |
| **校验本 MAP** | `python3 scripts/lint_map.py` | 本文件第 7 节 |
| **查看**仓库运行记录 / 历史 | 浏览 `references/90_Runs/` | — |
| **找一个可复用 Pattern** | 浏览 `references/30_Patterns/` | — |
| **修改代码**（scripts/ / shared/ / harness/） | 看 AGENTS.md 提交规则 | `AGENTS.md` + `.codex/skills/karpathy-guidelines/SKILL.md` |
| **用 Claude Code 协作** | — | `CLAUDE.md` |
| **理解为什么这么设计** | — | `soul.md` |

> 标 ⚠️ 的条目是已知未补全项。如果你正在做这件事，**顺手把入口写进来**，比单独发 PR 更有效。

---

## 3. 两套系统的关系：当前 vs 目标

### 3.1 当前状态（截至 2026-05-11）

```
┌──────────────────────────────────────────────────────────┐
│           Design Data Factory Pipeline                    │
│                                                            │
│  00_Inbox_Staging ──► scan_inbox ──► run_design           │
│                              │                             │
│                              ▼                             │
│                       critic_design ──► archive_design     │
│                                                │           │
│                                                ▼           │
│                                       references/30_Patterns│
│                                                            │
│  共享：shared/{schema, frontmatter, prompt_render,         │
│         rule_engine, rubric_engine, recommendation_engine} │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│           Harness Runtime（当前 mock）                     │
│                                                            │
│  Goal ──► Planner ──► Generator ──► Critic ──► Review ──► │
│                                                Archive    │
│                                                            │
│  状态：harness/runtime.py 当前为确定性 mock lifecycle，    │
│        不调用 Pipeline CLI，不消费 references/，           │
│        不实际依赖 shared/ 中的资产引擎。                    │
│                                                            │
│  共享：events、task、registry 等运行时基础设施（harness/ 自带）│
└──────────────────────────────────────────────────────────┘

两套系统当前互不依赖，可各自独立演化。
```

### 3.2 目标状态（M4–M6 之后）

```
┌──────────────────────────────────────────────────────────┐
│                  Harness Runtime                          │
│                                                            │
│  Goal ──► Planner ──► Generator ──► Critic ──► Review ──► │
│              │             │            │         Archive  │
│              │             │            │            │     │
│              ▼             ▼            ▼            ▼     │
│       调用 / 编排 Pipeline 的对应 CLI 阶段                  │
│              │             │            │            │     │
│              ▼             ▼            ▼            ▼     │
│   scan_inbox  run_design  critic_design  archive_design   │
│                                                            │
│  共享层：shared/ 被双方消费，Pipeline 产物（references/）   │
│           成为 Harness 的记忆与判据。                       │
└──────────────────────────────────────────────────────────┘
```

### 3.3 简单决策规则

| 场景 | 走哪条 |
|---|---|
| 只做某一步（盘点 / Plan / 评价 / 归档） | **Pipeline 单步 CLI** |
| 跑一个 mock 的任务生命周期，验证 Runtime 行为 | **Harness Runtime** |
| 写代码扩展资产生产能力 | 在 `scripts/` 下新增 CLI + `shared/` 配套 |
| 写代码扩展任务生命周期能力 | 加 `harness/` 节点 |
| **跑一个端到端、真实接入 Pipeline 的任务** | ⚠️ 目前还不行，等 M4+ |

### 3.4 关于"是否合并"的未决问题

详见第 8 节。

---

## 4. 给 AI agent 的阅读顺序

如果你是 Codex / Claude Code 第一次进这个仓库：

1. **先读** → 本文件 `MAP.md`
2. **任务分类后再读其中一个**：
   - 写代码 / 改 scripts、shared、harness → `AGENTS.md` + `.codex/skills/karpathy-guidelines/SKILL.md`
   - 用 Claude Code 协作 → `CLAUDE.md`
   - 不确定该不该做某事 → `soul.md`（价值观）
3. **具体子流程**：按路由表去对应 `docs/` 文档

> 不要一次性读完所有全局说明文件（`AGENTS.md` / `CLAUDE.md` / `soul.md` / `docs/CODEX_GUIDE.md` / `docs/available-skills-guide.md`）。
> 按需读，多读不仅浪费 token，还会引入冲突判断噪音。

---

## 5. 目录约定

| 目录 | 一句话定位 | 注意 |
|---|---|---|
| `00_Inbox_Staging/` | 资料**进入系统的入口**，未消化 | 应有"超过 30 天未处理"告警（未实现） |
| `imports/` | 外部导入的原料 | — |
| `references/30_Patterns/` | 已沉淀的可复用设计模式 | **核心资产**，schema 校验 |
| `references/40_Rules/` | 设计规则库 | — |
| `references/50_Prompts/` | Prompt 库 | — |
| `references/90_Runs/` | 运行历史 | **记忆闭环关键** |
| `references/schemas/` | 实体 schema 定义 | — |
| `references/beautiful-html-templates/` | ⚠️ 外部仓库 checkout | **建议未来迁出 references，挪到顶层 external 目录** |
| `references/10_Projects/` | 项目级资料 | — |
| `docs/` | ⚠️ 当前混合：文档 + 成品 + 评估 | **建议拆分（详见第 8 节）** |
| `demo/` | Runtime 可视化原型（cockpit / dashboard / timeline） | — |
| `examples/` | 示例 Goal 和 staging 样本 | — |
| `harness/` | Harness Runtime 源码 | 当前**不**调用 Pipeline |
| `scripts/` | Pipeline CLI 入口 | 每个 Python CLI 必须支持 `--help` |
| `shared/` | Pipeline 当前的共用核心库 | 未来 Harness 也会消费 |
| `hooks/` | Manual relay / 外部 hook | — |
| `prototypes/` | 实验性 skill / 原型 | 成熟后转正 |
| `tests/` | pytest 测试 | 提交前必须 `python3 -m pytest -q` |

---

## 6. 成熟度地图

| 模块 | 状态 | 说明 |
|---|---|---|
| `scripts/scan_inbox.py` | 🟢 稳定 | 主路径已用于实际素材摄入 |
| `scripts/obsidian_capture.py` | 🟢 稳定 | Obsidian staging 摄入入口 |
| `scripts/run_design.py` | 🟢 稳定 | 核心 Plan 生成路径 |
| `scripts/critic_design.py` | 🟡 演进中 | Rubric 规则仍在调整 |
| `scripts/archive_design.py` | 🟡 演进中 | Pattern schema 偶有变更 |
| `scripts/generate_design.py` | 🟡 演进中 | 渲染管线待与小红书路径打通 |
| `scripts/run_harness_demo.py` | 🟢 稳定 | Harness mock lifecycle 演示入口 |
| `harness/` M1–M3 | 🟡 演进中 | mock lifecycle 跑通，未接 Pipeline |
| `harness/` M4 Memory | 🔴 未开始 | 计划中 |
| `harness/` M5 Evaluator | 🔴 未开始 | 计划中 |
| `harness/` M6 Multi-Agent | 🔴 未开始 | 计划中 |
| `references/30_Patterns/` schema | 🟡 演进中 | 未稳定，写入需 lint 校验 |
| 小红书图文管线 | 🟡 演进中 | HTML/CSS → Playwright → PNG，入口待写进 MAP |
| Obsidian Staging | 🟢 稳定 | capture + scan 已成闭环 |

🟢 稳定 = 接口和路径不太会动 / 🟡 演进中 = 还会变 / 🔴 未开始 = 设计中

---

## 7. 维护本 MAP（带可执行规则）

### 7.1 何时必须更新 MAP

下列任一发生时，**同一次 commit 内**必须更新 MAP：

- 新增 / 删除 / 重命名 `scripts/` 下的 Python CLI
- 新增 / 删除 `harness/` 的 stage
- 新增 / 删除顶层目录
- 新增一类 `docs/<output-type>/` 成品包
- README / AGENTS / CLAUDE 的入口命令变化
- 第 6 节成熟度地图里任一模块状态迁移

### 7.2 自动校验（`scripts/lint_map.py`）

跑 `python3 scripts/lint_map.py`，应通过下列检查：

1. `MAP.md` 必须存在于 repo root
2. MAP 中所有反引号路径在仓库中真实存在
3. MAP 中提到的所有 `scripts/` Python CLI 必须能跑 `--help`
4. 路由表中所有 `docs/...` 路径必须存在（除显式标 ⚠️ 的）
5. 全文 "待补" / "TBD" 出现次数 ≤ 已标 ⚠️ 的条目数
6. **措辞一致性**：如果 `harness/runtime.py` 当前实现不调用 Pipeline CLI，
   MAP 第 3.1 节必须包含"不调用 Pipeline CLI"措辞，
   且**不允许**出现"Harness 复用 Pipeline 的各步骤"或"共享 shared 层"等未来态描述
7. 第 6 节成熟度地图必须覆盖第 2 节路由表中所有入口

### 7.3 维护原则

- 这份 MAP 是**导航**，不是完整文档目录。如果一个条目要写超过 3 行才说得清，说明那个东西本身需要简化，不是 MAP 写得不够长。
- 不要让 MAP 取代 README——README 面向"外部访客"，MAP 面向"已经决定要用这个仓库的人和 AI"。
- 当一条信息在多个地方重复时，让 MAP 指向源头，不要把内容复制进来。

---

## 8. 未决战略问题

这里显式记录尚未决定的架构走向，**避免 AI agent 把它当作"正常的含糊"**。

### 8.1 Pipeline 和 Harness 是否合并？何时合并？

- 现状：两套独立。
- 倾向：M4 Memory 阶段开始，让 Harness 消费 Pipeline 产物（`references/`）作为记忆层。
- M5 Evaluator 阶段开始，让 Harness 直接调度 Pipeline CLI 完成 Generator / Critic 步骤。
- 未定的关键问题：
  - `shared/` 的 engine 抽象（rule / rubric / recommendation）是否需要先做一轮接口稳定化？
  - Harness 是用子进程调 CLI，还是直接 import `scripts/` 的 main 函数？
  - 当 Harness 接管端到端流程后，`scripts/` 下的 CLI 是否还保留独立入口？（当前判断：**保留**，因为单步调试价值高）
- 推迟决策的代价：双系统会继续累积小幅重复（schema 校验逻辑、状态记录格式）。已可接受，但要在 M4 启动时复盘。

### 8.2 是否值得做"Skill 回写"机制？

- Karpathy 知识库架构里的 ingest 回写，对应到本仓库是：任务跑完后自动把"新模式"提议入库到 `references/30_Patterns/`。
- 现状：`scripts/archive_design.py` 是手动 archive，不是自动提议。
- 推迟原因：在 schema 未稳定前自动回写会污染 Pattern 库。等 30_Patterns schema 稳定（见第 6 节）后再启动。

### 8.3 docs/ 与 references/ 的拆分计划

- docs/ 当前混合三类内容：文档、成品、外部评估
- 计划拆分：
  - docs/ 只保留"给人读的文档"
  - 新增顶层 outputs/ 放生产成品（小红书图文、Feishu 文档等）
  - 新增顶层 external/ 放外部仓库 checkout（如 beautiful-html-templates）
- 未启动原因：拆分会破坏大量交叉引用，需要先做一轮 grep + 链接修复
- 触发条件：当 docs/ 顶层文件 > 50 个 或 outputs 类内容占比 > 30%

---

_Last updated: 2026-05-11 · 维护人：repo owner · 校验脚本：`scripts/lint_map.py`_
