# Runtime Manifesto

Date: 2026-05-09
Status: Manifesto

## Prompt Is Not The End

Prompt 是入口，不是终点。

Prompt 可以召唤一次回答，可以塑造一次输出，可以让模型短暂地进入一个角色。

但 Prompt 不会记住一个项目如何演化，不会知道一个结果是否被接受，不会判断一次失败该重试还是暂停，不会把成功经验沉淀成 Pattern，也不会在外部授权、人工确认、风险操作面前自己停下来。

真正的 AI 系统不止是在问模型。

真正的 AI 系统在管理一个过程。

这个过程需要状态，需要边界，需要评审，需要记忆，需要可恢复的运行轨迹。

Prompt 是语言。

Runtime 是制度。

## AI Companies Become Runtime Companies

当模型越来越强，模型本身会越来越像基础设施。

差异不会只来自谁写了更长的 Prompt，谁调用了更新的模型，谁生成了更漂亮的一张图。

真正的差异会来自 Runtime：

- 谁能把意图变成可执行的生命周期
- 谁能把工具、模型、记忆和人类决策编排在一起
- 谁能知道什么时候继续，什么时候重试，什么时候暂停
- 谁能证明一个结果为什么被接受
- 谁能把一次成功变成下次的上下文
- 谁能让系统长期变好，而不是每次从零开始

未来的 AI 公司不是 Prompt Company。

未来的 AI 公司是 Runtime Company。

模型负责能力。

Runtime 负责秩序。

## Design Needs Runtime

设计行业尤其需要 Runtime。

设计不是一次生成。

设计是反复理解目标、吸收上下文、提出方向、生成草案、批评修正、人工判断、沉淀经验的过程。

设计工作里最重要的东西常常不是最终那张图，而是：

- 为什么这样做
- 哪些方向被否定
- 哪些反馈改变了下一版
- 哪些风格可以复用
- 哪些 Pattern 适合下一个项目
- 哪些决策需要人类承担责任

单次生成只能给出一个结果。

Runtime 才能保存设计判断。

如果设计行业要进入 AI Native 阶段，它需要的不只是更强的生成器，而是能承载设计过程的运行时。

## Single Generation Has No Long-Term Value

单次生成的价值很短。

它可能惊艳，但它不积累。

它可能有用，但它不解释。

它可能被采用，但它不告诉系统为什么被采用。

没有 Runtime，生成结果会消失在对话里、文件夹里、临时输出里。下一次任务开始时，系统仍然不知道上一次学到了什么。

长期价值来自复利。

复利来自记忆。

记忆来自结构化的生命周期。

所以 AI 设计系统的目标不是多生成几张图，而是让每一次生成都能进入一个可评审、可追踪、可复用的循环。

## Vocabulary Of Runtime

### Lifecycle

Lifecycle 是一次任务的生命线。

它定义从目标到计划、生成、批评、评审、归档的路径。没有 Lifecycle，AI 工作就是零散调用；有了 Lifecycle，AI 工作才成为流程。

### Review

Review 是人类治理点。

它承认有些决定不能交给模型自动通过。Review 不是阻碍效率，而是保护责任、质量和长期记忆。

### Critic

Critic 是系统的判断器。

Generator 负责提出可能性，Critic 负责判断可能性是否成立。没有 Critic，系统只会生产；有了 Critic，系统才会辨别。

### Memory

Memory 是经验的容器。

它保存项目、Pattern、Run、Critique、Prompt、Rule，以及过去的成功和失败。Memory 让系统不必每次从零开始。

### Evaluator

Evaluator 是能力的量尺。

它不只评价一次输出，而是评价一类能力是否稳定。Evaluator 让系统知道自己有没有变好。

### Pattern

Pattern 是被提炼出来的可复用设计知识。

它不是一张图，也不是一句描述。它是经过上下文、生成、批评和评审之后，仍然值得带入未来任务的经验。

### Runtime State

Runtime State 是系统对自身处境的声明。

它告诉我们当前是在运行、重试、等待人类、等待授权、被外部依赖阻塞、需要评审、已经失败，还是已经归档。

没有 Runtime State，系统只会继续执行。

有了 Runtime State，系统开始理解边界。

## Human Steer, Agents Execute

人类不应该被迫执行每个机械步骤。

Agent 也不应该被允许替人类承担所有判断。

正确的关系是：

```text
Human steer, agents execute.
```

人类设定目标、边界、品味、风险偏好和最终责任。

Agent 执行搜索、生成、整理、评估、归档和复用。

Runtime 站在中间，负责把人类意图变成可执行的状态机，也负责在越过边界前停下来。

## Evaluator Is More Important Than Generator

Generator 会让系统看起来聪明。

Evaluator 会让系统真的变好。

生成能力越来越便宜，越来越普遍，越来越容易调用。真正稀缺的是判断能力：知道什么是好，什么是坏，什么只是看起来完成，什么值得进入长期记忆。

没有 Evaluator，Generator 会把噪声也生产得很漂亮。

有了 Evaluator，系统才知道哪些输出可以信任，哪些 Prompt 退化了，哪些 Pattern 误导了后续任务，哪些 Critic 太宽松，哪些 Archive 不应该发生。

Generator 扩大可能性。

Evaluator 建立方向感。

长期看，方向感比产能更重要。

## To Pause Is More Advanced Than To Generate

会生成不稀奇。

会暂停更高级。

暂停意味着系统知道自己不能越界。

当 OAuth 没完成，当外部授权缺失，当用户还没有确认，当风险操作需要人类承担责任，继续执行不是智能，而是失控。

真正成熟的 Runtime 必须能说：

```text
I can continue, but I should not.
```

它必须能进入 `WAITING_HUMAN`、`WAITING_AUTH`、`BLOCKED_EXTERNAL`、`PAUSED`、`RESUMABLE`。

暂停不是失败。

暂停是治理。

暂停是安全。

暂停是对人类边界的尊重。

## AI Native Design Runtime OS

`ai-design-skill-lab` 的长期方向不是做一个更会写 Prompt 的仓库。

它的方向是成为一个 **AI Native Design Runtime OS**。

这个 OS 应该让设计工作具备以下能力：

- 目标可以进入 Lifecycle
- 上下文可以被结构化加载
- 生成可以被 Critic 检查
- 结果可以被 Review 治理
- 失败可以被 Retry 修正
- 外部依赖可以触发 Blocked State
- 通过的成果可以 Archive
- 成功经验可以沉淀为 Pattern
- Pattern 可以进入未来 Memory
- Evaluator 可以持续校准系统质量

这不是为了让设计变成机械流程。

相反，这是为了保护真正重要的设计判断。

AI Native Design Runtime OS 的目标，是让人类的方向感、审美和责任，与 Agent 的执行力、记忆力和规模化能力结合起来。

不是让模型替代设计。

而是让设计拥有自己的 Runtime。

## Closing

Prompt 时代问的是：

```text
What should I ask the model?
```

Runtime 时代问的是：

```text
What system should carry the work?
```

这就是转折点。

AI 的长期价值，不在一次回答里。

它在可以被运行、被评审、被暂停、被恢复、被记住、被改进的循环里。
