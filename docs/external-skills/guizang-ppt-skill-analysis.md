# guizang-ppt-skill 接入分析：Presentation Output Skill

## 项目简介

- 来源：<https://github.com/op7418/guizang-ppt-skill>
- 项目定位：适配 Claude Code / Codex 等 Agent 环境的网页 PPT Skill，用于生成单文件 HTML 横向翻页 PPT、PPT 配图和多平台封面。
- 读取范围：`README.md`、`SKILL.md`、`assets/`、`references/`、`scripts/validate-swiss-deck.mjs`。
- 许可证：MIT。

该项目不是一个普通 HTML 模板集合，而是一套带工作流约束的 Presentation Output Skill。它把“做一份 PPT”拆成：风格选择、需求澄清、模板拷贝、版式选择、配图生成、自检、浏览器预览、迭代修改。

它内置两套视觉系统：

1. **Style A：电子杂志 × 电子墨水**  
   使用衬线标题、电子墨水质感、WebGL 流体背景和杂志式图文编排，适合叙事、人文、行业观察、个人风格表达。

2. **Style B：瑞士国际主义**  
   使用 Inter / Helvetica 气质、16 列网格、单一高饱和锚点色、直角色块、发丝线和极大字号对比，适合事实、产品、数据、分析、方法论表达。

## 已读取结构

```text
guizang-ppt-skill/
├── README.md
├── README.en.md
├── SKILL.md
├── LICENSE
├── assets/
│   ├── motion.min.js
│   ├── template.html
│   └── template-swiss.html
├── references/
│   ├── checklist.md
│   ├── components.md
│   ├── image-prompts.md
│   ├── layouts.md
│   ├── layouts-swiss.md
│   ├── swiss-layout-lock.md
│   ├── themes.md
│   └── themes-swiss.md
└── scripts/
    └── validate-swiss-deck.mjs
```

核心文件职责：

- `SKILL.md`：主工作流和 Agent 执行协议。
- `assets/template.html`：Style A 电子杂志风单文件 HTML 模板。
- `assets/template-swiss.html`：Style B 瑞士国际主义单文件 HTML 模板。
- `references/layouts.md`：Style A 的 10 种页面布局骨架。
- `references/layouts-swiss.md`：Style B 的 22 种锁定版式。
- `references/swiss-layout-lock.md`：瑞士风硬约束，防止“看起来像 Swiss 但结构已跑偏”。
- `references/image-prompts.md`：PPT 内嵌配图的类型、比例和提示词规则。
- `references/checklist.md`：P0/P1/P2/P3 分级自检清单。
- `scripts/validate-swiss-deck.mjs`：瑞士风版式校验器。

## 核心能力总结

### 1. 单文件 HTML 横向翻页 PPT

项目输出的是浏览器可直接打开的 `index.html`，不依赖 Keynote、PowerPoint 或在线协作工具。它支持键盘、滚轮、触屏、底部圆点和索引式浏览。这个形态适合 Design Data Factory，因为 HTML 文件可以进入 Git、被 diff、被浏览器截图、被归档，也能和生成记录形成可追踪链路。

### 2. 电子杂志风

Style A 的强项是叙事和气质。它更接近“线下分享 / 私享会 / 观点发布”的视觉表达：大标题、引用、图文混排、图片网格、Pipeline、Before / After。对品牌故事、行业观察、案例复盘和个人表达更友好。

### 3. 瑞士国际主义风

Style B 的强项是结构和事实表达。它要求正文页从 `S01-S22` 登记版式中选择，并通过 `data-layout="Sxx"` 标记。它强调网格、左对齐、单一锚点色、直角、发丝线、无阴影、无渐变、无圆角。这对方法论、产品说明、数据汇报、AI 工作流讲解更稳定。

### 4. 多平台封面

