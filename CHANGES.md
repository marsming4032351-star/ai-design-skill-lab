# skill-v6 · Pattern 推荐 + PyYAML 上线（双交付）

## 本次发布做了两件事

### 1. 主交付：Pattern 推荐机制（v6 主线）
让 design-run 在概念阶段**自动从历史 Pattern 库中拉相关 Pattern 进 prompt context**。
这是 Design Data Factory 闭环真正"转起来"的关键——上一次的设计沉淀真的影响下一次。

### 2. 紧急转向：PyYAML 替换（v6.5 修复）
原本计划在选项 D 之后做 PyYAML 替换。但在 v6 实现过程中，推荐 rule 因为有
`computation: |` block scalar 嵌在 list-of-dict 里，**手写解析器再次崩溃**。
这是第 6 个 frontmatter bug。决定立即上线 PyYAML，不再打补丁。

## Round 1 vs Round 2 对比（这是 v6 最重要的演示）

```
ROUND 1：空 Pattern 库
├─ ingest → run → critic → archive
├─ run prompt 中 "可参考的历史 Pattern: (无)"
└─ archive 后产生 pat_dryrun，加入 Pattern 库

ROUND 2：库里有 1 个 Pattern  ←── design-run 自动检测并推荐
├─ ingest → run（推荐 pat_dryrun）→ critic → archive
├─ run prompt 中 "可参考的历史 Pattern: pat_dryrun"
├─ pat_dryrun.reuse_count: 0 → 1
└─ Plan.consumed_patterns: ["pat_dryrun"] ← 审计字段
```

**这就是工厂闭环。每跑一次新项目，工厂都从历史项目中自动获益。**

## 文件清单（v6 新增）

```
skill-v6/
├── scripts/
│   ├── scan_inbox.py            ← v2 沿用（因 PyYAML 自动受益）
│   ├── run_design.py            ← v6 重大增强（推荐器集成）
│   ├── critic_design.py         ← v4 沿用
│   └── archive_design.py        ← v5 沿用
├── shared/
│   ├── frontmatter.py           ← v6.5 PyYAML 重写（API 不变）
│   ├── recommendation_engine.py ← v6 新增
│   └── (其他模块无变化)
├── references/
│   ├── 40_Rules/
│   │   └── rul_recommend_pattern.md   ← v6 新增（4 维度推荐 rule）
│   └── (其他 references 无变化)
└── example_output/
    ├── round1_no_patterns/       ← 空库时跑全链路
    └── round2_with_patterns/     ← 库里有 1 pattern 时再跑
```

## 推荐器架构（4 维度加权）

| 维度 | 权重 | 含义 |
|---|---:|---|
| applicability | 45% | Pattern.applicable_when 与 Project 上下文的重叠度 |
| quality | 25% | Pattern.reuse_score（来自原 critique 的 reuse_potential） |
| validation | 20% | reuse_count（被引用次数，封顶 5） |
| recency | 10% | 创建时间衰减（< 90 天 = 5，>= 2 年 = 1） |

阈值：
- `recommendation_threshold: 3.0` — 加权分必须 ≥ 此值
- `top_k: 3` — 默认推荐 Top-3
- `min_score: 1.5` — 低于此完全不考虑

## CLI 使用（design-run v6 新增参数）

```bash
python3 scripts/run_design.py \
  --project ... --manifest ... --prompts-dir ... --out ... \
  --rules-dir references/40_Rules \      # ← 新增：推荐 rule 来源
  --patterns-dir /vault/30_Patterns \    # ← 新增：Pattern 库
  --top-k 3 \                            # ← 可选
  --pattern pat_specific \               # ← 可选：强制指定（多次）
  --no-recommend \                       # ← 可选：禁用推荐
  --no-update-pattern-counts             # ← 可选：不自增 reuse_count
```

## 端到端实测结果

| 验证项 | 结果 |
|---|---|
| **Round 1 → Round 2 闭环** | ✓ Round 2 自动推荐 Round 1 沉淀的 Pattern |
| 推荐器黄金集 3 个 test_case | ✓ 3/3 |
| 推荐进 prompt context 渲染 | ✓ "可参考的历史 Pattern: pat_dryrun" 真实注入 |
| Pattern.reuse_count 自动 +1 | ✓ 0 → 1 |
| Plan.consumed_patterns 写入 | ✓ ["pat_dryrun"] |
| `--pattern` 强制指定 | ✓ 用户指定优先于推荐 |
| `--no-recommend` 禁用 | ✓ 0 patterns |
| `--top-k 0` 限制 | ✓ 候选有但不取 |
| **PyYAML 回归测试** 9/9 | ✓ 所有 v2~v5 测试不破坏 |
| brief signals lexicon 提取 | ✓ "高端" / "限定" 等正确识别 |

