# Output Skill 规范

本文定义 ai-design-skill-lab / Design Data Factory 的正式 Output Skill 规范，用于统一小红书图文发布包、HTML 导出流程、PPT / Presentation Output，以及外部 skill 评估结果。

它不是某一个具体模板，也不是某个第三方仓库的 vendor 方案。它是一套输出层协议：规定一次设计输出应该如何组织文件、记录来源、验证质量、进入 Git，并在后续被 Codex / Claude Code 复用。

## 1. Output Skill 是什么

Output Skill 是把 Design Data Factory 中已经形成的 brief、资料、Pattern、Prompt、版式判断和运行记录，转成可发布、可演示、可归档成果的 Agent 能力。

它关注的是输出层：

- 小红书图文：HTML/CSS 源文件 -> Playwright / 浏览器截图 -> 1080 x 1350 PNG。
- Presentation：资料 / 提案结构 -> 横向 HTML deck -> 浏览器预览 / 截图 / 封面。
- 多平台传播：同一组观点拆成小红书、公众号头图、分享卡、直播 deck 或客户提案。
- 输出评估：检查文件结构、图片尺寸、中文可读性、来源记录和复用价值。

Output Skill 的目标不是“多生成一个成品”，而是让每次输出都能被复查、复用和再次调用。

## 2. 和 Design Data Factory 的关系

Design Data Factory 的主链路可以理解为：

```text
brief -> reference -> analysis -> plan -> prompt -> layout -> render -> review -> archive -> reuse
```

Output Skill 位于 `layout -> render -> review -> archive` 这一段，负责把结构化判断变成可交付资产。

它和仓库现有系统的关系如下：

| 系统 / 目录 | 职责 | 与 Output Skill 的关系 |
|---|---|---|
| `00_Inbox_Staging/` | 原始资料入口 | 提供文章、链接、品牌资料、截图、旧 PPT、Prompt 候选 |
| `references/30_Patterns/` | 可复用模式 | 提供内容结构、页面结构、提案叙事和版式经验 |
| `references/40_Rules/` | 设计规则库 | 提供检查标准和质量约束 |
| `references/90_Runs/` | 运行历史 | 记录一次输出从输入到成品的过程 |
| `docs/` | 当前知识资产和输出包目录 | 保存规范文档、评估文档、现阶段的发布包和提案输出 |
| `scripts/` | Pipeline CLI | 未来可提供导出、校验、归档等自动化入口 |
| `harness/` | 任务生命周期 Runtime | 未来可把 Output Skill 编排为 Archive / Deliver 阶段 |

当前阶段，Output Skill 主要以文档协议和人工 / Agent 执行流程存在。等 Harness M4-M6 之后，它可以成为被 Runtime 调度的输出节点。

## 3. 标准目录结构

现阶段输出包仍放在 `docs/` 下，遵守 MAP 中的现实约定。未来当仓库拆分 `outputs/` 和 `external/` 后，成品包迁入 `outputs/`，文档和评估继续留在 `docs/`，第三方 checkout 迁入 `external/`。

### 3.1 小红书图文包

```text
docs/<topic-name>/
├── README.md
├── index.html
├── post-copy.md
├── assets/
└── cards/
    ├── card-01.png
    ├── card-02.png
    └── ...
```

### 3.2 Presentation 输出包

```text
docs/<project-or-topic>/presentation/
├── README.md
├── index.html
├── images/
├── exports/
└── run-notes.md
```

### 3.3 外部 Skill 评估文档

```text
docs/external-skills/
└── <external-skill-name>-analysis.md
```

外部仓库源码不默认提交。需要阅读时可以临时克隆到 `/private/tmp` 或隔离 reference 目录；真正进入仓库的应是本项目自己的评估、接入判断和仿写方向。

## 4. 每个输出包必须包含哪些文件

每个正式输出包至少包含：

| 文件 / 目录 | 必须性 | 作用 |
|---|---:|---|
| `README.md` | 必须 | 说明输出目标、文件结构、规格、编辑和导出方式 |
| `index.html` | 必须 | 可编辑源文件，小红书为竖图卡片，Presentation 为横向 deck |
| `post-copy.md` | 小红书必须 | 发布标题、正文、评论区引导和标签 |
| `cards/` | 小红书必须 | 导出的 1080 x 1350 PNG |
| `assets/` | 按需 | 背景图、参考图、生成图、局部素材 |
| `images/` | Presentation 按需 | deck 内嵌配图、截图再设计、信息图素材 |
| `exports/` | Presentation 按需 | 封面、关键页截图、多平台导出图 |
| `run-notes.md` | Presentation 必须 | 记录输入来源、风格选择、页表、自检和迭代记录 |

