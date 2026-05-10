# Beautiful HTML Templates 评估

评估对象：`https://github.com/zarazhangrui/beautiful-html-templates`

本次已克隆到：

- `references/beautiful-html-templates/`

评估读取文件：

- `references/beautiful-html-templates/README.md`
- `references/beautiful-html-templates/AGENTS.md`
- `references/beautiful-html-templates/index.json`
- 若干候选模板的 `template.json` / `template.html`

## 结论

适合作为 `ai-design-skill-lab` 的外部 HTML 模板参考库。用于 PPT / HTML deck 时，可以沿用模板原来的横向比例、翻页结构和导航 runtime；用于小红书 PNG 卡片时，更适合定位为“视觉系统与版式语法参考”，不建议直接把模板原样作为小红书成品源文件。

原因：

- 优点：模板库结构清晰，`index.json` 有可机器读取的模板元数据；每个模板有独立 HTML、截图、模板说明，便于 Agent 基于 brief 做模板推荐。
- 优点：模板覆盖品牌提案、Founder Pitch、咨询交付、研究报告、投资人更新、双语 EN/CN deck 等场景，和当前项目的品牌策划 / 方法论内容高度相关。
- 优点：MIT 许可，适合本项目作为参考、改造和二次创作的设计资产来源。
- 注意：模板主要面向 HTML slide deck，默认是全屏浏览器演示逻辑；做 PPT / deck 时这正是优势，可以保留原比例使用。
- 风险：当前小红书工作流需要 1080 x 1350、4:5、PNG 卡片输出，不能直接套用模板原比例。
- 风险：AGENTS.md 强调保留字体、色彩、网格、装饰和导航 runtime。对 PPT / deck 而言应该保留；对小红书卡片而言，导航 runtime 通常不需要，应抽取视觉规则而不是照搬整套 deck runtime。
- 风险：部分模板使用 Google Fonts、全屏 viewport、键盘翻页脚本或外部字体资源，最终导 PNG 时需要检查离线可复现性、字体加载和中文字体 fallback。

## 模板选择机制

这个库的核心入口是 `index.json`。文件包含：

- `schema_version`
- `generated_at`
- `template_count`
- `templates[]`

每个模板记录包括：

- `slug`：模板目录名，例如 `neo-grid-bold`、`blue-professional`、`signal`。
- `name` / `tagline`：展示名称和一句话视觉描述。
- `mood`：情绪关键词，例如 confident、warm、editorial、trustworthy。
- `occasion`：适用场合示例，例如 founder pitch、brand deck、investor update。
- `tone`：表达气质，例如 polished、graphic、literary、design-led。
- `formality`：正式程度，low 到 high。
- `density`：信息密度，low / medium / high。
- `scheme`：light / dark / mixed。
- `best_for`：适合什么“感觉”和使用场景。
- `avoid_for`：不适合什么语境。
- `slide_count`：模板示例页数量。

AGENTS.md 的选择流程是：

1. 先问用户两个问题：使用场合和想要的 mood / vibe。
2. 读取 `index.json`，用 `mood`、`tone`、`best_for`、`formality`、`density`、`scheme` 做匹配。
3. 选出 3 个有明显差异的候选模板，而不是只选同一种风格。
4. 为 3 个候选模板各做一个标题页预览，让用户比较真实内容落在模板里的效果。
5. 用户选定后，复制该模板完整目录，替换内容；如果缺少某种布局，就在同一模板的字体、颜色、网格、装饰语法内扩展。

这个机制对当前项目有价值：它不是按行业硬匹配，而是按“场合 + 气质 + 信息密度 + 正式程度”匹配，适合我们做小红书方法论图文、品牌提案和路演材料时的设计决策。

## 与当前小红书工作流的关系

先区分两个使用场景：

- PPT / HTML deck：可以使用模板原来的比例、页级结构、翻页脚本和全屏浏览器演示方式。
- 小红书图文卡片：需要改成 1080 x 1350、4:5、PNG 输出。

当前项目已有的小红书包通常采用：

1. 写 `index.html` 作为可编辑源文件。
2. 每张卡片是 1080 x 1350、4:5 的 HTML section。
3. 用 HTML/CSS 叠加中文排版、信息结构和图片资产。
4. 用 Playwright 打开页面、截图导出 PNG。
5. 输出 `cards/*.png` 和 `post-copy.md`。

`beautiful-html-templates` 可以接入在第 1-3 步之前，作为模板推荐和视觉系统提取层：

1. 根据内容 brief 读取 `references/beautiful-html-templates/index.json`。
2. 按小红书内容类型选择 3 个候选模板。
3. 不直接复制完整 deck 成品，而是读取候选模板的 `template.html` / `template.json`，抽取：
   - 字体层级
   - 色彩变量
   - 网格节奏
   - 标题 / 数据 / 对比 / 流程布局语法
   - 装饰元素风格
