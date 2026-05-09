# Git Commit vs Git Push：AI Runtime 日常工作流指南

## 1. 为什么 AI Runtime 时代必须理解 Git

AI Runtime 会让 Codex、Harness、测试、审计、飞书发布和 Git 变成一条连续生产线。

在这条生产线里，Git 不是最后一步的“保存按钮”，而是项目记忆账本。每一次明确的 commit 都是在记录一个 Runtime milestone：这次人类给了什么目标，AI 改了什么，测试是否通过，哪些文档沉淀到了飞书，哪些成果可以被未来复用。

如果不理解 Git，AI 执行速度越快，风险越高。因为错误、缓存、密钥、临时输出和私人上下文都可能被一起带到公开仓库。

## 2. git add 是什么

`git add` 是把工作区里的改动放进暂存区。

可以把 Git 分成三层：

- 工作区：你当前文件系统里的真实改动。
- 暂存区：准备进入下一次 commit 的改动清单。
- 本地历史：已经形成 commit 的项目记录。

`git add` 的核心价值是精准提交。

AI Runtime 里不要默认使用：

```bash
git add .
```

原因很简单：工作区里可能同时存在本次任务文件、测试缓存、临时 output、飞书 auth 痕迹、本机路径、下载文件和用户尚未确认的改动。

更好的方式是只 add 本次目标相关文件：

```bash
git add README.md docs/feishu/GIT_WORKFLOW_GUIDE.md
```

这让 commit 的边界清晰，也方便 review 和回滚。

## 3. git commit 是什么

`git commit` 是创建一个本地历史快照。

commit 发生在本机，不等于公开，也不等于 GitHub 已经更新。

在 AI Runtime 项目里，commit 应该被理解为 Runtime milestone：

- 某个目标被执行完成。
- 相关文件被明确纳入。
- 测试或审计结果已经确认。
- 这一步可以被 Git 历史追溯。

commit 的好处是把阶段成果固定下来。即使后面继续试错，也能回到一个已知状态。

## 4. git push 是什么

`git push` 是把本地 commit 同步到远端仓库。

对于 GitHub 来说，push 就是 publish。

commit 可以是本地记忆；push 是把记忆交给团队、GitHub、CI、投资人、合伙人或开源社区。

所以 push 前必须 review：

- 有没有 token、secret、webhook、cookie。
- 有没有 output、logs、pycache、zip。
- 有没有本机绝对路径。
- docs 里有没有 auth 输出、workspace id、userOpenId、appId。
- README 里的外部链接是否适合公开。

## 5. 当前项目中的正确流程

```text
Human Goal
↓
Codex 修改
↓
pytest
↓
git status
↓
Security Audit
↓
git add 指定文件
↓
git commit
↓
Human Review
↓
git push
↓
GitHub
```

这条链路的重点不是“让 AI 更快提交”，而是让 AI 的每一次动作都能被观察、验证、复盘和回滚。

## 6. 为什么 AI 可以 commit 但不应该默认自动 push

AI 可以 commit，因为 commit 是本地边界。

只要文件范围明确、测试通过、提交信息清楚，Codex 可以把一次任务固化成 commit。

但 AI 不应该默认自动 push，因为 push 是公开边界。

push 会把本地历史同步到外部系统。它可能触发 GitHub Actions、通知、权限扩散、公开访问、团队 review 和长期留存。

因此默认治理原则是：

```text
AI can commit.
Human should review before push.
```

当用户明确要求 push，并且通过了安全审计、状态检查和分支确认，Codex 才应该执行 push。

## 7. review_required 的治理思想

Harness Runtime 里的 `review_required` 不是一个 UI 状态，而是一种治理思想。

它表达的是：

- 有些步骤可以自动执行。
- 有些步骤必须让人类确认。
- 外部授权、公开发布、安全边界、重大架构变化不应该被无限 retry。

Git push 就属于典型的 review boundary。

AI 可以准备材料，但最终 publish 前应留下明确 review 点。

## 8. push 前必须检查

push 前至少检查：

- token
- output
- logs
- pycache
- docs
- auth cache

推荐额外检查：

- `.env`
- `*.zip`
- `.DS_Store`
- 本机绝对路径
- Feishu workspace/document links
- userOpenId
- appId
- webhook
- cookie

这些检查可以通过 `git status --short`、`git diff`、`rg` 和安全审计文档完成。

## 9. 常用命令

查看工作区：

```bash
git status --short
```

查看具体改动：

```bash
git diff
```

精准暂存：

```bash
git add README.md docs/feishu/GIT_WORKFLOW_GUIDE.md
```

创建本地快照：

```bash
git commit -m "docs: add git workflow and runtime governance guide"
```

查看历史：

```bash
git log --oneline
```

同步 GitHub：

```bash
git push
```

## 10. 适合 Mars 的最佳实践

### 小 commit

每个 commit 只做一件事。

小 commit 更容易 review、回滚、解释，也更适合 Runtime milestone。

### docs first

当项目处在架构演进期，先写清楚概念和边界，再让代码跟上。

docs first 可以减少 AI 误解，也能让合伙人、技术朋友和投资人快速理解项目。

### review before push

commit 可以频繁，push 要谨慎。

push 前至少确认：

- branch 正确
- status 清楚
- 测试通过
- 审计无 live secret
- 本次 push 的目的明确

### Runtime 生命周期记录

每次重要变更都应该留下：

- goal
- changed files
- test result
- commit hash
- Feishu document link
- next milestone

### 飞书沉淀

飞书是移动端工作台。

适合沉淀：

- 使用指南
- 阶段总结
- 展示页
- 决策记录
- 给合伙人的说明

### Obsidian Memory

Obsidian 更适合长期知识库和个人记忆。

飞书偏协作和移动端阅读，Obsidian 偏深度知识沉淀。

## 11. Runtime Company 的 Git Governance

Runtime Company 的 Git 治理原则可以总结为：

```text
Goal drives work.
Codex executes.
Harness records lifecycle.
Tests verify behavior.
Git commits memory.
Human reviews publish.
GitHub distributes.
Feishu explains.
Obsidian remembers.
```

这套流程的本质是把 AI 从“随手改代码的助手”升级成“受治理的 Runtime Worker”。

好的 Git 工作流不是拖慢 AI，而是让 AI 的速度可以被信任、被审计、被复用。