README 明确覆盖公众号头图 21:9、公众号分享卡 1:1、小红书 3:4、视频号横版等封面规格。它可以作为“PPT 核心观点 → 多平台传播素材”的延展能力，而不仅是演讲页生成器。

### 5. 配图流程

`references/image-prompts.md` 不是泛泛的生图提示词，而是围绕“图片作为 PPT 内嵌素材”建立规则：

- 先确定版式槽位和比例，再生成图片；
- 生成图不能自带页眉、页脚、标题、页码、角标、署名或装饰边框；
- 中文 deck 的信息图用中文标签，英文 deck 用英文标签；
- Style A 适合纪实照片、杂志风信息图、流程图、系统关系图、截图再设计；
- Style B 适合 21:9 顶部横幅、Swiss Style 信息图、UI 情景图、多图网格素材、极简数据块。

这和当前仓库的 GPT Image / HTML/CSS / Playwright 工作流高度一致。

### 6. 自检 checklist

`references/checklist.md` 是该项目最有价值的部分之一。它不是只列视觉偏好，而是把真实踩坑转成 P0/P1/P2/P3 检查项。尤其是瑞士风部分，会检查：

- 正文页是否使用登记版式；
- 是否缺少 `data-layout`；
- 是否在 SVG 里写可见文字；
- S22 是否绑定 `s22-hero-21x9` 图片槽位；
- 图片是否错误使用 `top center` 裁切；
- 标题、图片、分页安全区、网格 padding 是否跑偏。

这类 checklist 可以直接启发 Design Data Factory 自己的 Presentation Evaluator。

## 适合场景

- 线下分享、行业内部讲话、私享会、Demo Day。
- AI 产品发布、方法论发布、工作流演示。
- 从文章、研究、案例、运行记录中生成一份完整 HTML deck。
- 将御炉品牌升级资料整理成品牌提案、策略提案或内部评审材料。
- 将 Design Data Factory 的运行结果转成“可讲、可演示、可归档”的 Presentation Output。
- 将一份 PPT 的核心观点拆出多平台封面：公众号头图、分享卡、小红书封面、视频号横版封面。

## 不适合场景

- 大段表格数据、财务明细、复杂 BI dashboard。
- 培训课件或知识库课程，信息密度要求过高时不适合。
- 多人实时协作编辑的公司 PPT 流程。
- 需要严格沿用客户 PPT 模板、品牌模板或 Office 动画的场景。
- 需要 `.pptx` 原生格式交付且客户后续要在 PowerPoint 中编辑的场景。
- 未经人工判断就批量生成商业提案。它能提高输出稳定性，但不能替代品牌判断、商业取舍和提案策略。

## 和 ai-design-skill-lab / Design Data Factory 的关系

当前仓库的核心是把设计工作变成可复用、可验证、可追踪的数据流：

```text
brief -> reference -> analysis -> plan -> prompt -> layout -> render -> review -> archive -> reuse
```

`guizang-ppt-skill` 可以放在这条链路的 **Presentation Output** 阶段：

```text
00_Inbox_Staging
  -> 资料清洗 / 判断 / 分类
  -> 30_Patterns 中沉淀方法、版式、提案结构
  -> 90_Runs 中记录一次提案生成过程
  -> docs/<project-or-topic>/ppt/index.html
  -> browser preview / screenshot / export
  -> archive reusable presentation pattern
```

它和当前仓库的关系不是“替换现有 Harness Runtime”，而是补足 **最终可演示输出层**：

- Harness Runtime 负责目标、运行、反馈、归档；
- Obsidian Staging 负责资料入口；
- Patterns 负责沉淀可复用判断和结构；
- Runs 负责记录一次执行过程；
- `guizang-ppt-skill` 负责把结构化内容转成可展示的横向 PPT 和平台封面。

## 对 Design Data Factory 的价值

### 1. 让输出从“文档”变成“可演示资产”

Design Data Factory 目前已经能沉淀图文包、运行记录、Pattern 和 Prompt。`guizang-ppt-skill` 能补上面向会议、客户沟通和公开分享的演示输出。

