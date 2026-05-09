# 当前可用 Skills 使用指南

日期：2026-05-07

这份文档列出当前环境中可用的 skills，并说明它们适合什么场景、怎么触发、使用时要注意什么。

## 使用方式总览

你通常不需要手动运行 skill。只要你的需求命中某个 skill 的场景，我会先读取对应的 `SKILL.md`，再按它的流程执行。

你也可以显式指定：

- “用 `markitdown` 把这个 PPT 转成 Markdown”
- “用 `playwright` 打开网页检查”
- “用 `lark-doc` 创建飞书文档”
- “用 `superpowers:brainstorming` 先头脑风暴”

通用规则：

- **创意、功能、方案设计前**：优先用 `superpowers:brainstorming`。
- **代码、调试、测试、提交前**：优先用本仓库的 `karpathy-guidelines` 和相关 Superpowers。
- **飞书/Lark 操作**：优先用对应 `lark-*` skill。
- **Obsidian 文件/库操作**：优先用 `obsidian-*` skill。
- **PDF、PPT、Word、Excel 等文件转 Markdown**：优先用 `markitdown`。
- **网页清洗成 Markdown**：优先用 `defuddle`。
- **真实浏览器检查网页/UI**：优先用 `playwright`。

## 系统与通用工具 Skills

| Skill | 使用场景 | 使用方法 |
|---|---|---|
| `imagegen` | 生成或编辑位图视觉资产，例如照片、插画、纹理、精灵图、透明背景素材、视觉变体。 | 当需要 AI 生成图片或基于参考图改图时触发。若更适合用 SVG/HTML/CSS/代码绘制，则不用它。 |
| `openai-docs` | 查询 OpenAI API、模型、ChatGPT、SDK、提示词迁移等官方最新文档。 | 当问题涉及 OpenAI 产品如何使用时触发；优先查官方文档，必要时只浏览 OpenAI 官方域名。 |
| `plugin-creator` | 创建 Codex 插件目录、`.codex-plugin/plugin.json`、插件占位结构或 marketplace 条目。 | 当你要“新建插件”“发布/整理插件结构”时触发。 |
| `skill-creator` | 创建或更新 Codex skill。 | 当你要“写一个新 skill”“改一个已有 skill”“让某套流程变成 skill”时触发。 |
| `skill-installer` | 列出可安装 skills，或从 curated list/GitHub 安装 skill。 | 当你要“安装 skill”“看看有哪些可安装 skill”时触发。 |
| `defuddle` | 从网页提取干净 Markdown，去掉导航、广告、杂项。 | 当你给 URL 让我阅读、分析、总结网页时触发；`.md` URL 不用它。 |
| `markitdown` | 将 PDF、PPTX、DOCX、XLSX、图片、音频、HTML、CSV、JSON、XML、ZIP 等转成 Markdown。 | 当你给本地文档让我读取、整理、抽取内容时触发。 |
| `playwright` | 用真实浏览器打开网页、截图、表单操作、UI 检查、调试页面。 | 当需要“打开网页看看”“截图验证”“检查 HTML/PDF 导出效果”时触发。 |
| `json-canvas` | 创建或编辑 Obsidian JSON Canvas `.canvas` 文件、节点、边、分组和连接。 | 当你提到 Canvas、脑图、流程图、Obsidian `.canvas` 时触发。 |

## Obsidian Skills

| Skill               | 使用场景                                                                     | 使用方法                                                       |
| ------------------- | ------------------------------------------------------------------------ | ---------------------------------------------------------- |
| `obsidian-cli`      | 读写 Obsidian vault、搜索笔记、管理任务/属性、调试插件和主题。                                  | 当你让我“查 Obsidian 笔记”“创建/移动/搜索 vault 内容”“调试 Obsidian 插件”时触发。 |
| `obsidian-markdown` | 编写 Obsidian Flavored Markdown，包括 wikilink、embed、callout、frontmatter、标签等。 | 当你让我写或改 Obsidian 笔记、模板、知识库 Markdown 时触发。                   |
| `obsidian-bases`    | 创建或编辑 Obsidian Bases `.base` 文件，配置表格/卡片视图、过滤、公式、汇总。                      | 当你提到 Obsidian Bases、数据库视图、表格视图、卡片视图、过滤公式时触发。               |

