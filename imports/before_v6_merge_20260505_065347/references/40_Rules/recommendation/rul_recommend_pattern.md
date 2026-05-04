---
id: "rul_recommend_pattern"
type: rule
schema_version: "1.0"
created_at: "2026-05-04T18:00:00Z"
updated_at: "2026-05-04T18:00:00Z"
status: active
created_by: "human"
source_run_id: null
tags:
  - recommendation
  - pattern
  - meta

rule_version: "1.0.0"
domain: recommendation
applies_to:
  - "skill:design-run"
  - "stage:concept"
  - "target_type:pattern"
precedence: 100
engine: weighted

body:
  # 4 个匹配维度
  dimensions:
    - id: applicability
      label: 适用性匹配
      weight: 0.45
      definition: "Pattern.applicable_when 与 Project 上下文的重叠度"
      computation: |
        score = sum_of(
          project_type in pattern.applicable_when.project_types,
          deliverable_categories ∩ pattern.applicable_when.categories,
          brief_signals_matched / brief_signals_total,
          stage in pattern.applicable_when.stages
        ) / 4 * 5
      anchors:
        1: "几乎不重叠"
        3: "局部匹配（仅类目或仅项目类型）"
        5: "全维度匹配"

    - id: quality
      label: Pattern 自身质量
      weight: 0.25
      definition: "Pattern 的 reuse_score（来自原始 critique）"
      computation: "reuse_score * 5"
      anchors:
        1: "reuse_score < 0.4"
        3: "reuse_score 0.4-0.7"
        5: "reuse_score >= 0.9"

    - id: validation
      label: 历史验证
      weight: 0.20
      definition: "已被多少其他 Project 复用过"
      computation: "min(reuse_count, 5)"
      anchors:
        1: "从未被引用 (reuse_count = 0)"
        3: "被引用 1-2 次"
        5: "被引用 5+ 次"

    - id: recency
      label: 时效性
      weight: 0.10
      definition: "Pattern 创建距今的时间衰减"
      computation: |
        days_old = (now - pattern.created_at).days
        if days_old < 90: 5
        elif days_old < 180: 4
        elif days_old < 365: 3
        elif days_old < 730: 2
        else: 1
      anchors:
        1: ">= 2 年"
        5: "< 90 天"

  # 推荐阈值
  recommendation_threshold: 3.0   # weighted_score 必须 >= 此值才能进入推荐池
  top_k: 3                         # 默认推荐 Top-K
  min_score: 1.5                   # 低于此分数完全不考虑

  # status 过滤
  status_filter:
    accept: [active]
    reject: [draft, archived, deprecated]

  scale: [1, 5]

replaces: null
replaced_by: null

test_cases:
  - id: tc_recommend_perfect_match
    input:
      project:
        project_type: poster_campaign
        deliverable_categories: [poster]
        brief_signals: ["新品发布", "限定", "高端"]
        stage: concept
      pattern:
        applicable_when:
          project_types: [poster_campaign]
          categories: [poster]
          brief_signals: ["新品发布", "限定", "高端"]
          stages: [concept, iteration]
        reuse_score: 0.95
        reuse_count: 3
        days_old: 60
    expect:
      weighted_score_min: 4.5
      recommended: true

  - id: tc_recommend_no_match
    input:
      project:
        project_type: brand_system
        deliverable_categories: [brand]
        brief_signals: ["重塑"]
        stage: concept
      pattern:
        applicable_when:
          project_types: [poster_campaign]
          categories: [poster]
          brief_signals: ["新品发布"]
          stages: [concept]
        reuse_score: 0.5
        reuse_count: 0
        days_old: 100
    expect:
      weighted_score_max: 2.5
      recommended: false

  - id: tc_recommend_high_quality_partial_match
    input:
      project:
        project_type: poster_campaign
        deliverable_categories: [poster, brand]
        brief_signals: ["新品"]
        stage: concept
      pattern:
        applicable_when:
          project_types: [poster_campaign]
          categories: [poster]
          brief_signals: ["新品发布"]
          stages: [concept]
        reuse_score: 0.95
        reuse_count: 5
        days_old: 30
    expect:
      weighted_score_min: 3.5
      recommended: true
---

# Rule: pattern recommendation

## Intent
当 design-run 启动一个新概念阶段时，自动从 30_Patterns/ 拉取与当前 Project 高度相关的
历史 Pattern 进 prompt context。这是 Design Data Factory 闭环的核心机制：让上一次的
设计沉淀真正影响下一次的设计输入。

## 4 个维度
| ID | 名称 | 权重 |
|---|---|---:|
| applicability | 适用性匹配 | 45% |
| quality | Pattern 自身质量 | 25% |
| validation | 历史验证 | 20% |
| recency | 时效性 | 10% |

权重总和：1.00

## 推荐流程
```
1. design-run 启动 → 加载 patterns_dir 中所有 active Pattern
2. 对每个 Pattern 调用 rul_recommend_pattern 计算 weighted_score
3. 过滤: weighted_score >= recommendation_threshold (3.0)
4. 排序: weighted_score 降序
5. 取 Top-K (默认 3)
6. 写入 Plan.consumed_patterns + Pattern.reuse_count += 1
```

## 关键设计

### applicability 占 45% 是有意的
"适用性"是 Pattern 是否相关的硬性条件。一个 reuse_score=0.95 的高质量 Pattern 如果
applicability=1（完全不重叠），加权也才 1.45 + 0.95*1.25 = 2.7 < 3.0 阈值，不会被推荐。
这防止"高质量但不相关"的污染。

### reuse_count 上限封顶 5
被引用 100 次和 5 次没有本质差别——这条规则避免"赢者通吃"。
让新 Pattern 也有机会被发现。

### recency 占 10%（最低）
我们故意不让"新"成为强信号。一个 2 年前的高质量 Pattern 可能比上周新建的 dry-run 占位
更值得复用。

## Change Log
- 1.0.0 (2026-05-04): 初版