如果输出包缺少 `README.md`，它只能算临时草稿，不能作为正式资产归档。

## 5. 小红书图文包标准

小红书图文包采用 HTML/CSS -> Playwright / 浏览器截图 -> PNG 的路线，不依赖生图模型直接生成中文长文案。

### 5.1 规格

- 比例：4:5。
- 尺寸：1080 x 1350 px。
- 格式：PNG。
- 建议张数：3-6 张，除非任务明确要求更多。
- 源文件：`index.html`。
- 成品目录：`cards/`。
- 发布文案：`post-copy.md`。

### 5.2 标准页面结构

一篇图文建议包含：

| 页类型 | 作用 |
|---|---|
| 封面页 | 明确主题和收藏理由 |
| 判断页 | 解释为什么选这个方法 / 工具 / 路径 |
| 流程页 | 展示步骤、链路或命令 |
| 操作页 | 给出可复制的 prompt、命令或检查方法 |
| 总结页 | 沉淀原则、清单或下一步 |

### 5.3 发布包检查清单

导出后至少检查：

- `cards/card-01.png` 等文件存在。
- PNG 尺寸为 1080 x 1350。
- 中文清晰可读，没有溢出。
- 背景图没有遮挡正文。
- `post-copy.md` 与卡片内容一致。
- `README.md` 写清页数、规格、源文件和导出方式。

## 6. HTML 导出流程标准

HTML 是当前仓库最稳定的视觉输出源格式。它的优势是可编辑、可 diff、可截图、可归档。

标准流程：

```text
确定主题
  -> 写卡片结构
  -> 编写 index.html
  -> 浏览器预览
  -> Playwright / 浏览器截图导出 PNG
  -> 检查尺寸、文字、遮挡和发布文案
  -> 归档 README + HTML + PNG + post-copy
```

导出时应避免把中文长文案交给生图模型直接渲染。生图模型更适合生成主视觉、背景、插图和质感素材；标题、正文、编号、流程和检查清单应由 HTML/CSS 叠加。

## 7. PPT / Presentation Output 接入

Presentation Output 是面向客户提案、线下分享、方法论发布、直播课程和内部评审的横向输出层。

它可以借鉴 `guizang-ppt-skill` 的结构，但不直接复制第三方仓库源码。当前应吸收的方法包括：

- 风格选择；
- 版式库；
- 图片槽位；
- 配图提示词；
- 自检 checklist；
- 浏览器预览；
- 校验脚本；
- 输出归档。

### 7.1 Presentation 标准流程

```text
输入资料
  -> 提案 brief
  -> 风格选择
  -> 页表规划
  -> 图片槽位规划
  -> 生成 / 编写 index.html
  -> 浏览器预览
  -> 导出封面和关键页
  -> 自检
  -> 写 README.md 和 run-notes.md
```

### 7.2 风格选择

| 场景 | 推荐方向 |
|---|---|
| 品牌故事、文化叙事、空间体验、行业观察 | 电子杂志风 |
| 策略提案、产品说明、方法论、数据和路线图 | 瑞士国际主义风 |
| 客户必须编辑 `.pptx` | 不适合 HTML deck，需另选交付方式 |
| 多人实时协作编辑 | 不适合当前 Output Skill |

一份 deck 内不建议混用两套视觉系统。需要同时讲情绪和策略时，可以拆成两个输出：一个讲品牌气质，一个讲执行路径。

### 7.3 页表和自检

Presentation 生成前必须先写页表：

```text
页码 -> 页面目的 -> 版式 -> 图片槽位 -> 来源资料 -> 自检要点
```

输出完成后至少检查：

- 浏览器能直接打开。
- 翻页正常。
- 图片路径正常。
- 每页只有一个主要任务。
- 中文没有溢出。
- 图片没有裁掉关键内容。
- `README.md` 说明用途、受众、风格、导出方式。
- `run-notes.md` 记录输入、页表、判断过程和自检结果。

