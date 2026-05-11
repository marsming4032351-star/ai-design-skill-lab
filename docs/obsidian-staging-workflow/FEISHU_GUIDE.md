# Obsidian Staging 资料收集使用指南

## 这个功能解决什么问题

Obsidian Staging 工作流解决的是“看到有价值资料时，先稳定收进系统”的问题。

日常设计工作里，资料经常散落在微信文章、小红书案例、GitHub 项目、品牌灵感、提示词和临时聊天记录里。如果只靠收藏夹、截图或聊天转发，后续很难知道：

- 资料从哪里来；
- 当时为什么觉得它有价值；
- 它适合品牌案例、设计参考、工具参考还是提示词候选；
- 它是否和御炉项目有关；
- 后续应该整理进哪个正式资产目录。

这个工作流先不追求一步到位归档，而是把资料统一写入 `00_Inbox_Staging/`，生成带 YAML frontmatter 的 Obsidian Markdown。后续再由人或 Agent 做判断、补充和归档。

## 在 Design Data Factory 中的定位

Design Data Factory 的核心是把设计经验变成可复用资产。Obsidian Staging 是这条链路里的入口层：

```text
外部资料 -> 00_Inbox_Staging -> 人工确认 -> 正式资产 / 项目参考 / Prompt / Pattern
```

它的职责不是替代判断，也不是自动抓取全网内容，而是先把资料变成结构化、可追踪、可复查的记录。

当前版本是本地 dry-run：

- 不联网；
- 不调用微信、小红书或 GitHub API；
- 不自动抓网页正文；
- 只根据输入文本和来源标签做规则分类；
- 默认输出到 `00_Inbox_Staging/`。

## 外部资料进入系统的流程

1. 看到一条值得保留的资料。
2. 复制标题和正文摘要、链接或说明。
3. 用快捷命令写入 staging。
4. 系统生成 Markdown note，并自动写入 `title`、`source`、`material_type`、`asset_type`、`project`、`tags` 等字段。
5. 后续人工检查分类是否正确。
6. 有价值的资料再进入正式资产目录、项目参考库或方法论沉淀。

## 快捷命令怎么用

最重要的日常入口是：

```bash
./scripts/capture.sh wechat "文章标题" "文章内容或链接"
```

三个参数分别是：

- `wechat`：来源标签，也可以换成 `xiaohongshu`、`github`、`manual-note` 等短标签；
- `"文章标题"`：生成 note 的标题；
- `"文章内容或链接"`：原始资料，可以是链接、正文、摘要或你自己的描述。

快捷脚本内部调用的是：

```bash
python3 scripts/obsidian_capture.py \
  --input "文章内容或链接" \
  --title "文章标题" \
  --source "wechat" \
  --out 00_Inbox_Staging
```

原 Python 命令仍然可用，适合需要显式指定输出目录或后续扩展参数时使用。

## 微信文章怎么收集

微信文章可以收链接，也可以收正文摘要。

```bash
./scripts/capture.sh wechat "北京老字号案例" "这是一篇关于北京老字号升级的微信文章"
```

如果只复制到了链接，也可以这样：

```bash
./scripts/capture.sh wechat "某公众号文章标题" "https://mp.weixin.qq.com/s/example"
```

当前版本不会自动抓取微信正文，所以更推荐把关键摘要一起放进第三个参数。

## 小红书案例怎么收集

小红书案例适合收集选题、封面结构、评论区反馈、图文节奏和品牌表达方式。

```bash
./scripts/capture.sh xiaohongshu "小红书老字号翻新案例" "案例观察：标题强调老字号升级，封面突出门头对比，评论区集中讨论排队体验和空间记忆。"
```

如果它是视觉参考，内容里可以写清楚版式、配色、字体、封面信息层级等关键词，系统会更容易识别为 `design_reference`。

## GitHub 项目怎么收集

GitHub 项目直接放仓库 URL 即可。

```bash
./scripts/capture.sh github "Beautiful HTML Templates" "https://github.com/zarazhangrui/beautiful-html-templates"
```

只要内容中包含 `github.com/`，系统会自动标记为：

```yaml
material_type: github_tool
asset_type: reference
```

这一步只是把项目放入 staging，不代表要把第三方源码提交进主仓库。是否克隆、是否放入 `references/`、是否写评估文档，仍然需要后续判断。