### 2. 提供 Presentation Output Skill 的参考实现

它示范了一个成熟 Skill 应该包含什么：

- 主 `SKILL.md`；
- 可运行模板；
- 版式库；
- 主题库；
- 配图提示词；
- 自检清单；
- 校验脚本；
- 明确的适用/不适用边界。

这对当前仓库后续自建 `presentation-output` skill 很有参考价值。

### 3. 建立“版式锁定 + 校验”的质量思路

瑞士风的 `S01-S22` 锁定版式尤其值得借鉴。Design Data Factory 后续不应只说“生成一个高级 PPT”，而应该要求：

- 先选择已登记版式；
- 每页声明版式 ID；
- 图片声明槽位；
- 生成后运行校验器；
- checklist 未过不归档。

这比单纯依赖 Agent 审美更可靠。

### 4. 强化多平台分发能力

当前仓库已有小红书 HTML -> PNG 工作流。`guizang-ppt-skill` 的封面生成规则可以帮助把同一套观点转成：

- 横向演讲 deck；
- 公众号头图；
- 小红书封面；
- 视频号封面；
- 分享卡。

这符合 Design Data Factory “一次判断，多处复用”的目标。

## 对御炉品牌提案的价值

御炉品牌升级类任务通常同时需要：

- 品牌洞察；
- 文化叙事；
- 门头 / 空间 / 菜单 / 内容传播分析；
- 经营逻辑；
- 客户可读的提案结构。

`guizang-ppt-skill` 可作为御炉提案的演示层：

- **Style A 电子杂志风**：适合讲御炉的品牌故事、非遗叙事、老字号语境、空间体验、消费者场景。
- **Style B 瑞士国际主义风**：适合讲品牌诊断、传播路径、内容矩阵、门店指标、阶段计划、执行路线图。

推荐组合：

```text
封面 / 品牌故事 / 消费者场景：Style A
诊断 / 策略 / 路线图 / 执行清单：Style B
```

但一份 deck 内不建议混用两套模板。更稳的做法是按用途拆成两个输出：

- `docs/yulu-brand-upgrade/proposal-magazine/index.html`
- `docs/yulu-brand-upgrade/proposal-strategy/index.html`

前者面向情绪与品牌气质，后者面向决策与执行。

## 对小红书内容生产的价值

当前仓库的小红书生产方式是 HTML/CSS -> Playwright -> PNG。`guizang-ppt-skill` 可以补充两类能力：

1. **从 PPT 核心观点拆小红书图文**
   - 一份 10-20 页横向 deck 可以沉淀出 3-5 张小红书竖图；
   - 每一页 deck 的大观点可转成一张 4:5 卡片；
   - `checklist.md` 的自检思路可迁移到小红书导出检查。

2. **从小红书选题反向生成分享 deck**
   - 小红书图文用于传播；
   - 横向 HTML PPT 用于直播、线下课、客户沟通；
   - 两者共享同一套 Pattern、Prompt 和素材判断。

推荐内容链路：

```text
小红书选题
  -> 5 张卡片讲清一个方法
  -> 扩写成 10 页 deck
  -> deck 中的封面 / 关键页反向产出多平台封面
```

## 推荐接入方式

### 是否作为全局 Claude Skill 安装

建议：**可以作为全局 Claude Skill 安装，但不要在本次执行中安装。**

原因：

- 该项目本身就是 Claude Code / Codex Agent Skill 形态；
- 全局安装后更适合在需要制作 PPT 时按触发词调用；
- 它依赖完整的 `assets/`、`references/`、`scripts/` 结构，作为全局 skill 使用比拆散复制更稳；
- 当前任务目标是评估和接入建议，不是安装。

建议未来安装位置：

```text
~/.claude/skills/guizang-ppt-skill/
```

