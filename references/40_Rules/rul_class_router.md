---
id: "rul_class_router"
type: rule
schema_version: "1.0"
created_at: "2026-05-04T15:00:00Z"
updated_at: "2026-05-04T15:00:00Z"
status: active
created_by: "human"
source_run_id: null
tags:
  - classification
  - router
  - meta

rule_version: "1.0.0"
domain: classification
applies_to:
  - "skill:design-ingest"
  - "category:*"
precedence: 1000   # 最高，作为最终仲裁者
engine: hybrid

body:
  description: |
    仲裁器规则：协调 7 个 category 规则的命中结果，决定最终 category / confidence / family_role。
    单条 category 规则只回答"我能否命中"，本规则负责"最终归哪类"。

  steps:
    # ─────────────────────────────────────────
    # Step 1: 调用所有 category 规则收集候选
    # ─────────────────────────────────────────
    - id: collect_candidates
      action: invoke_all
      target_rules:
        - "rul_class_brand"
        - "rul_class_proposal"
        - "rul_class_space"
        - "rul_class_soft_decoration"
        - "rul_class_reference"
        - "rul_class_poster"
        - "rul_class_process"
      output: candidates
      output_shape:
        - rule_id: string
          category: string
          confidence: enum  # high | medium | low | null
          evidence: string[]
          precedence: int

    # ─────────────────────────────────────────
    # Step 2: 过滤未命中的候选
    # ─────────────────────────────────────────
    - id: filter_hits
      action: filter
      condition: "candidate.category != null"
      output: hits

    # ─────────────────────────────────────────
    # Step 3: 路径上下文增强（reference 路径优先）
    # ─────────────────────────────────────────
    - id: path_context_boost
      action: boost
      rules:
        # 如果文件位于 reference 类文件夹中，reference 候选升 +20 precedence
        - if: "asset.path matches /(references?|refs|参考|案例|竞品|调研|灵感|inspiration|research)/"
          then:
            target_category: reference
            precedence_delta: +20

    # ─────────────────────────────────────────
    # Step 4: 处理 process 共生（关键）
    # ─────────────────────────────────────────
    # process 不作为主类目，而是作为 family_role
    - id: extract_family_role
      action: split
      condition: "process IN hits.categories AND len(hits) > 1"
      effect:
        - 把 process 从 hits 中移除
        - 在最终输出添加 family_role: variant
        - evidence 中保留 process 的依据

    # ─────────────────────────────────────────
    # Step 5: 仲裁 - 单一命中
    # ─────────────────────────────────────────
    - id: single_hit
      action: select
      condition: "len(hits) == 1"
      output:
        category: hits[0].category
        confidence: hits[0].confidence
        evidence: hits[0].evidence
        needs_review: "hits[0].confidence != high"

    # ─────────────────────────────────────────
    # Step 6: 仲裁 - 多命中（按 precedence + confidence 加权）
    # ─────────────────────────────────────────
    - id: multi_hit
      action: rank_and_select
      condition: "len(hits) >= 2"
      ranking_formula: |
        score = precedence * 1.0 + confidence_weight(confidence) * 100
        confidence_weight: high=3, medium=2, low=1
      tie_breaker: "category 字典序 + needs_review=true"
      output:
        category: top_candidate.category
        confidence: |
          if top.score - second.score >= 50: top.confidence
          else: downgrade(top.confidence, by=1)  # 拉低一档
        evidence: union(all_hits.evidence)
        needs_review: |
          top.score - second.score < 50  → true
          OR top.confidence != high       → true
        conflicts:
          - reason: "multiple categories matched"
          - candidates: [hits.category list]

    # ─────────────────────────────────────────
    # Step 7: 仲裁 - 全部未命中
    # ─────────────────────────────────────────
    - id: no_hit
      action: fallback
      condition: "len(hits) == 0"
      output:
        category: unknown
        confidence: low
        evidence: ["no rule matched"]
        needs_review: true

    # ─────────────────────────────────────────
    # Step 8: LLM 兜底（可选，opt-in）
    # ─────────────────────────────────────────
    - id: llm_fallback
      action: invoke_prompt
      condition: "category == unknown AND config.enable_llm_fallback == true"
      prompt_id: "prm_classify_visual"   # 待 P1 创建
      output_schema:
        category: enum
        confidence: enum
        rationale: string
      override_only_if: "llm.confidence in {high, medium}"

  output_shape:
    category: enum
    confidence: enum
    evidence: string[]
    needs_review: bool
    family_role: enum | null     # original | variant | final | derivative | null
    conflicts: object | null