## 飞书 / Lark Skills

| Skill | 使用场景 | 使用方法 |
|---|---|---|
| `lark-shared` | 飞书 CLI 初始化、登录、权限、scope、身份切换、Permission denied 处理。 | 首次配置 Lark、遇到权限问题、需要切换 user/bot 身份时触发。 |
| `lark-doc` | 创建、读取、编辑飞书云文档，从 Markdown 创建文档，搜索云空间文档。 | 当你要“创建飞书文档”“更新文档”“搜索文档”“插入图片/文件”时触发。 |
| `lark-drive` | 管理飞书云空间文件和文件夹，上传、下载、复制、移动、删除、权限、评论。 | 当你要整理云盘、上传/下载文件、管理权限或评论时触发。 |
| `lark-sheets` | 创建和操作飞书电子表格，读写单元格、追加行、查找、导出。 | 当你要处理电子表格数据、写入表头/行、导出表格时触发。 |
| `lark-base` | 操作飞书多维表格 Base：建表、字段、记录、视图、公式、查找引用、仪表盘等。 | 当需求涉及 Base、字段设计、公式字段、跨表计算、记录管理时触发。 |
| `lark-calendar` | 飞书日历与会议日程：查看日程、创建/更新会议、忙闲查询、推荐时间。 | 当你要查日程、建会议、邀请参会人、找空档时触发。 |
| `lark-contact` | 查询组织架构、人员信息、搜索员工 open_id、邮箱、手机号。 | 当你要找同事、查联系人、查部门结构时触发。 |
| `lark-im` | 飞书即时通讯：发消息、回复、搜聊天、群成员管理、上传下载图片/文件。 | 当你要发飞书消息、查聊天记录、管理群聊或下载群文件时触发。 |
| `lark-mail` | 飞书邮箱：写草稿、发邮件、回复、转发、搜索邮件、附件、标签和联系人。 | 当你提到邮件、收件箱、草稿、回复、转发、下载附件时触发。 |
| `lark-task` | 飞书任务：创建待办、查看任务、更新状态、拆子任务、分配协作成员。 | 当你要创建/管理待办、项目清单、任务分配时触发。 |
| `lark-minutes` | 飞书妙记：获取妙记信息、AI 总结、待办、章节。 | 当你提供 `/minutes/<token>` 链接或要整理妙记内容时触发。 |
| `lark-vc` | 查询已结束会议记录、获取会议纪要、总结、待办、章节、逐字稿。 | 当你要查“昨天/上周开过的会议”“整理会议纪要”时触发；未开始会议用 `lark-calendar`。 |
| `lark-whiteboard` | 在飞书云文档中绘制图表，创建飞书画板、架构图、流程图、思维导图等。 | 当你要“在飞书里画图/流程图/架构图/白板”时触发。 |
| `lark-wiki` | 管理飞书知识库空间和节点，查询、创建、移动、复制知识库文档。 | 当你要在飞书知识库里查找、创建、组织文档节点时触发。 |
| `lark-event` | 通过 WebSocket 实时监听飞书事件，输出消息/通讯录/日历变更等 NDJSON。 | 当你要实时监听飞书事件或搭建事件驱动流程时触发。 |
| `lark-openapi-explorer` | 查找并调用 lark-cli 未封装的原生飞书 OpenAPI。 | 当现有 `lark-*` skill 或 CLI 命令不能满足需求时触发。 |
| `lark-skill-maker` | 创建 lark-cli 自定义 Skill，封装原子 API 或多步流程。 | 当你想把某个飞书操作做成可复用 skill 时触发。 |
| `lark-workflow-meeting-summary` | 汇总某个时间范围内的会议纪要，生成结构化报告。 | 当你要会议周报、月度会议回顾、指定时间段会议总结时触发。 |
| `lark-workflow-standup-report` | 汇总日程和未完成任务，生成今天/明天/本周安排摘要。 | 当你要“今天安排”“明天站会材料”“本周日程待办摘要”时触发。 |

## 开发流程 Superpowers

这些是过程类 skills，主要约束我如何规划、执行、验证开发工作。

