---
id: "rul_score_concept_direction"
type: rule
schema_version: "1.0"
created_at: "2026-05-04T16:00:00Z"
updated_at: "2026-05-04T16:00:00Z"
status: active
created_by: "human"
source_run_id: null
tags:
  - scoring
  - concept
  - rubric

rule_version: "1.0.0"
domain: scoring
applies_to:
  - "skill:design-critic"
  - "stage:concept"
  - "target_type:plan_direction"
precedence: 100
engine: weighted

body:
  # 评分量表（所有维度共享）
  scale: [1, 5]
  scale_anchors:
    1: "完全不达标 / 严重偏离"
    2: "明显短板 / 需要重做"
    3: "基本可用 / 有保留意见"
    4: "良好 / 小修可发"
    5: "优秀 / 直接采纳"

  # 评分维度（权重总和必须 = 1.0）
  dimensions:
    - id: "strategy_fit"
      label: "战略契合度"
      weight: 0.25
      definition: "方向是否精准回应 brief 中的核心战略意图"
      anchors:
        1: "完全偏离 brief 主张"
        3: "基本符合，但关键诉求覆盖不全"
        5: "精准命中战略意图，且有放大效果"

    - id: "differentiation"
      label: "差异化"
      weight: 0.20
      definition: "在同类项目和市场中的差异化清晰度"
      anchors:
        1: "高度同质化，无记忆点"
        3: "有差异点但不显著"
        5: "在同行/历史方案中具备明显独特性"

    - id: "executability"
      label: "可执行性"
      weight: 0.15
      definition: "在预算、工期、技术可行范围内能落地"
      anchors:
        1: "明显无法在项目周期内实现"
        3: "可行但需协调多方资源"
        5: "现有团队能直接执行"

    - id: "brand_consistency"
      label: "品牌一致性"
      weight: 0.15
      definition: "与客户既有品牌资产/调性的一致性"
      anchors:
        1: "与品牌定位明显冲突"
        3: "不冲突但缺乏品牌识别度"
        5: "强化品牌资产，可复用"

    - id: "craft_potential"
      label: "工艺潜力"
      weight: 0.10
      definition: "方向能否承载高质量的视觉/材料/空间执行"
      anchors:
        1: "结果几乎不可能高完成度"
        3: "需要资深执行者把控"
        5: "结果质量天然优秀"

    - id: "reuse_potential"
      label: "复用潜力"
      weight: 0.15
      definition: "未来可被抽象为 Pattern 复用到其他项目"
      anchors:
        1: "高度项目特定，无复用价值"
        3: "局部可复用（某个元素）"
        5: "整体可作为 Pattern 沉淀"

  # 决策规则
  pass_threshold: 3.5
  fail_threshold: 2.5
  decision_rule:
    pass:
      conditions:
        - "weighted_score >= pass_threshold"
        - "all dimensions >= 2"
    fail:
      conditions:
        - "weighted_score < fail_threshold OR any dimension == 1"
    revise:
      default: true   # 不满足 pass 也不满足 fail → revise

replaces: null
replaced_by: null

test_cases:
  - id: tc_score_pass
    inputs:
      scores:
        strategy_fit: 4
        differentiation: 4
        executability: 4
        brand_consistency: 4
        craft_potential: 3
        reuse_potential: 4
    expect:
      weighted_score: 3.9   # 0.25*4 + 0.20*4 + 0.15*4 + 0.15*4 + 0.10*3 + 0.15*4 = 3.9
      decision: pass
  - id: tc_score_fail_low_avg
    inputs:
      scores: {strategy_fit: 2, differentiation: 2, executability: 2,
               brand_consistency: 2, craft_potential: 2, reuse_potential: 2}
    expect:
      weighted_score: 2.0
      decision: fail
  - id: tc_score_fail_one_critical
    inputs:
      scores: {strategy_fit: 1, differentiation: 5, executability: 5,
               brand_consistency: 5, craft_potential: 5, reuse_potential: 5}
    expect:
      weighted_score: 4.0
      decision: fail   # 任何维度 == 1 → fail
  - id: tc_score_revise
    inputs:
      scores: {strategy_fit: 3, differentiation: 3, executability: 3,
               brand_consistency: 3, craft_potential: 3, reuse_potential: 3}
    expect:
      weighted_score: 3.0
      decision: revise   # 介于 pass 和 fail 之间
---

# Rubric: concept direction 评分

## Intent
对 design-run 产出的概念方向（plan_direction）进行 6 维评分，决定是否能进入 iteration 阶段。

## 6 个维度
| ID | 名称 | 权重 |
|---|---|---|
| strategy_fit | 战略契合度 | 25% |
| differentiation | 差异化 | 20% |
| executability | 可执行性 | 15% |
| brand_consistency | 品牌一致性 | 15% |
| craft_potential | 工艺潜力 | 10% |
| reuse_potential | 复用潜力 | 15% |

权重总和：1.00

## 决策规则
- weighted_score ≥ 3.5 且所有维度 ≥ 2 → **pass**
- weighted_score < 2.5 或任意维度 = 1 → **fail**
- 其他 → **revise**

## 设计要点

### "任意维度 = 1 → fail" 是硬约束
即使加权平均很高，单一维度 1 分也意味着方向有致命缺陷。例如战略 1 分但执行 5 分 = 拍马屁式的方案。

### reuse_potential 占 15%
这是 Design Data Factory 的特异性：评审不只看本项目，还看能否沉淀为 Pattern。这把"工厂化"的目标内化进每一次评审。

## Change Log
- 1.0.0 (2026-05-04): 初版，6 维度评分；权重和阈值待真实使用后微调
