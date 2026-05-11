# AGENTS.md：AI Design Skill Lab 协作规则

本文是 Codex / Claude Code / 其它执行型 Agent 进入本仓库后的工作协议。

先读 `MAP.md` 判断当前仓库结构和任务路由，再按任务类型读取本文件、`CLAUDE.md` 或具体 `docs/` 文档。涉及价值判断、资产边界或是否值得沉淀时，再读 `soul.md`。`soul.md` 解释这个仓库为什么存在；本文件规定 Agent 应该怎么协作、怎么产出、怎么验证、怎么提交。

## 1. 仓库定位

这个仓库是 **AI Design Skill Lab / Design Data Factory**。

它不是普通素材库，不是一次性生图项目，也不是网页模板合集。它的核心目标是把设计经验、AI 工作流、模板、Prompt、规则、评估文档、运行记录和发布成果沉淀为可复用资产。

Agent 在这里工作的重点不是“多生成一点内容”，而是把一次工作变成未来可以复用、验证和追踪的设计资产。

进入仓库后，默认理解为：

- `MAP.md` 是当前结构、任务路由和 Pipeline / Harness 边界的第一事实源。
- Design Data Factory 是数据和资产沉淀基础。
- Harness Runtime 是 AI 辅助设计任务的执行层。
- `docs/OUTPUT_SKILL_SPEC.md` 是小红书、HTML 导出、PPT / Presentation Output 等输出类任务的协议。
- `docs/` 是知识资产空间。
- `references/` 是参考隔离区。
- Git 是设计资产演化的版本系统。

## 2. Agent 执行原则

### 先分析，再执行

不要一上来写文件或复制代码。先阅读相关 README、已有文档、目录结构和用户目标，确认任务属于哪类资产：文档、图文包、模板评估、运行时能力、测试、外部参考，或 Git 提交整理。

### 先隔离，再吸收

外部项目、模板、源码、图片和 Prompt 不应直接混入主项目。先放在 `references/` 或任务目录的 `assets/` 中，写清来源、用途、边界，再决定是否吸收为项目资产。

### 先验证，再提交

完成任务后必须运行与任务匹配的验证：

- 文档任务：检查文件存在、关键章节完整、链接和路径合理。
- HTML/CSS 图文任务：检查浏览器渲染、PNG 导出、尺寸、文件完整性。
- 代码任务：运行相关测试；涉及核心脚本时优先运行 `python3 -m pytest -q`。
- Git 任务：先执行 `git status --short --branch`，再决定提交范围。

### 先沉淀方法，再追求数量

不要为了数量堆图、堆模板、堆 Prompt。优先沉淀可复用方法、判断标准、工作流和评估结论。

### 不把未验证的第三方源码直接混入主项目

完整第三方仓库默认不提交到主项目。除非用户明确要求 vendor 或 submodule，否则应保留为本地 reference，并在 `.gitignore` 或文档中说明处理方式。

## 3. 目录使用规则

### `docs/`

知识资产和交付成果目录。输出类任务优先遵守 `docs/OUTPUT_SKILL_SPEC.md`；本文件只保留执行边界和提交规则。

适合放：

- 架构说明；
- Harness Runtime 文档；
- Output Skill 规范；
- 小红书图文包；
- HTML/CSS 源文件；
- Playwright 导出的 PNG；
- 发布文案；
- 外部项目评估；
- 工作流复盘；
- Feishu / Obsidian / Codex 使用指南。

新建小红书图文时，使用：

```text
docs/<topic-name>/
├── README.md
├── index.html
├── post-copy.md
├── assets/
└── cards/
```

### `skills/`

可复用 Agent 能力目录。

适合放经过验证的操作流程、专门技能、可复用任务协议。不要把一次性提示词直接放进 `skills/`；只有当它能稳定指导 Agent 重复完成一类任务时，才适合成为 skill。

### `templates/`

项目内生模板目录。