## 8. docs / outputs / references / external 的边界

当前仓库尚未拆出顶层 `outputs` 和 `external` 目录，因此正式成品仍放在 `docs/` 下。拆分前按以下规则执行。

### 8.1 现在进入 docs 的内容

- Output Skill 规范文档。
- 外部 skill 评估文档。
- 小红书图文发布包。
- Presentation 输出包。
- Feishu / Obsidian / Codex 工作流说明。
- 可供人和 Agent 阅读的复盘、指南、接入建议。

### 8.2 现在进入 references 的内容

- 可复用 Pattern。
- 规则、Prompt、schema。
- 运行记录。
- 内部样本和隔离参考资料。
- 外部仓库 checkout 仅作为隔离研究对象，默认不提交完整源码。

### 8.3 未来进入 outputs 的内容

未来拆分后，以下内容应从 `docs/` 迁出到顶层 outputs 目录：

- 小红书 PNG 成品包。
- HTML deck 成品。
- Feishu 文档导出结果。
- 多平台封面和分享图。
- 已完成交付的 proposal / presentation 输出。

### 8.4 未来进入 external 的内容

未来拆分后，以下内容应放入顶层 external 目录：

- 第三方仓库 checkout。
- 外部模板源码。
- 外部 skill 原始结构。
- 未吸收为本项目资产的参考工程。

外部项目进入本仓库前必须先有评估文档，不应因为“看起来有用”就直接进入 `skills/`、`templates/` 或生产代码目录。

## 9. Codex / Claude Code 调用方式

### 9.1 Codex 调用

Codex 适合执行具体输出任务：

1. 先读 `MAP.md`，判断任务属于小红书、Presentation、外部评估还是流程文档。
2. 读取本规范和对应输出包 README。
3. 根据目标建立输出目录。
4. 编写或更新 `index.html`、`README.md`、`post-copy.md` 或 `run-notes.md`。
5. 如需导图，使用浏览器 / Playwright 导出并检查尺寸。
6. 运行相关验证：
   - `python3 scripts/lint_map.py`
   - `python3 -m pytest -q`
   - 图片尺寸检查或浏览器预览检查。
7. 汇报变更，不默认 commit，除非用户明确要求。

### 9.2 Claude Code 调用

Claude Code 更适合承担长链路规划和大型提案组织：

- 把 staging 资料整理成提案 brief。
- 生成 Presentation 页表。
- 规划小红书系列内容矩阵。
- 把外部 skill 评估转成自有 skill 草案。
- 对复杂输出包做结构性重写。

Claude Code 产出的方案仍应落到本规范定义的目录和文件结构中，避免只生成一次性长文。

### 9.3 未来 Skill 形态

后续可把本规范沉淀为自有 `presentation-output-skill` 或 `social-output-skill`。一个正式 skill 至少应包含：

- `SKILL.md`：触发条件、输入、输出、执行步骤、验证要求。
- `references/`：版式规则、配图规则、自检 checklist。
- `assets/`：可复用 HTML 模板或 CSS 片段。
- `scripts/`：可选校验器或导出辅助脚本。

该 skill 应该调用本项目自己的规范，而不是复制第三方仓库作为内部实现。

## 10. 最小验收标准

一个 Output Skill 产物达到可归档状态，必须满足：

- 有明确输出目录。
- 有 `README.md`。
- 有可编辑源文件。
- 有可发布或可演示成品。
- 有输入来源和判断过程记录。
- 有基本自检结果。
- 不包含未说明来源的第三方源码。
- 不包含 token、secret、auth cache、本机私有路径。
- 能被 Git 清晰追踪。

如果它只是一组截图或一个临时 HTML 文件，还不能算正式 Output Skill 产物。

## 11. 下一步

建议优先把“小红书图文生产”和“Presentation Output”分别沉淀成两个轻量自有 skill：

- `xiaohongshu-output-skill`：围绕 4:5 卡片、HTML/CSS、Playwright 导出和发布文案。
- `presentation-output-skill`：围绕 brief、页表、横向 HTML deck、配图槽位、自检和导出。

等这两个 skill 稳定后，再考虑用 Harness Runtime 把它们编排进端到端的 Archive / Deliver 阶段。
