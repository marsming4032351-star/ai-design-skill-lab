# AI Native Design Runtime 使用指南

## 1. 当前仓库是什么

`ai-design-skill-lab` 是一个 AI 原生设计工作台。

它把设计任务拆成可执行、可评审、可复盘、可沉淀的流程，而不是只保存一次模型输出。仓库里同时存在三层东西：

- 设计知识：Project、Asset、Prompt、Rule、Plan、Critique、Pattern、Run。
- 执行脚本：`scripts/` 下的 ingest、run、critic、archive、generate 等阶段入口。
- Harness Runtime：`harness/` 下的任务模型、运行上下文、阶段编排、事件日志、评审和重试机制。

一句话：这是一个面向 AI 设计生产的 Runtime OS 原型。

## 2. 它已经从 Design Data Factory 升级成了什么

早期的 Design Data Factory v6 重点是把设计生产变成结构化数据流水线：

```text
ingest -> run -> critic -> archive -> pattern reuse
```

升级后的方向是 **AI Native Design Harness Runtime**。

这意味着仓库不再只是脚本集合，也不只是 Prompt 仓库，而是增加了一个运行时层，用来管理：

- 一个任务如何开始
- 每一步由谁执行
- 结果如何被记录
- 失败是否可以重试
- 什么时候需要人工评审
- 什么时候应该暂停等待人类或外部授权
- 哪些结果可以归档成未来可复用的 Pattern

## 3. Harness Runtime 是什么

Harness Runtime 是 AI 设计任务的执行协调器。

它接收 `TaskSpec`，创建 `RunContext`，按生命周期运行 Planner、Generator、Critic、Review、Archive，并把每一步写入 `step_history` 和 `event_log`。

当前 Runtime 是 deterministic/mock runtime。它故意不调用真实 LLM，也不调用外部 API。这样做的目的是先证明状态机、重试、评审、归档和事件记录是稳定可测试的。

## 4. 当前已完成能力

### M1 Skeleton

M1 建立最小 Harness 骨架：

- `TaskSpec`
- `RunContext`
- `StepResult`
- `SkillRegistry`
- `ReviewDecision`
- `HarnessRuntime`

M1 的重点是安全：可以解析任务，但不执行既有生产 pipeline。

### M2 Runtime Execution

M2 证明 Runtime 可以执行完整 mock 生命周期：

```text
planner -> generator -> critic -> review -> archive
```

它加入了：

- mock planner
- mock generator
- mock critic
- mock archive
- `step_history`
- `event_log`
- `scripts/run_harness_demo.py`

### M3 Review / Retry Loop

M3 加入最小闭环：

```text
generator -> critic -> feedback -> generator -> critic
```

当 Critic 返回 fail 且还有 retry budget 时，Runtime 会把 critic feedback 传回 Generator，再生成下一版。

M3 也引入了终态：

- `ARCHIVED`
- `FAILED`
- `REVIEW_REQUIRED`

### Blocked State Design

Blocked State Design 用来处理无法由 Agent 自主修复的问题。

例如：

- OAuth 未完成
- 飞书授权未完成
- Keychain 缺失
- 外部服务阻塞
- 人工确认未给出

这类问题不应该无限 retry，而应该进入：

- `WAITING_HUMAN`
- `WAITING_AUTH`
- `BLOCKED_EXTERNAL`
- `PAUSED`
- `RESUMABLE`

### Feishu Workspace Integration

飞书现在被定位为移动端工作台。

Codex / Harness 生成的阶段报告、使用指南、项目总结，可以通过 `lark-cli docs +create --as user` 发布到飞书文档，方便手机端阅读、分享和复盘。

## 5. 核心模块解释

### TaskSpec

`TaskSpec` 是任务说明书。

它描述这次 Harness 要做什么，包括任务 id、skill id、inputs、metadata，以及是否需要 review。

### RunContext

`RunContext` 是一次运行的上下文。

它保存：

- `run_id`
- workspace
- artifacts_dir
- state
- step_history
- event_log
- retry_count
- max_retries

### HarnessRuntime

`HarnessRuntime` 是状态机和协调器。

它负责按顺序运行 planner、generator、critic、review、archive，并决定是否 retry、failed、review required 或 archived。

### Planner

Planner 把 brief 变成 mock plan。

