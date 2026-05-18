# 小红书发布包：用 Codex 构建设计工作流

这是一个可直接发布的小红书图文包，主题是“Codex 不是 prompt 工具，而是设计流水线”。

## 内容策略

核心观点：

- Codex 不只是 prompt 输入框，而是一条可编排的设计生产线。
- 设计策划自动化流程应按“资料诊断 → 策略 → 视觉生成 → 排版 → 输出图文”拆解。
- 图片生成负责质感，HTML/CSS 负责中文信息层级和可验证输出。

选题标题备选：

1. 别再把 Codex 当 Prompt 工具了
2. 我用 Codex 搭了一条设计流水线
3. 设计师用 Codex，关键不是写 Prompt

## 分页大纲

1. 封面：别再把 Codex 当成 Prompt 工具
2. 认知冲突页：Prompt 是一句话，流程是一套系统
3. 工作流总览：资料诊断、策略成型、视觉生成、排版输出
4. 策略前置：先做资料诊断，不要急着出图
5. 方法拆解：策略先定住，视觉才不会乱飞
6. 视觉边界：视觉生成只负责氛围，不负责长中文
7. 排版输出：排版是最后一道质量控制
8. 行动引导：把 Codex 当成设计项目经理

## 逐页发布结构

### 封面图说明

- 图片：`cards/card-01.png`
- 内容说明：深色设计工作台背景，超大标题制造认知冲突，强调“Codex 不是 Prompt 工具”。
- 对应文案：别再把 Codex 当成 Prompt 工具。真正高效的用法，是把它搭成一条从策略、视觉到排版的设计流水线。

### 第 1 页

- 图片：`cards/card-01.png`
- 页面角色：封面，强吸引。
- 对应文案：别再把 Codex 当成 Prompt 工具，先建立“设计流水线”的核心认知。

### 第 2 页

- 图片：`cards/card-02.png`
- 页面角色：认知冲突页。
- 对应文案：Prompt 是一句话，流程是一套系统。普通用法是丢一句需求，工作流用法是拆成多个阶段。

### 第 3 页

- 图片：`cards/card-03.png`
- 页面角色：工作流总览。
- 对应文案：资料诊断、策略成型、视觉生成、排版输出，组成一条可复制的设计生产线。

### 第 4 页

- 图片：`cards/card-04.png`
- 页面角色：资料诊断和策略前置。
- 对应文案：先读资料，拆目标、受众、渠道和限制，不要急着让 AI 出图。

### 第 5 页

- 图片：`cards/card-05.png`
- 页面角色：策略方法拆解。
- 对应文案：先锁定核心主张、传播钩子和页面逻辑，视觉才不会乱飞。

### 第 6 页

- 图片：`cards/card-06.png`
- 页面角色：视觉生成边界。
- 对应文案：imagegen / GPT Image 负责质感和场景，中文标题、正文、编号和流程图交给 HTML 排版。

### 第 7 页

- 图片：`cards/card-07.png`
- 页面角色：排版输出和质量控制。
- 对应文案：排版不是美化，而是检查字号、层级、溢出、遮挡和最终发布尺寸。

### 第 8 页

- 图片：`cards/card-08.png`
- 页面角色：方法总结和行动引导。
- 对应文案：把 Codex 当成设计项目经理，收藏后按“诊断、策略、视觉、排版、验证”这条流程复用。

## 文件说明

- `index.html`：8 张小红书卡片的 HTML/CSS 源文件
- `post-copy.md`：标题、正文、评论区引导和标签
- `cards/card-01.png` 到 `cards/card-08.png`：导出的最终发布图片
- `assets/`：复用上一版已生成的 GPT Image / Codex Image 视觉素材

## 图片规格

- 数量：8 张
- 尺寸：1080 x 1350 px
- 比例：4:5
- 格式：PNG
- 风格：深色背景、高级信息卡、强对比大标题、中文可读

## 素材来源

视觉背景复用仓库内已生成资产：

- `assets/gpt-image-01-cover.png`
- `assets/gpt-image-02-skills.png`
- `assets/gpt-image-03-imagegen.png`
- `assets/gpt-image-04-deck.png`
- `assets/gpt-image-05-export.png`

长中文标题、正文、编号和流程信息全部由 HTML/CSS 叠加，避免生图模型生成中文错误。

## 导出方式

使用 Playwright 对每个卡片节点截图：

```bash
bash /Users/ming/.codex/skills/playwright/scripts/playwright_cli.sh screenshot "#card-01" --filename "docs/xiaohongshu-codex-design-pipeline-post/cards/card-01.png"
```

按 `#card-01` 到 `#card-08` 依次导出。
