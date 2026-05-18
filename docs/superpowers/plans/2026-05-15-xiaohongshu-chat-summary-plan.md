# 小红书聊天总结图文 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把最近围绕仓库结构、Output Skill、Lovart / imagegen、HTML PPT 和生图流程的对话，总结成一套 5 张卡片的小红书图文包，适合小白快速理解。

**Architecture:** 复用仓库现有的 `docs/<topic>/` 小红书输出包结构，使用单个 `index.html` 作为源文件，用 HTML/CSS 直接排版 5 张 1080 x 1350 卡片，再用浏览器截图导出 PNG。内容上按“这段聊天在讲什么 → 仓库在做什么 → 结构和路由 → Output Skill 与生图链路 → 怎么使用”来组织，保证解释顺序清晰，不引入额外脚本或主流程改动。

**Tech Stack:** HTML/CSS, 浏览器截图导出, Markdown 发布文案, PNG cards, 现有 `docs/` 归档结构。

---

### Task 1: 定义图文结构和文案

**Files:**
- Create: `docs/xiaohongshu-chat-summary/README.md`
- Create: `docs/xiaohongshu-chat-summary/post-copy.md`
- Create: `docs/xiaohongshu-chat-summary/index.html`

- [ ] **Step 1: 写出 5 张卡片的具体文案和信息层级**

```text
卡 1：这段聊天在干嘛
卡 2：这个仓库到底是干嘛的
卡 3：四层结构和任务路由
卡 4：Output Skill、HTML PPT、小红书图文、PDF 的关系
卡 5：Lovart、imagegen、design-generate 分别是什么
```

- [ ] **Step 2: 写可直接发布的小红书正文**

```md
# 标题
用 5 张图讲清 AI Design Skill Lab 到底在做什么

正文：
...
```

- [ ] **Step 3: 写 HTML 源文件**

```html
<section class="card">...</section>
```

- [ ] **Step 4: 浏览器预览确认 5 张卡片结构完整**

Run: 打开 `docs/xiaohongshu-chat-summary/index.html`
Expected: 5 张卡片都能正常显示，中文不溢出。

### Task 2: 导出卡片 PNG

**Files:**
- Create: `docs/xiaohongshu-chat-summary/cards/card-01.png`
- Create: `docs/xiaohongshu-chat-summary/cards/card-02.png`
- Create: `docs/xiaohongshu-chat-summary/cards/card-03.png`
- Create: `docs/xiaohongshu-chat-summary/cards/card-04.png`
- Create: `docs/xiaohongshu-chat-summary/cards/card-05.png`

- [ ] **Step 1: 用真实浏览器逐卡截图**

Run: 浏览器/Playwright 截图
Expected: 每张 PNG 为 1080 x 1350。

- [ ] **Step 2: 检查导出结果**

Run: `file docs/xiaohongshu-chat-summary/cards/card-01.png`
Expected: PNG, 1080 x 1350。

### Task 3: 归档说明和质量检查

**Files:**
- Create: `docs/xiaohongshu-chat-summary/README.md`

- [ ] **Step 1: 写清楚来源、规格、导出方式和适用场景**

```md
样例名称、类型、源文件、导出方式、与 OUTPUT_SKILL_SPEC 的关系、为什么不是主流程代码
```

- [ ] **Step 2: 检查标题、路径和卡片内容一致**

Run: 读 `README.md` + `post-copy.md`
Expected: 文案与卡片内容一致，目录结构清楚。

- [ ] **Step 3: 提交前检查**

Run: `git status --short`
Expected: 只包含这次新建的小红书图文包相关文件。

