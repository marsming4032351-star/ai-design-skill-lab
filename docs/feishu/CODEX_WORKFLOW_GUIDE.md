# Mars 的 Codex 使用指南

## 1. Codex 在我当前工作流中的定位

Codex 是当前工作流里的 Runtime Worker。

它不是单纯聊天助手，也不是只会生成代码的工具。它应该像一个有工程纪律的 AI 工人：先读仓库，理解目标，执行任务，验证结果，整理报告，再把阶段成果交付到 Git 和飞书。

在 ai-design-skill-lab 里，Codex 的位置是：

```text
Human gives goal
Codex executes
Harness records lifecycle
Feishu receives report
Git keeps project memory
```

## 2. Codex 适合做什么

### 读仓库

Codex 适合快速理解目录、README、docs、scripts、tests 和当前 git 状态。

它应该优先用 `rg`、`rg --files`、`git status`、`sed` 等轻量命令读取上下文。

### 写代码

Codex 可以实现明确边界内的代码改动。

适合的任务包括：

- 新增小模块
- 修 bug
- 补测试
- 调整 CLI 行为
- 改文档生成逻辑

### 写文档

Codex 很适合把阶段成果整理成文档：

- 架构说明
- 使用指南
- 阶段总结
- Manifesto
- 飞书发布稿

### 跑测试

Codex 应该在代码或行为变更后运行对应测试。

常用命令：

```bash
python3 -m pytest -q
```

### git commit

Codex 可以在确认变更范围后提交。

提交前应该先看：

```bash
git status --short
git diff --cached --stat
```

### 发飞书文档

当 `lark-cli auth status` 显示 `tokenStatus=valid` 时，Codex 可以用飞书作为移动端发布面。

推荐命令模式：

```bash
lark-cli docs +create --as user --title "<title>" --markdown "<markdown>"
```

### 总结阶段成果

Codex 适合把一次开发或 Runtime 阶段整理成：

- 本次做了什么
- 影响了哪些文件
- 如何验证
- 飞书链接
- commit hash
- 下一步建议

## 3. Codex 不适合直接做什么

### 无限 retry 外部授权

OAuth、Keychain、浏览器授权、飞书权限、人工确认都不是 Codex 可以靠 retry 修好的问题。

遇到这些边界应该进入：

```text
WAITING_AUTH / BLOCKED_EXTERNAL
```

### 跳过测试

如果改了代码或行为，就不能用“看起来没问题”替代测试。

### git add .

默认不要 `git add .`。

只有用户明确要求，并且当前工作区范围已经确认时才可以使用。通常更好的方式是只 add 本次目标相关文件。

### 擅自重构大范围代码

Codex 不应该为了“顺手优化”改动大量无关代码。

重构必须有明确目标、测试和回滚边界。

### 提交 pycache / output / zip

不要提交：

- `__pycache__/`
- `*.pyc`
- `.DS_Store`
- `output/`
- `playwright-cli/`
- `*.zip`

这些应该被 `.gitignore` 忽略或从历史提交中清理。

## 4. 标准 /goal 写法

一个好的 `/goal` 应该包含：

```text
目标：
<这次最终要完成什么>

背景：
<为什么做，当前上下文是什么>

要求：
1. <必须做什么>
2. <必须避免什么>
3. <需要运行哪些命令>
4. <需要输出哪些结果>

提交：
<是否提交，commit message 是什么>

限制：
<不能改哪些文件，不能运行哪些命令>
```

关键是把成功标准写清楚，让 Codex 可以自己执行、验证和收尾。

## 5. Harness 项目常用 /goal 模板

### 文档发布模板

```text
/goal

目标：
整理 <主题> 文档并发布到飞书。

要求：
1. 先运行 lark-cli auth status
2. tokenStatus=valid 才发布
3. 本地文档写入 docs/feishu/<name>.md
4. 创建飞书文档
5. README 增加入口
6. 运行 pytest
7. 只 add README 和本次文档
8. commit: docs: <message>
```

### Runtime 功能模板

```text
/goal

目标：
为 Harness Runtime 增加 <能力>。

要求：
1. 先读 harness/runtime.py 和 tests
2. 先补测试
3. 再实现
4. 不改无关 pipeline
5. 运行 python3 -m pytest -q
6. 输出变更摘要和 commit hash
```

### Blocked State 模板

```text
/goal

目标：
处理一个外部授权或人工边界。

要求：
1. 不无限 retry
2. 不重复 auth/init
3. 先检查状态
4. 如果不可由 Agent 修复，输出 WAITING_AUTH 或 BLOCKED_EXTERNAL
5. 写清楚人类下一步动作
```

## 6. Git 提交流程

推荐流程：

```bash
git status --short
git diff -- <files>
python3 -m pytest -q
git add <specific-files>
git diff --cached --stat
git commit -m "<message>"
git status --short
```

原则：

- 只提交本次目标相关文件
- 不提交缓存和输出产物
- commit message 写清楚目的
- 提交后确认工作区状态

## 7. 飞书发布流程

飞书发布前必须先检查：

```bash
lark-cli auth status
```

只有看到：

```text
tokenStatus: valid
```

才创建文档。

创建文档命令模式：

```bash
lark-cli docs +create --as user --title "<title>" --markdown "<markdown>"
```

如果文档内容来自本地 Markdown，Codex 应该用脚本把文件内容作为参数传给 CLI，避免 shell 误解释代码围栏。

## 8. 遇到 WAITING_AUTH / BLOCKED_EXTERNAL 怎么处理

如果遇到：

- OAuth 页面等待
- Keychain 缺失
- 飞书权限不足
- 浏览器授权未完成
- 用户确认未给出

Codex 应该停止继续执行，并明确输出：

```text
WAITING_AUTH / BLOCKED_EXTERNAL
```

然后说明人类需要做什么。

不要继续开新的授权流。

不要无限等待。

不要把外部授权失败伪装成普通测试失败。

## 9. 如何让 Codex 成为 Runtime Worker

让 Codex 成为 Runtime Worker 的关键，是让它围绕生命周期工作，而不是围绕单次回答工作。

它应该遵循：

```text
read context -> execute scoped change -> verify -> publish/report -> commit -> summarize
```

在 Harness 项目里，Codex 应该主动维护这些边界：

- 用户给目标
- Codex 执行
- Harness 记录生命周期
- Feishu 接收报告
- Git 保存项目记忆

## 10. 未来最佳实践

未来最佳实践是：

```text
Human gives goal, Codex executes, Harness records lifecycle, Feishu receives report.
```

Human 负责方向、品味、优先级和边界。

Codex 负责执行、验证、整理和交付。

Harness 负责让 AI 工作变成可追踪的运行过程。

Feishu 负责让阶段成果进入移动端工作台。

Git 负责让项目历史可追溯。

这套流程的目标不是让 AI 取代人，而是让人类目标可以被稳定、透明、可复盘地执行。