replaces: null
replaced_by: null

test_cases:
  - id: tc_router_01_single
    input:
      path: "/projects/foo/品牌/VI手册.pdf"
    expect:
      category: brand
      confidence: high
      family_role: null
      needs_review: false

  - id: tc_router_02_multi_clear_winner
    input:
      path: "/projects/x/poster_logo_overlay.psd"
    explanation: "poster + brand 双命中，brand precedence=80 > poster=60"
    expect:
      category: brand
      confidence: medium  # 因为冲突，拉低一档
      conflicts:
        candidates: ["brand", "poster"]
      needs_review: true

  - id: tc_router_03_process_split
    input:
      path: "/projects/x/main_kv_v3.psd"
    explanation: "poster (kv) + process (v3) 双命中。process 不是主类，仅作 family_role"
    expect:
      category: poster
      confidence: high
      family_role: variant
      evidence_contains: ["kv", "v3 模式"]

  - id: tc_router_04_path_boost
    input:
      path: "/projects/foo/参考/some_brand_logo.png"
    explanation: "看起来命中 brand，但路径有 '参考' → 升级 reference"
    expect:
      category: reference
      confidence: high
      conflicts:
        candidates: ["brand", "reference"]

  - id: tc_router_05_no_hit
    input:
      path: "/random/IMG_4837.jpg"
    expect:
      category: unknown
      confidence: low
      needs_review: true

  - id: tc_router_06_close_tie
    input:
      path: "/x/lighting_proposal.pdf"
    explanation: "soft-decoration (lighting) + proposal (proposal+pdf) 都命中且分差小"
    expect:
      confidence: medium
      needs_review: true
      conflicts:
        candidates: ["soft-decoration", "proposal"]
---

# Rule: classification router（仲裁器）

## Intent
协调 7 条 category 规则，决定最终 category / confidence / family_role。
**单条 category 规则只判"是否命中"，仲裁权全部下放到本规则。**

## 设计要点

### 1. precedence 排序
```
brand (80) > proposal (78) > space (75) > soft-decoration (70)
        > reference (65) > poster (60) > process (50)
```

### 2. process 不作为主类目
process 与其他类目"共生"。文件名带 v3 / draft 不应让它失去原本的 category 身份，
而是标记 `family_role = variant`。

### 3. 路径上下文 > 文件名
当文件位于 `/参考/` `/refs/` 等明确路径下，**reference 应当胜出**，
即使文件名命中其他类目（reference 类目本身就是"作为参考使用"）。

### 4. 多命中且分差小 → 拉低置信度 + needs_review
两个候选 score 差 < 50 时，即使有 winner 也降一档置信度，强制人工 review。

### 5. LLM 兜底是 opt-in
仅在 `unknown` 时调用，且需要显式 `enable_llm_fallback = true`。
默认不调用，避免 P0 阶段引入 LLM 成本与不确定性。

## 输出契约（被 design-ingest 消费）

```yaml
category: brand              # 最终类目
confidence: medium           # 最终置信度
evidence:                    # 所有依据合并
  - "brand: logo, .ai"
  - "poster: kv"
needs_review: true           # 是否进 review queue
family_role: variant         # 资产族角色（可选）
conflicts:                   # 冲突详情（可选）
  candidates: ["brand", "poster"]
```

## precedence: 1000
最高优先级，是所有 category 规则的"上层调度"。
其他规则的 precedence 在 50~80 之间。

## 与 design-ingest 的契约

design-ingest 的 `classify()` 函数应当：
1. 加载所有 `domain: classification` 的 active rules
2. **直接调用 `rul_class_router`**（它会 invoke 其他规则）
3. 接收 router 的输出作为最终分类结果

**不要让 design-ingest 直接遍历 7 条 category 规则**——那是 router 的职责。

## Change Log
- 1.0.0 (2026-05-04): 初版；引入 hybrid 引擎；定义 8 步仲裁流程；process 共生机制