## 御炉品牌灵感怎么收集

御炉相关资料可以来自微信、小红书、门头照片、菜单观察、北京老字号案例、非遗叙事、餐饮运营和空间动线。

```bash
./scripts/capture.sh wechat "御炉门头灵感" "北京烤鸭老字号通过非遗叙事、门头识别和菜单结构重塑餐饮品牌体验。"
```

只要内容或来源里出现以下关键词之一，系统会自动写入 `project: yulu`：

```text
御炉、御爐、yulu、御炉餐饮、御爐餐飲、烤鸭、北京、非遗、老字号
```

同时会标记：

```yaml
asset_type: brand_reference
tags:
  - brand-reference
  - project/yulu
```

## 生成的 Markdown 会放在哪里

默认输出目录是：

```text
00_Inbox_Staging/
```

生成文件名大致形如：

```text
20260510-145622-note-c19c172bf6.md
```

Markdown 内容包含：

- YAML frontmatter；
- 自动判断结果；
- 原始资料；
- 后续处理建议。

这让资料能被 Obsidian、脚本、Agent 和后续归档工具共同读取。

## project: yulu 的自动识别规则

当前规则在 `shared/obsidian_staging.py` 中维护。只要输入内容或来源包含以下关键词，就会识别为御炉项目：

- `御炉`
- `御爐`
- `yulu`
- `御炉餐饮`
- `御爐餐飲`
- `烤鸭`
- `北京`
- `非遗`
- `老字号`

识别后写入：

```yaml
project: yulu
asset_type: brand_reference
```

如果同一条资料同时包含 Prompt 关键词，Prompt 规则优先，`asset_type` 会变成 `prompt_candidate`。

## asset_type 的自动分类规则

`asset_type` 用来判断资料后续应该怎么处理。

当前规则优先级：

1. 如果包含 `prompt`、`提示词`、`system prompt`、`指令`、`Midjourney`、`Lovart`、`生图`，标记为 `prompt_candidate`。
2. 如果包含御炉相关关键词，标记为 `brand_reference`。
3. 如果包含 `方法论`、`框架`、`流程`、`工作流`、`设计原则`、`判断标准`、`沉淀`、`先分析`、`提案结构` 等，标记为 `pattern_candidate`。
4. 其它资料先标记为 `reference`。

`material_type` 则更偏资料类型，例如：

- `brand_case`：品牌案例；
- `design_reference`：设计参考；
- `restaurant_ops`：餐饮运营；
- `github_tool`：GitHub 工具；
- `prompt`：提示词；
- `image_asset`：图片资产。

## 日常使用建议

- 先收集，不急着归档。看到资料时先进入 `00_Inbox_Staging/`，避免资料散失。
- 标题写人能看懂的名字，不要只写“收藏”“参考”“文章”。
- 第三个参数尽量写摘要，不只放链接。当前版本不会自动抓正文。
- 御炉资料尽量保留品牌、门头、菜单、空间、北京、老字号、非遗、烤鸭等信号。
- Prompt 和生图工作流要写清楚适用场景，不要只保存一句孤立提示词。
- GitHub 项目进入 staging 后，仍需按仓库规则先评估，再决定是否克隆到 `references/`。
- 定期清理 `00_Inbox_Staging/`：无价值资料删除，有价值资料补充判断后转成正式资产。

## 下一阶段 staging_to_asset 规划

下一阶段建议新增 `staging_to_asset`，把 staging note 从“临时收集”推进到“正式资产”。

规划方向：

- 读取 `00_Inbox_Staging/*.md` 的 frontmatter；
- 根据 `project`、`material_type`、`asset_type` 推荐目标目录；
- 对 `project: yulu` 的资料推荐进入御炉项目资料或品牌参考目录；
- 对 `prompt_candidate` 推荐进入 Prompt 候选库；
- 对 `pattern_candidate` 推荐进入方法论或工作流文档；
- 对 `github_tool` 推荐进入外部项目评估流程；
- 归档前保留人工确认步骤；
- 写入移动记录，避免资料被移动后失去来源。

这一步完成后，Design Data Factory 会形成更完整的资料生命周期：

```text
capture -> staging -> review -> asset -> reuse
```