| Skill                                        | 使用场景                        | 使用方法                                  |
| -------------------------------------------- | --------------------------- | ------------------------------------- |
| `superpowers:using-superpowers`              | 每次开始任务时检查是否有适用 skill。       | 作为总入口规则，提醒我先看 skills，再行动。             |
| `superpowers:brainstorming`                  | 所有创意、功能、设计、行为改动前的头脑风暴和方案确认。 | 当你让我“设计/策划/做一个功能/改行为”时触发；先了解上下文，再提方案。 |
| `superpowers:writing-plans`                  | 根据已确认的规格写详细实施计划。            | 当已有 spec/方案，需要拆成具体任务和文件步骤时触发。         |
| `superpowers:executing-plans`                | 按已写好的实施计划逐步执行。              | 当你让我“按计划执行”或已有计划文档时触发。                |
| `superpowers:subagent-driven-development`    | 用多个独立子任务并行推进开发。             | 当任务可拆成互不冲突的实现块，且允许使用 subagent 时触发。    |
| `superpowers:dispatching-parallel-agents`    | 面对多个独立任务时并行派发 agent。        | 当至少有两个可独立处理的工作块时触发；需用户允许使用 subagents。 |
| `superpowers:systematic-debugging`           | 遇到 bug、测试失败、异常行为时系统化调试。     | 当出现失败、报错、行为不符合预期时触发；先定位原因再修。          |
| `superpowers:test-driven-development`        | 实现功能或修 bug 前使用 TDD。         | 当要写代码改行为时触发；先写失败测试，再实现，再验证。           |
| `superpowers:verification-before-completion` | 完成前必须做验证，不能只凭感觉说完成。         | 当我要宣称修好、通过、完成、可交付前触发。                 |
| `superpowers:requesting-code-review`         | 完成主要实现后请求代码审查。              | 当实现较大或合并前需要质量检查时触发。                   |
| `superpowers:receiving-code-review`          | 收到代码审查意见后处理反馈。              | 当你给 review 意见或我收到审查反馈时触发；先验证意见再改。     |
| `superpowers:finishing-a-development-branch` | 开发分支完成后决定合并、PR、清理等。         | 当实现和测试都完成，要收尾集成时触发。                   |
| `superpowers:using-git-worktrees`            | 需要隔离工作区时创建 git worktree。    | 当任务大、当前工作区脏、需要隔离开发时触发。                |
| `superpowers:writing-skills`                 | 编写、修改、验证 skills。            | 当你要创建/改进 skill 本身时触发。                 |

## 本仓库专用 Skill

| Skill | 使用场景 | 使用方法 |
|---|---|---|
| `karpathy-guidelines` | 本仓库默认开发规则，用于代码、调试、重构、测试、提交、发布等任务。 | 当我修改 `scripts/`、`shared/`、`tests/`，或做非平凡代码/文档提交时触发；强调小改动、可验证、保护用户已有改动。 |

## 推荐用法示例

### 读取和整理文件

```text
把这个 PPT 转成 Markdown 并总结重点
```

会触发：

- `markitdown`

### 做品牌策划或设计方案

```text
帮我头脑风暴一个品牌策划案
```

会触发：

- `superpowers:brainstorming`

### 做网页或 PPT 效果检查

```text
打开这个 HTML 看看效果，并截图验证
```

会触发：

- `playwright`

### 操作飞书文档

```text
把这份 Markdown 发到飞书文档里
```

会触发：

- `lark-doc`
- 如遇权限或登录问题，再触发 `lark-shared`

### 查 Obsidian 笔记

```text
在我的 Obsidian 里查一下聚贤堂相关笔记
```

会触发：

- `obsidian-cli`
- 如需要写 Obsidian 格式，再触发 `obsidian-markdown`

### 调试代码

```text
这个测试失败了，帮我修
```

会触发：

- `superpowers:systematic-debugging`
- `superpowers:test-driven-development`
- `superpowers:verification-before-completion`
- `karpathy-guidelines`

## 文件路径索引

主要 skill 存放位置：

- 系统与通用工具：`/Users/ming/.codex/skills/`
- Superpowers：`/Users/ming/.codex/superpowers/skills/`
- 飞书/Lark：`/Users/ming/.agents/skills/`
- 本仓库规则：`/Users/ming/ai-design-skill-lab/.codex/skills/`

