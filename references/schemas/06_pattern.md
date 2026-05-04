# Schema · Pattern

> Pattern = 抽象出的可复用设计模式。**不可变**（一旦发布）。由 `design-archive` 产出，
> 是 Design Data Factory 的最终沉淀物。Pattern 让历史项目变成未来项目的输入。

## 字段定义

| 字段 | 类型 | 必填 | 说明 |
|---|---|:---:|---|
| `id` | string | ✓ | `pat_<slug>` |
| `type` | const | ✓ | 固定为 `pattern` |
| `schema_version` | string | ✓ | 当前 `1.0` |
| `created_at` | ISO8601 | ✓ | |
| `updated_at` | ISO8601 | ✓ | |
| `status` | enum | ✓ | `draft` / `active` / `archived` / `deprecated` |
| `created_by` | string | ✓ | 通常 `skill:design-archive` |
| `source_run_id` | string | ✓ | 产生此 Pattern 的 archive run |
| `tags` | string[] | | |
| **专属字段** | | | |
| `pattern_version` | string | ✓ | semver |
| `category` | enum | ✓ | 与 Asset.category 一致 |
| `title` | string | ✓ | 人类可读名称（≤ 30 字） |
| `summary` | string | ✓ | 一句话核心主张（≤ 200 字） |
| `applicable_when` | object | ✓ | 适用条件（结构见下） |
| `not_applicable_when` | string[] | | 反例条件 |
| `core_elements` | object[] | ✓ | 模式构成要素（≥ 1 must_have） |
| `evidence_assets` | string[] | ✓ | 至少 2 个 Asset id 作为证据 |
| `derived_from_projects` | string[] | ✓ | 来源 Project id（≥ 1） |
| `derived_from_runs` | string[] | ✓ | critic + archive 的 run 链（≥ 1） |
| `derived_from_critique_id` | string | ✓ | **v5 新增**：直接产生此 Pattern 的 critique，便于追溯质量背书 |
| `reuse_score` | float | ✓ | 0.0~1.0，复用潜力评分 |
| `reuse_count` | int | ✓ | 被引用次数（其他 project.pattern_refs） |
| `related_patterns` | string[] | | 相关 Pattern id |
| `replaces` | string \| null | | |
| `replaced_by` | string \| null | | |
| `usage_examples` | object[] | | 使用示例 |

### applicable_when 子结构

```yaml
applicable_when:
  project_types: [poster_campaign]
  categories: [poster]
  client_traits: ["high-end", "tech"]
  brief_signals: ["新品发布", "限定"]
  stages: [concept, iteration]
```

### core_elements 子结构

```yaml
core_elements:
  - id: "elem_001"
    aspect: composition         # composition | color | typography | material | motion | cultural
    description: "三段式构图：上 30% 主视觉物，中 50% 标题，下 20% 信息层"
    must_have: true
    parameters:
      top_ratio: 0.30
      middle_ratio: 0.50
      bottom_ratio: 0.20
```

### usage_examples 子结构

```yaml
usage_examples:
  - project_id: "prj_acme_q4_campaign"
    asset_id: "ast_a1b2c3d4e5f6"
    note: "首次使用，client 反馈正面"
```

## 校验规则

```
required: 全部上面标 ✓
constraints:
  - id MUST match pattern: ^pat_[a-z0-9_]+$
  - len(title) <= 30
  - len(summary) <= 200
  - len(evidence_assets) >= 2
  - len(derived_from_projects) >= 1
  - len(derived_from_runs) >= 1
  - core_elements MUST contain at least one element with must_have=true
  - reuse_score in [0.0, 1.0]
  - reuse_count >= 0
  - status == active 时禁止修改 core_elements / applicable_when
  - 升级走 replaces / replaced_by
```

## 反向引用规则（archive 写入后强制执行）

archive 在写出 Pattern 后必须更新以下实体：

```
1. Plan: status (reviewed → adopted), adopted_direction_id, derived_pattern_refs[]
2. Project: derived_pattern_refs[], updated_at
3. Asset (in evidence_assets): pattern_refs append (idempotent)
```

任一更新失败应 rollback 写入：archive 是事务性的。

## 反模式

- ❌ 凭空创建 Pattern（无 evidence） → 必须从真实 critic=pass 的 direction 抽取
- ❌ 一个 Pattern 描述多个无关元素 → 拆成多个 Pattern + related_patterns 互链
- ❌ 修改 active Pattern 的 core_elements → 必须发新版
- ❌ 项目特化逻辑写进 Pattern（"仅用于 ACME"） → Pattern 是通用的，特化用 applicable_when
- ❌ Pattern 直接引用文件路径 → 用 Asset id