## 关键架构决策

### 1. 推荐是 design-run 的内置能力，不是独立 skill
推荐没有独立产物（不写新实体），它是 prompt context 组装的一环。
但推荐**逻辑**是 Rule 实体，独立版本化、可被黄金集覆盖、可被 LLM 取代。

### 2. 推荐评分用 weighted engine（与 rubric 同款）
两个引擎共享 `engine: weighted`：
- `rul_score_concept_direction` 给 direction 打分
- `rul_recommend_pattern` 给 Pattern 与 Project 的匹配度打分
**同一引擎服务不同决策场景**——这是 Rule 系统的复用价值。

### 3. 强制 `--pattern X` 即使 X 不存在也保留
当用户显式指定 pattern id 时，即使该 id 在库中不存在（比如还没归档），
我们也保留它在 `consumed_patterns` 里。理由：用户可能在别处定义。
这避免"我记得有这个 pattern 但工厂说找不到"的体验断裂。

### 4. brief_signals 用保守的 lexicon 匹配
P1 不做 NLP / 嵌入相似度。用一个固定词表（`高端 / 限定 / 新品 / launch / minimal` 等）
做 substring 匹配。词表不全是有意的——避免假阳性破坏推荐质量。
P2 可以替换为嵌入相似度。

### 5. validation 维度封顶 reuse_count=5
被引用 100 次和 5 次没本质区别，封顶避免"赢者通吃"。
让新 Pattern 也有机会被发现。

## v6.5 PyYAML 替换的真实代价

```
减少:
- frontmatter.py 从 ~250 行减少到 ~70 行
- 累计 6 个 YAML bug 一次性消失
- 加新 prompt / rule 不再需要避开陷阱
- block scalars / inline list / 嵌套 dict 自然支持

代价:
- 加 1 个外部依赖（PyYAML）
- safe_load 默认会把 ISO 日期转成 date 对象 → 加 _StringPreservingLoader 保留为 str
- frontmatter.dump() 输出风格略变（更标准化）

净收益:
高。所有现有 prompt/rule 文件直接受益，未来加新文件不踩坑。
```

## 完整工厂的现状

```
原始素材 ─ingest─→ Asset ─run─→ Plan ─critic─→ Critique ─archive─→ Pattern
   │                  │           │               │                    │
   sha256 去重        类目分组    consumed_assets  weighted_score       reuse_score
   family detect      family_role consumed_patterns  decision rule       core_elements
                                  ↑                                       │
                                  │                                       │
                                  └─── 推荐器 ──── pat_*.md 库 ←─────────┘
                                                  
   每跑一次 archive：库 +1 Pattern
   每跑一次 run：从库里推荐 Top-K
   每被推荐一次：reuse_count += 1
```

工厂真正"转"起来了：
- 第 1 个项目：从零开始 → archive 沉淀 1 个 Pattern
- 第 2 个项目：享受第 1 个项目的沉淀 → 又沉淀 1 个 Pattern
- 第 N 个项目：享受全部历史沉淀 → 自然形成 Pattern 网络

## Design Data Factory 完成度

| 阶段 | 状态 |
|---|---|
| 数据层（9 entity schemas） | ✅ |
| 执行层 ingest | ✅ |
| 执行层 run（含推荐器） | ✅ |
| 执行层 critic | ✅ |
| 执行层 archive | ✅ |
| **闭环：archive → run 推荐反馈** | ✅ |
| Vault staging 写入 | ⏳ P2 |
| 工作流编排（auto pipeline） | ⏳ P2 |

## 下一步建议

至此 Design Data Factory 的**核心数据闭环完成**。接下来 3 个方向价值递减：

### 选项 A：Vault staging 写入 (P2)
让所有产物可以一键同步到真实 Obsidian Vault，保持人工确认 gate。
**价值：把工具变成生产系统。**

### 选项 B：Workflow 编排器 (P2)
单命令跑完 ingest → run → critic → archive，用户只在每一步暂停确认。
**价值：把"工具集"变成"流水线"。**

### 选项 C：推荐器进化 (P2)
- brief_signals 用嵌入相似度替换 lexicon
- 加 anti-pattern（推荐时排除已被替代/废弃的 Pattern）
- 多 LLM 混合（lexicon 第一轮，LLM 第二轮精排）

我建议 **A**：Vault staging 是把工厂从"实验室"变成"生产系统"的关键一步。
B 和 C 都是在 A 之上的优化。

要继续 A 吗？