如果要给 Codex 使用，不建议直接把它塞进当前仓库 `skills/`，而是先沉淀本分析文档，再根据项目自己的输出规范仿写一个轻量自有 skill。

### 是否需要复制到当前仓库

建议：**不要复制完整第三方仓库到当前仓库。**

原因：

- 外部仓库会持续更新，复制进来容易形成过期 fork；
- 完整模板、动效、校验脚本和 references 体积较大，不应混入本项目核心资产；
- 当前仓库更应该沉淀“如何使用、如何接入、如何评价”的方法，而不是 vendor 第三方源码；
- 本项目只需要保留分析文档和未来自有 skill 的设计方向。

可选做法：

- 临时阅读：克隆到 `/private/tmp` 或 `references/guizang-ppt-skill/`，但默认不提交第三方源码。
- 长期引用：在文档中保留 GitHub URL、读取范围和推荐触发方式。
- 真正吸收：只吸收可复用方法，例如版式锁定、图片槽位、自检 checklist、输出目录协议。

### 输出文件应该放到哪里

建议根据输出用途放入 `docs/` 下的具体项目目录，而不是放进 `skills/` 或 `templates/`：

```text
docs/<topic-or-project>/ppt/
├── README.md
├── index.html
├── images/
├── exports/
└── run-notes.md
```

如果是御炉品牌提案：

```text
docs/yulu-brand-upgrade/presentation/
├── README.md
├── index.html
├── images/
├── exports/
└── run-notes.md
```

如果是小红书系列扩展成公开课或直播 deck：

```text
docs/<xiaohongshu-topic>/presentation/
├── README.md
├── index.html
├── images/
├── exports/
└── post-derived-outline.md
```

其中：

- `index.html` 是单文件横向翻页 PPT；
- `images/` 放配图素材；
- `exports/` 放导出的封面、长图或关键页截图；
- `run-notes.md` 记录输入来源、风格选择、版式选择、自检结果和后续迭代。

### 如何与 00_Inbox_Staging、30_Patterns、90_Runs 形成闭环

推荐闭环：

```text
1. 00_Inbox_Staging
   收集文章、微信链接、品牌资料、客户访谈、旧 PPT、图片说明。

2. 资料判断
   Agent 从 staging 中判断哪些资料进入项目参考，哪些可转为提案素材。

3. 30_Patterns
   沉淀可复用结构：
   - 品牌提案叙事弧；
   - 御炉品牌升级页面结构；
   - 小红书图文转 deck 的结构；
   - PPT 版式选择规则；
   - 图片槽位与提示词规则。

4. 90_Runs
   每次生成 presentation 时记录：
   - 输入资料；
   - 使用的 Pattern；
   - 风格 A 或 B；
   - 页码 -> layout -> 用途 -> 图片槽位；
   - 自检 checklist；
   - 预览和导出结果。

5. docs/<project>/presentation/
   保存最终 HTML PPT、图片、导出图、README 和 run-notes。

6. Archive / Reuse
   如果某次 deck 结构表现稳定，把其叙事结构、页面选择和自检经验沉淀回 30_Patterns。
```

这样，`guizang-ppt-skill` 不是孤立的“做 PPT 工具”，而是 Design Data Factory 的输出节点。

## 推荐使用流程

### A. 资料进入

先把原始资料放入 `00_Inbox_Staging`，例如：

```bash
./scripts/capture.sh wechat "御炉品牌参考文章" "文章内容或链接"
```

不要直接从零做 PPT。先确认资料是否值得进入品牌提案或方法论沉淀。

### B. 形成提案 brief

在 `docs/<project>/presentation/run-notes.md` 中记录：

- 目标受众；
- 使用场景；
- 分享时长；
- 是否有旧 PPT / 文章 / 图片；
- 推荐风格；
- 主题色；
- 必须出现和不能出现的内容。

### C. 选择风格