它是“先想清楚要做什么”的阶段。

### Generator

Generator 根据 plan 生成 mock visual。

如果前一次 Critic 失败，它会读取 `generator_feedback`，生成带反馈的新版本。

### Critic

Critic 是评价器。

它根据输入里的 `critic_decision` 或 `critic_decisions` 返回 pass/fail，并在 fail 时给出 mock feedback。

### Archive

Archive 是归档器。

只有 Critic pass 且 Review approved 后，Archive 才会把结果变成 mock pattern。

### Event Log

`event_log` 是运行事件流水。

它记录“发生了什么”，例如：

- run_started
- step_started
- step_finished
- critic_failed
- retry_started
- retry_finished
- review_requested
- review_approved
- run_finished

### Step History

`step_history` 是阶段结果列表。

它记录“每一步产出了什么”。如果发生 retry，会看到重复的 generator / critic 记录。

### Review Required

`REVIEW_REQUIRED` 表示 Runtime 到达了需要人工处理的治理点。

它不是普通失败，而是说明结果不能自动进入 Archive。

### Retry Count / Max Retries

`retry_count` 表示已经重试了几次。

`max_retries` 表示最多允许重试几次。

当前默认 `max_retries=1`，也就是一次初始尝试加一次重试机会。

## 6. 怎么运行 demo

在仓库根目录运行：

```bash
python3 scripts/run_harness_demo.py examples/harness_goal.yaml
```

这个命令会读取 `examples/harness_goal.yaml`，创建 `TaskSpec`，然后调用 `HarnessRuntime.run()`。

## 7. 如何理解运行结果

### run_id

`run_id` 是本次运行的唯一编号。

它用于追踪一次 Harness run。

### final_state

`final_state` 是运行终态：

- `ARCHIVED`：通过 Critic 和 Review，已经归档。
- `FAILED`：失败且没有可用 retry。
- `REVIEW_REQUIRED`：需要人工评审或人工处理。

### step_history

`step_history` 适合看每个阶段的输出。

一次 retry 后通过的运行可能是：

```text
planner
generator
critic
generator
critic
archive
```

### event_log

`event_log` 适合看 Runtime 决策过程。

它能说明什么时候失败、什么时候 retry、什么时候通过、什么时候请求 review。

### review_required

`review_required` 表示任务是否声明需要 review。

当前 archive 前会有 review gate；默认 reviewer 会自动 approve，但事件仍然会记录。

## 8. 当前项目能用来做什么

当前项目可以用来：

- 演示 AI 设计 Runtime 的基本生命周期
- 验证 planner / generator / critic / archive 的最小编排
- 测试 retry loop 和 review loop
- 记录 step_history 和 event_log
- 写设计系统、Runtime、Prompt、Codex 使用指南
- 把阶段成果发布到飞书移动端工作台
- 为后续 Memory / Evaluator / Multi-Agent Runtime 打基础

## 9. 下一阶段

### M4 Memory

M4 要把历史运行和已归档 Pattern 接回未来任务，让系统拥有可复用设计记忆。

目标是让下一次规划可以参考过去成功经验，而不是每次从零开始。

### M5 Evaluator

M5 要把评估变成一等能力。

它会关注：

- golden cases
- prompt regression
- rule regression
- critic calibration
- generator output quality
- archive/promotion gate

### M6 Multi-Agent Runtime

M6 要协调多个专业 Agent：

- planner agent
- generator agent
- critic agent
- memory agent
- archive agent
- human review gate

重点不是“让 Agent 自主乱跑”，而是让每个 Agent 的输入、输出、边界和审计记录清晰。

## 10. 用通俗语言理解

### Codex 是 AI 工人

Codex 负责执行具体任务：读仓库、写文档、改代码、跑测试、提交 git、发布飞书。

### Harness 是 AI 工厂

Harness 负责把 AI 工作组织成流水线：计划、生成、评价、重试、评审、归档。

### Feishu 是移动端工作台

Feishu 负责承载报告、指南、阶段总结和移动端阅读入口。

### Git 是项目记忆账本

Git 负责记录项目每次变化，让所有文档、代码、测试和决策都能追踪。

一句话：

```text
Human gives goal, Codex executes, Harness records lifecycle, Feishu receives report, Git keeps memory.
```