4. 在新的小红书包目录中创建 4:5 HTML 卡片，例如 `docs/<post-name>/index.html`。
5. 将模板的横向 slide 布局改写成固定卡片画布：
   - `.card { width: 1080px; height: 1350px; }`
   - 每页一个 `section.card`
   - 控制中文标题、正文、编号、页脚和主视觉不溢出
6. 使用 Playwright 设置 1080 x 1350 viewport，对每个 `#card-NN` 截图。
7. 输出 PNG 到 `cards/`，再人工或浏览器检查文字截断、字体加载、图片遮挡。

建议新增一个轻量接入规范，而不是把模板库纳入运行时代码：

- `references/beautiful-html-templates/`：外部参考库，只读。
- `docs/<post-name>/index.html`：基于某个模板风格改造的小红书源文件。
- `docs/<post-name>/README.md`：记录使用的模板 slug、改造点、截图规格。
- `cards/*.png`：Playwright 导出的发布图。

## 接入注意事项

- 保留模板的视觉 DNA，但不要保留不必要的 deck navigation runtime。
- 任何候选模板都必须先做 4:5 适配，不要把 16:9 / full viewport deck 直接截图成小红书图。
- 字体需要重点检查。模板多使用 Google Fonts，中文内容应指定可靠中文字体 fallback，例如 `Noto Sans SC`、`PingFang SC`、`Microsoft YaHei`。
- 小红书卡片通常需要更高信息压缩和更强首屏标题。低密度模板如 `bold-poster` 适合封面和金句页，不适合承载长段说明。
- 高密度模板如 `neo-grid-bold`、`signal`、`monochrome` 更适合方法论拆解、矩阵、流程、对比、检查清单。
- 每次使用模板时应在 README 里注明来源和 MIT license，保留必要版权信息。

## 三类内容的模板建议

### 1. 小红书方法论图文

推荐模板：`neo-grid-bold`

适用理由：

- `density: high`，适合步骤、矩阵、对比、流程图和检查清单。
- 气质是 confident / punchy / editorial / modern，适合“技术流方法论”和“可收藏教程”。
- `best_for` 明确提到 stat-heavy slides、comparisons、process flows，和小红书知识卡片很匹配。

使用方式：

- 用它的强网格、粗标题、编号、对比模块做 5 张以内卡片。
- 封面用大标题 + 一句核心判断；中间页用 3-5 步流程；末页用 checklist / formula。
- 注意 neon yellow 不宜过量，中文长句需要压短。

备选：`monochrome`。适合更克制的研究札记、清单、深度教程。

### 2. 品牌提案

推荐模板：`bold-poster`

适用理由：

- `occasion` 包含 brand manifesto、creative-led pitch、founder vision deck。
- 强海报感适合品牌主张、定位语、品牌世界观、核心概念页。
- 低密度设计能放大关键词，让品牌提案更有记忆点。

使用方式：

- 用作品牌提案的封面、章节页、定位主张页、传播金句页。
- 信息密集页不要硬套 `bold-poster`，可同一方向参考 `broadside` 或 `neo-grid-bold` 的列表 / 对比语法重新设计。
- 对中文品牌名和 slogan 要单独调字距、行高和断行，避免英文模板的 display 字体逻辑直接套中文。

备选：`broadside`。适合需要中英双语、文化感、戏剧性更强的品牌叙事。

### 3. 投资人路演

推荐模板：`signal`

适用理由：

- `occasion` 包含 investor deck、board presentation、consulting deliverable、advisory pitch。
- `formality: high`、`density: high`，适合市场规模、商业模式、财务数据、路线图、风险和里程碑。
- 气质是 institutional / trustworthy / considered / weighty，能避免过度营销感。

使用方式：

- 用它作为路演卡片或 deck 的主视觉参考，保留深色 / 金色 / 骨白的权威感。
- 数据页使用模板里的高密度模块语言；封面和章节页保持克制，不做过多装饰。
- 如果内容面向小红书传播版路演复盘，可以降低文字密度，把每页压成一个观点 + 一个数据证据。

备选：`blue-professional`。适合更现代、轻咨询、B2B SaaS 或投资人 update 场景。

## 是否建议纳入当前项目

建议纳入，但只作为 `references/` 外部参考库使用。

短期接入方式：

- 保持 `references/beautiful-html-templates/` 原样。
- 在未来新建小红书图文包时，从 `index.json` 选候选模板。
- 将候选模板的视觉规则移植到新的 4:5 `index.html`。
- 用 Playwright 截图验证最终 PNG。

不建议：

- 不建议直接修改模板库原文件作为成品。
- 不建议把模板导航脚本作为小红书导图的必要依赖；但做 PPT / HTML deck 时可以保留。
- 不建议一次性把全部模板改造成项目内置主题，当前阶段会增加维护成本。

本次未修改 `docs/xiaohongshu-git-runtime-workflow-post/` 目录。
