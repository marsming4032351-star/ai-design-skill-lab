# AI Native Design Runtime 展示测试页

## 1. 这个展示页是什么

Runtime Demo Cockpit 是 `ai-design-skill-lab` 的静态展示界面。

它不是一个新的 Web 服务，也不是 React 应用，而是一个可以直接打开的单文件 HTML，用来向合伙人、技术朋友、投资人解释：

```text
这个项目不是单次生图工具，而是 AI Native Design Runtime。
```

它把当前 Harness M1/M2/M3 的核心能力放在一页里：

- Human Goal 如何进入 Codex
- Codex 如何把目标交给 Harness Runtime
- Harness 如何运行 Planner / Generator / Critic / Archive
- Critic 如何触发 retry loop
- blocked state 为什么代表更成熟的 runtime
- Feishu 如何成为移动端工作台

## 2. 本地怎么打开

在仓库根目录运行：

```bash
open demo/runtime_cockpit.html
```

这个页面是纯静态 HTML，不需要启动服务，不需要安装前端依赖。

如果是在非 macOS 环境，也可以直接用浏览器打开：

```text
demo/runtime_cockpit.html
```

## 3. 如何运行 demo

在仓库根目录运行：

```bash
python3 scripts/run_harness_demo.py examples/harness_goal.yaml
```

这条命令会读取 `examples/harness_goal.yaml`，创建 `TaskSpec`，调用 `HarnessRuntime.run()`，并输出：

- `run_id`
- `review_required`
- `retry_count`
- `max_retries`
- `final_state`
- `step_history`
- `event_log`

## 4. 如何理解 Runtime 生命周期

当前 Runtime 生命周期是：

```text
Human Goal
-> Codex
-> Harness Runtime
-> Planner
-> Generator
-> Critic
-> Retry Loop
-> Archive
-> Feishu Workspace
```

通俗理解：

- Human Goal：人类给出目标和边界。
- Codex：AI 工人，负责读仓库、写文档、跑测试、提交、发布飞书。
- Harness Runtime：AI 工厂，负责把目标组织成生命周期。
- Planner：先做计划。
- Generator：生成候选结果。
- Critic：判断结果是否通过。
- Retry Loop：失败后带反馈再试。
- Archive：通过评审后沉淀为可复用知识。
- Feishu Workspace：把阶段成果交付到移动端。

## 5. 如何理解 Codex / Harness / Feishu 三者关系

这三个角色分工不同：

```text
Codex = AI Worker
Harness = AI Factory
Feishu = Mobile Workspace
```

Codex 负责执行。

Harness 负责记录生命周期。

Feishu 负责把阶段成果带到移动端，让它可以被阅读、分享、讨论和复盘。

更完整的链路是：

```text
Human gives goal
Codex executes
Harness records lifecycle
Feishu receives report
Git keeps project memory
```

## 6. 后续如何演变

### 飞书知识库

后续可以把 Runtime 指南、Codex 指南、Demo Cockpit、阶段总结沉淀到飞书知识库。

知识库可以成为移动端入口，让非开发角色也能理解项目进展。

### 飞书多维表格 Dashboard

未来可以把 Harness run 写入飞书多维表格：

- run_id
- final_state
- retry_count
- max_retries
- review_required
- created_at
- doc_url

这样可以形成移动端 Runtime Dashboard。

### 飞书白板全景图

Runtime Cockpit 的生命周期图可以进一步做成飞书白板：

```text
Human Goal -> Codex -> Harness -> Planner -> Generator -> Critic -> Archive -> Feishu
```

白板适合对外演示整体系统结构。

### 飞书机器人移动端入口

最终可以让飞书机器人成为移动端入口：

- 接收一个 goal
- 调用 Codex / Harness 工作流
- 返回运行状态
- 发布结果文档
- 在移动端提醒人类 review 或处理 blocked state

这会让 `ai-design-skill-lab` 从本地仓库进一步变成移动端可触达的 AI Native Design Runtime OS。

## 7. 演示时的核心话术

可以这样介绍：

```text
这个项目不是为了生成一张图。
它是在建立一个设计 Runtime。
Codex 是执行者，Harness 是生命周期，Feishu 是移动端工作台。
每一次生成、批评、重试、评审、归档，都可以被记录和复盘。
```

这就是 Runtime Demo Cockpit 要展示的内容。