只有经过评估、改造、验证并被认定可复用的模板，才应该进入 `templates/`。外部模板不能因为好看就直接放入这里。

### `references/`

参考隔离区。

适合放：

- 外部 GitHub 仓库 checkout；
- 示例项目；
- 规则；
- Prompt；
- patterns；
- schemas；
- run 样本；
- 可供研究但未必进入主项目的资料。

外部仓库放入 `references/` 后，仍然不等于要提交完整源码。优先提交本项目自己的评估文档，而不是第三方仓库本体。

### `runs/`

运行记录目录，如果存在，应保存可复盘的运行产物。

适合放能说明目标、输入、过程、判断和输出的记录。不适合放不可解释的临时缓存和一次性草稿。

### `assets/`

素材目录通常应跟随具体成果目录存在，例如 `docs/<topic>/assets/`。

适合放：

- GPT Image / Codex Image 生成的主视觉；
- 手动整理过的参考图；
- 图文包使用的局部素材；
- 可追溯来源和用途的视觉资产。

不要把未说明用途的图片堆进全局 assets。

### `examples/`

示例输入和演示目标目录。

适合放 Harness demo goal、可运行示例、最小复现输入。示例应保持轻量、可解释、可执行。

## 4. 外部 GitHub 项目处理规则

当用户给出一个 GitHub 仓库时，按以下流程执行。

### 读取与判断

先读取：

- `README.md`
- `AGENTS.md` 或类似 Agent 指南
- `package.json`、`index.json`、`pyproject.toml`、`Cargo.toml` 或其它入口配置
- 示例目录、模板目录或核心说明文件

然后判断：

- 项目定位是什么；
- 它解决什么问题；
- 对本仓库有什么价值；
- 是否适合小红书图文、PPT / HTML deck、Design Data Factory、Harness Runtime 或 Agent skill；
- 是否存在许可、体积、依赖、隐私、维护成本风险；
- 是否应该只作为参考，而不是进入主项目。

### 克隆与隔离

如需克隆，优先放入：

```text
references/<repo-name>/
```

不要直接修改主项目成品目录。不要把第三方源码复制进 `docs/`、`templates/`、`skills/` 或 `scripts/`，除非用户明确要求并说明原因。

### 评估与沉淀

外部项目处理后，应输出以下之一：

- `docs/<topic>_EVALUATION.md`
- `docs/<topic>/README.md`
- 接入建议文档
- 模板选择说明
- 风险和边界说明

评估文档至少应包括：

- 来源 URL；
- 已读取文件；
- 核心机制；
- 适用场景；
- 不适用场景；
- 是否建议接入；
- 如何接入当前工作流；
- 是否建议提交第三方源码。

默认不提交完整第三方仓库，除非用户明确要求。

## 5. 小红书图文生成规则

当任务是生成小红书图文时，默认输出规格：

- 比例：4:5；
- 尺寸：1080 x 1350；
- 格式：PNG；
- 每篇图文建议 3-5 张，除非用户指定更多；
- 最终目录放在 `docs/<topic-name>/`。

优先使用：

```text
HTML/CSS -> Playwright -> PNG
```

不要依赖生图模型直接生成中文长文案。主视觉可以用 GPT Image / Codex Image 生成，但标题、正文、流程、编号和说明文字应由 HTML/CSS 叠加，以保证中文可读、可改、可复查。

每篇图文建议包含：

- 封面页：明确主题和利益点；
- 方法页：解释核心判断；
- 流程页：展示步骤；
- 命令页或操作页：给出可执行动作；
- 总结页：沉淀原则、清单或下一步。

文案要适合小红书传播，但不能牺牲准确性。不要为了标题刺激而夸大工具能力，不要把未验证事实写成结论。

## 6. HTML / Playwright 导出规则

小红书图文包的文件职责：