- 讲故事、讲品牌气质、讲空间体验：优先 Style A。
- 讲策略、数据、路线图、方法论：优先 Style B。

### D. 规划页表

生成前先列：

```text
页码 -> 版式 -> 目的 -> 图片槽位 -> 来源资料
```

瑞士风必须写 `data-layout="Sxx"`，并在完成后运行：

```bash
node scripts/validate-swiss-deck.mjs path/to/index.html
```

### E. 配图

配图必须先服务版式槽位：

- S22 主图：21:9；
- S15/S16 多图：统一 21:9 或 16:10；
- 截图再设计：16:10；
- 信息图：16:9 或 16:10。

图片作为 PPT 素材，不要生成带页眉、页脚、标题栏、页码、角标的“伪 slide”。

### F. 自检和归档

至少检查：

- 浏览器能直接打开；
- 翻页正常；
- 图片路径正常；
- 中文没有溢出；
- 标题层级清晰；
- 图片没有裁掉关键内容；
- 瑞士风 validator 通过；
- `README.md` 说明输入、输出、风格、导出方式；
- `run-notes.md` 说明本次判断过程。

## 后续可仿写的自有 Skill 方向

### 1. `presentation-output-skill`

面向当前仓库自有的 Presentation Output Skill，不直接复制 guizang 模板，而是定义本项目的输出协议：

- 输入：brief、资料、Pattern、目标受众、发布场景；
- 输出：`docs/<project>/presentation/index.html`；
- 过程：页表规划、风格选择、配图槽位、自检、导出；
- 归档：将稳定结构写回 `references/30_Patterns`。

### 2. `proposal-from-staging-skill`

从 `00_Inbox_Staging` 读取资料，生成品牌提案大纲和页面结构：

```text
staging notes -> insight clusters -> proposal narrative -> slide table -> presentation output
```

适合御炉、餐饮品牌、空间升级、内容传播策略。

### 3. `xiaohongshu-to-deck-skill`

把 3-5 张小红书图文扩展成 8-12 页横向分享 deck：

- 小红书负责传播；
- deck 负责讲解；
- 两者共享标题、观点、步骤和检查清单。

### 4. `deck-to-multiplatform-cover-skill`

从 deck 中提取核心观点，生成：

- 公众号头图；
- 分享卡；
- 小红书封面；
- 视频号横版封面。

这个方向可复用 guizang 的多平台封面思想，但应采用当前仓库自己的 HTML/CSS -> PNG 导出规范。

### 5. `presentation-evaluator-skill`

把 `checklist.md` 的思路转成本项目自有的演示输出评估器：

- 页面结构是否清晰；
- 每页是否只有一个任务；
- 图片是否服务内容；
- 中文是否可读；
- 是否有可复用 Pattern；
- 输出是否有 README 和 run-notes；
- 是否能被 Git 和 docs 追踪。

## 接入结论

推荐把 `guizang-ppt-skill` 作为 **外部 Presentation Output Skill 参考与可选全局 Claude Skill**，但不要把完整第三方仓库复制进当前项目。

对当前 Design Data Factory 来说，最有价值的不是直接拿它的模板，而是吸收它的工作流结构：

```text
风格选择 -> 版式库 -> 图片槽位 -> 配图提示词 -> 自检 checklist -> 校验脚本 -> 输出归档
```

短期建议：

- 不安装；
- 不复制源码；
- 保留本分析文档；
- 未来需要做御炉品牌提案或 AI Runtime 分享 deck 时，可临时使用全局 Claude Skill 或外部引用生成 deck；
- 生成结果放到 `docs/<project>/presentation/`，运行过程写入 `references/90_Runs`，可复用结构沉淀到 `references/30_Patterns`。

长期建议：

- 仿写一个当前仓库自己的 `presentation-output` skill；
- 只借鉴方法，不 vendor 第三方仓库；
- 将 Presentation Output 纳入 Harness Runtime 的 Archive / Pattern 闭环。
