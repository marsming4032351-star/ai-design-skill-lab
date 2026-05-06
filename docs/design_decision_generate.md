# Design Decision: design-generate — 视觉生产纳入工厂

Date: 2026-05-06
Status: Implemented
Author: Design Data Factory

## Problem

Design Data Factory 的 `run` 阶段只产出文字版 concept directions。真实的设计工作流需要视觉稿作为产出物，而当前生图过程发生在对话里——品牌文档在 Obsidian、菜品照片在微信、生成的海报在 `~/Desktop/临时/lovart-imgs/`——对话关掉后全部散失，没有 Project/Asset/Plan/Run 记录。

## Decision

**新增 `design-generate` 作为工厂的第五个 pipeline stage**，而非独立工具。

生成的视觉稿成为一等实体（Visual），有独立 schema、唯一 ID、可审计的 Run 记录，可被后续的 `critic_visual.py` 评审，通过后可被 `archive_design.py` 沉淀为 Pattern。

## Alternatives Considered

### A: 独立生图工具
不做。这会让生图过程继续在工厂外部发生，与"形成沉淀"的核心目标矛盾。

### B: 把图片路径写入 Plan direction 的 `visual_path` 字段
不做。这样视觉稿只是 Plan 的附属字段，无法独立审计、评分、复用。Visual 必须是独立实体。

### C: 生成即 Pattern，跳过评审
不做。缺少评审环节的生成没有质量保障，沉淀到工厂的知识会是噪声。

## Implementation Details

### 新增实体：Visual

```
id: vis_<timestamp>_<hash>
source_run_id, source_plan_id, source_direction_id  # 溯源
image_path, image_hash, image_size_bytes             # 图片
prompt_used, style_description                       # 生成上下文
llm_mode: dry-run | live                            # 执行模式
generator: lovart | mock                             # 生图引擎
critique_id, critique_score, derived_pattern_id      # 预留字段
```

ID 格式与现有实体一致（`vis_` + 时间戳 + hash），不嵌套 project/direction 信息，避免过长。

### 新增 CLI: scripts/generate_design.py

两种输入模式：
1. **从 Plan 读取**：`--plan <path> --direction dir_001`
2. **手动 prompt**：`--prompt "暗调留白风格..."`

两种生图模式：
1. **dry-run**：生成 mock 占位图（纯色 PNG，640x960），不依赖外部 API
2. **live**：直接调用 Lovart API（需 `LOVART_ACCESS_KEY` + `LOVART_SECRET_KEY`）

输出：
- `vis_<id>.md` — Visual 实体（frontmatter）
- `vis_<id>.jsonl` — Visual 实体（JSON）
- `manifest.jsonl` — 生图元数据（prompt、model、thread_id 等）
- `run_<id>.md` — Run 审计记录

### Lovart 适配层: shared/lovart_hook.py

封装 Lovart OpenClaw API，参考 `~/caihub-feishu-qa/caihub_qa/lovart_provider.py` 的实现模式。Mock 模式用最简 PNG 生成器（无 PIL 依赖），生成 640x960 纯色占位图。

## Tradeoffs

- **没有 hook 模式**：v1 只支持 dry-run 和 live，不做 hook。原因是 Lovart 调用逻辑已经封装在 lovart_hook.py 中，不需要外部脚本中转。后续如果需要接入其他生图后端再加 hook。
- **不依赖 PIL**：mock 占位图用 Python 标准库 `zlib` + `struct` 生成最小 PNG，不渲染文字。真实图片需要 live 模式。
- **单张参考图**：v1 只支持第一张参考图（图生图），多张参考图推迟到 P2。
- **consumed_patterns 留空**：v1 不做 Pattern 驱动的生成，字段预留。

## Consequences

- 工厂从"文字流水线"升级为"文字 + 视觉"双生产
- 每张生成的海报都有完整溯源链：Project → Run → Plan → Direction → Visual → (未来 Critique → Pattern)
- 新增 1 个 schema validator、1 个 Lovart 适配层、1 个 CLI 脚本
- 后续可扩展：`critic_visual.py` 评审视觉稿、`archive_design.py` 沉淀为视觉 Pattern