- `index.html`：可编辑源文件；
- `cards/`：导出的 PNG；
- `post-copy.md`：发布标题、正文、评论区引导和标签；
- `assets/`：主视觉、背景图、参考图或其它素材；
- `README.md`：说明页数结构、素材来源、图片规格和编辑方式。

导出后必须检查：

- `cards/card-01.png` 等文件是否存在；
- PNG 是否为 1080 x 1350；
- 文件是否能被系统识别为 PNG；
- 文字是否溢出；
- 中文是否清晰可读；
- 背景图是否遮挡正文；
- `post-copy.md` 是否与卡片内容一致。

可使用 `file` 检查图片尺寸，例如：

```bash
file docs/<topic>/cards/card-01.png
```

如果使用 Playwright，应优先真实浏览器检查，而不是只假设 HTML 正常。

## 7. Git 提交规则

Agent 在提交前必须执行：

```bash
git status --short --branch
```

然后识别：

- 本次任务相关文件；
- 临时文件；
- 缓存文件；
- 无关文档改动；
- 第三方仓库 checkout；
- 可能包含 token、secret、auth cache、本机路径的文件；
- `.DS_Store`、`__pycache__`、`.playwright-cli/`、`.superpowers/` 等误生成文件。

提交规则：

- 只提交本次任务相关内容。
- 不默认使用 `git add .`。
- 不提交误生成文件。
- 不提交完整第三方仓库，除非用户明确要求。
- 如果 `docs/LARK_CLI_SETUP.md`、`docs/OPEN_SOURCE_AUDIT.md` 或其它无关文件有变更，应提醒用户，不要默认提交。
- commit message 使用中文，清晰说明本次资产沉淀内容。

推荐提交前输出：

```text
建议提交：
- <file>

不建议提交：
- <file>：原因
```

## 8. 人与 Agent 分工

### 人

人负责方向、审美、商业判断、发布边界和最终选择。

Agent 可以提供选项和建议，但不能替代人判断品牌气质、传播尺度、商业语境和公开发布风险。

### Codex

Codex 负责执行、检查、整理、导出和提交建议。

适合任务：

- 阅读仓库；
- 分析外部 GitHub 项目；
- 克隆到 `references/`；
- 编写评估文档；
- 创建 HTML/CSS 图文包；
- 使用 Playwright 导出 PNG；
- 检查文件完整性；
- 整理 git status 和提交范围。

### Claude Code

Claude Code 适合复杂重构、长文档规划、系统性改造、多阶段设计和大范围上下文整理。

当任务涉及跨模块架构、长文档体系或复杂代码重构时，可以优先让 Claude Code 承担规划或深度整理角色。

### Git

Git 负责版本沉淀。

每次提交应代表一个清晰资产里程碑：新增图文包、完成模板评估、沉淀工作流、更新设计规则、修复运行时能力。

### Obsidian / docs

Obsidian 和 `docs/` 负责知识资产管理。

有复用价值的判断、方法、案例、外部项目评估和发布包，应沉淀到 `docs/` 或可同步到 Obsidian 的文档结构中。

## 9. 禁止事项

不要未经确认删除用户资料。

不要把第三方仓库源码直接复制进主项目。

不要把一次性截图草稿当成资产。

不要在没有检查 `git status --short --branch` 的情况下提交。

不要为了好看牺牲中文可读性。

不要生成没有方法论价值的纯视觉堆图。

不要把未验证的工具输出、授权日志、本机路径、token、secret 或 auth cache 写进长期文档。

不要为了省事把 `references/`、`output/`、`.playwright-cli/`、`.superpowers/` 里的临时内容一并提交。

## 10. 输出格式要求

完成任务时，Agent 应输出：

```text
做了什么：
- ...

改了哪些文件：
- ...

建议提交：
- ...

不建议提交：
- ...

下一步建议：
- ...
```

如果没有提交，明确说明“未 commit”。如果验证没有运行或无法运行，说明原因，不要暗示已经验证。

输出应简洁，但必须让人能判断本次工作是否可复查、可提交、可继续。
