# Codex 操作指南

本文档面向当前仓库 `ai-design-skill-lab`，用于指导如何让 Codex 协助维护、扩展和发布这个 Design Data Factory 实验项目。

## 1. 仓库结构速览

当前仓库没有根目录 `README.md`。主要项目说明集中在 `CHANGES.md`、`docs/CHANGES.md` 和 `docs/v6_diff_report.md`。

核心目录：

- `scripts/`：命令入口。
  - `scan_inbox.py`：扫描素材 inbox，分类、分组、生成 `manifest.jsonl`、资产索引和 ingest run log。
  - `run_design.py`：读取 Project、manifest、Prompt、Pattern，生成 concept stage Plan；支持 dry-run 和外部 LLM hook。
  - `critic_design.py`：对 Plan direction 进行 rubric 评分，生成 Critique。
  - `archive_design.py`：把通过评审的 direction 归档为可复用 Pattern，并可回写 Plan、Project、Asset notes。
- `shared/`：脚本共用模块。
  - `frontmatter.py`：Markdown frontmatter 读写，基于 PyYAML。
  - `schema.py`：Asset、Run、Plan、Critique、Pattern 等实体校验。
  - `prompt_loader.py`、`prompt_render.py`：Prompt 实体加载与渲染。
  - `project_loader.py`、`plan_loader.py`、`critique_loader.py`、`pattern_loader.py`：实体加载。
  - `rule_loader.py`、`rule_engine.py`、`rubric_engine.py`、`recommendation_engine.py`：规则分类、评分、Pattern 推荐。
  - `manifest.py`、`entity_updater.py`：manifest 读取和实体回写。
- `tests/`：当前测试集中主要验证 `run_design.py --help` 的依赖链、推荐 rule 加载和 `reuse_count` 自增。
- `references/`：项目样例、规则、Prompt、Pattern 和运行记录。
  - `10_Projects/`：Project 实体样例。
  - `30_Patterns/`：Pattern 库。
  - `40_Rules/`：分类 rule、rubric rule、推荐 rule。
  - `50_Prompts/`：run、critic、archive 使用的 Prompt 实体。
  - `90_Runs/`：历史 Run 记录。
  - `schemas/`：Plan、Pattern、Critique 等 schema 文档。
- `docs/`：项目说明文档。
- `imports/`：历史导入和合并前备份。
- `prototypes/`：早期 prototype。
- `repos/`：外部 skills 仓库副本，通常只作为参考，不建议在日常任务里修改。

## 2. 可以让 Codex 做什么

Codex 适合在这个仓库里做这些工作：

- 扫描当前项目状态，解释仓库结构、脚本入口、数据流和实体关系。
- 运行或调试 `scripts/` 下的 pipeline：ingest、run、critic、archive。
- 基于 `references/` 增加或修改 Project、Prompt、Rule、Pattern 示例。
- 为新功能补测试，例如扩展 `tests/test_run_design_dependencies.py` 或新增聚焦测试。
- 修复 schema、frontmatter、loader、recommendation、rubric 等共享模块中的 bug。
- 新增 design-run 能力，例如更细的 Pattern 推荐策略、asset 选择策略、prompt context 字段。
- 接入真实 LLM，但建议先通过 `--llm hook --llm-hook PATH` 的隔离方式接入。
- 生成和检查 Plan、Critique、Pattern、Run 记录。
- 做代码审查，重点看脚本副作用、实体回写、schema 覆盖和测试缺口。
- 在完成验证后 commit、push、打 tag。

Codex 不应默认做这些事：

- 直接删除 `references/`、`imports/`、`repos/`、历史运行记录或用户素材。
- 未经确认改写远程历史，例如 force push、reset、rebase 已发布分支。
- 未经确认把 dry-run 输出同步到真实 Obsidian Vault 或生产目录。
- 未经确认调用真实 LLM API、消耗额度或上传敏感素材。

## 3. 场景命令模板

以下命令默认在仓库根目录执行。

### 检查项目状态

```bash
pwd
git status --short --branch
git log --oneline --decorate -5
rg --files
```

检查关键目录：

```bash
find scripts shared tests references docs -maxdepth 2 -type f | sort
```

检查 Python 入口是否还能加载：

```bash
python3 scripts/run_design.py --help
python3 scripts/scan_inbox.py --help
python3 scripts/critic_design.py --help
python3 scripts/archive_design.py --help
```

### 跑测试

当前仓库没有 `pyproject.toml`、`requirements.txt` 或 Makefile。测试入口直接用 pytest：

```bash
python3 -m pytest -q
```

如果环境缺少 pytest：

```bash
python3 -m pip install pytest
python3 -m pytest -q
```

如果环境缺少 PyYAML：

```bash
python3 -m pip install PyYAML
python3 -m pytest -q
```

### 修复 bug

给 Codex 的任务模板：

```text
/goal 修复 <具体 bug 描述>。要求：
1. 先复现问题，给出失败命令和错误输出摘要。
2. 定位最小相关文件，不做无关重构。
3. 先补一个能失败的回归测试。
4. 修复实现。
5. 跑 python3 -m pytest -q。
6. 通过后提交 commit，不自动 push，等我确认。
```

常用本地命令：

```bash
python3 -m pytest -q
python3 scripts/run_design.py --help
git diff -- scripts shared tests references
```

### 新增 design-run 功能

适合改动的文件通常是：

- `scripts/run_design.py`
- `shared/prompt_render.py`
- `shared/recommendation_engine.py`
- `shared/pattern_loader.py`
- `shared/schema.py`
- `references/50_Prompts/prm_run_concept.md`
- `tests/`

给 Codex 的任务模板：

```text
/goal 为 design-run 新增 <功能名>。要求：
1. 扫描 scripts/run_design.py、shared/prompt_render.py、shared/schema.py、references/50_Prompts/prm_run_concept.md、tests。
2. 说明输入、输出和副作用。
3. 先加测试覆盖新行为。
4. 实现时保持 dry-run 可用，不引入真实 API 依赖。
5. 跑 python3 -m pytest -q。
6. 生成变更摘要，等待我确认是否 commit。
```

design-run dry-run 示例：

```bash
python3 scripts/run_design.py \
  --project references/10_Projects/prj_acme_q4_campaign/project.md \
  --manifest <staging-dir>/manifest.jsonl \
  --prompts-dir references/50_Prompts \
  --out <run-output-dir> \
  --patterns-dir references/30_Patterns \
  --rules-dir references/40_Rules \
  --llm dry-run
```

### 接入真实 LLM

当前 `run_design.py`、`critic_design.py`、`archive_design.py` 支持 `--llm hook`，由外部可执行脚本从 stdin 接收 RenderedPrompt JSON，并向 stdout 输出 JSON。优先用 hook 接入真实 LLM，避免把 provider SDK、密钥和网络逻辑直接耦合进主 pipeline。

hook 调用模板：

```bash
python3 scripts/run_design.py \
  --project references/10_Projects/prj_acme_q4_campaign/project.md \
  --manifest <staging-dir>/manifest.jsonl \
  --prompts-dir references/50_Prompts \
  --out <run-output-dir> \
  --patterns-dir references/30_Patterns \
  --rules-dir references/40_Rules \
  --llm hook \
  --llm-hook ./scripts/<your_llm_hook>
```

Critic hook：

```bash
python3 scripts/critic_design.py \
  --plan <run-output-dir>/<plan-id>.md \
  --project references/10_Projects/prj_acme_q4_campaign/project.md \
  --direction dir_001 \
  --rules-dir references/40_Rules \
  --prompts-dir references/50_Prompts \
  --out <critic-output-dir> \
  --llm hook \
  --llm-hook ./scripts/<your_llm_hook>
```

人工确认点：

- 使用哪个模型和 provider。
- 是否允许网络访问。
- API key 存放方式，不能提交到 git。
- 是否允许上传素材、brief、客户信息。
- 是否允许产生费用。

### 生成 plan.md / plan.jsonl

`run_design.py` 会在 `--out` 目录写入：

- `<plan-id>.md`
- `<plan-id>.jsonl`
- `<plan-id>.prompt.txt`
- `<run-id>.md`

命令模板：

```bash
python3 scripts/run_design.py \
  --project references/10_Projects/prj_acme_q4_campaign/project.md \
  --manifest <staging-dir>/manifest.jsonl \
  --prompts-dir references/50_Prompts \
  --out <run-output-dir> \
  --patterns-dir references/30_Patterns \
  --rules-dir references/40_Rules \
  --top-k 3 \
  --llm dry-run
```

禁用 Pattern 推荐：

```bash
python3 scripts/run_design.py \
  --project references/10_Projects/prj_acme_q4_campaign/project.md \
  --manifest <staging-dir>/manifest.jsonl \
  --prompts-dir references/50_Prompts \
  --out <run-output-dir> \
  --no-recommend \
  --llm dry-run
```

强制指定 Pattern：

```bash
python3 scripts/run_design.py \
  --project references/10_Projects/prj_acme_q4_campaign/project.md \
  --manifest <staging-dir>/manifest.jsonl \
  --prompts-dir references/50_Prompts \
  --out <run-output-dir> \
  --patterns-dir references/30_Patterns \
  --rules-dir references/40_Rules \
  --pattern pat_dryrun \
  --llm dry-run
```

### 做代码审查

给 Codex 的任务模板：

```text
请 review 当前改动。要求：
1. 以代码审查口径输出，先列问题，按严重程度排序。
2. 必须引用文件和行号。
3. 重点检查实体 schema、脚本副作用、测试覆盖、真实 LLM hook、安全边界。
4. 不要直接修改代码，除非我明确要求。
```

本地辅助命令：

```bash
git status --short --branch
git diff --stat
git diff -- scripts shared tests references docs
python3 -m pytest -q
```

### 自动 commit + push

建议只在测试通过且 diff 已审阅后执行。

```bash
git status --short --branch
git diff --stat
python3 -m pytest -q
git add <files>
git commit -m "<type(scope): message>"
git push origin main
```

给 Codex 的任务模板：

```text
/goal 完成开发后自动 commit + push。要求：
1. 先检查 git status 和 git diff，确认只提交本任务相关文件。
2. 跑 python3 -m pytest -q。
3. commit message 使用 Conventional Commit。
4. push 前再次确认当前分支和 remote。
5. 如果发现无关改动、测试失败、需要 force push 或远程不匹配，停止并问我。
```

### 打 tag

打轻量 tag：

```bash
git status --short --branch
git log --oneline --decorate -3
git tag vX.Y.Z
git push origin vX.Y.Z
```

打带说明的 tag：

```bash
git status --short --branch
git log --oneline --decorate -3
git tag -a vX.Y.Z -m "vX.Y.Z: <release summary>"
git push origin vX.Y.Z
```

检查远程 tag：

```bash
git ls-remote origin refs/tags/vX.Y.Z
```

## 4. 推荐的 /goal 命令清单

可直接复制给 Codex 使用：

```text
/goal 扫描 ai-design-skill-lab 当前结构，说明 scripts/shared/tests/references 的职责，并列出可以安全运行的检查命令。
```

```text
/goal 跑完整验证。要求执行 python3 -m pytest -q，并额外检查 scripts/run_design.py --help、scripts/critic_design.py --help、scripts/archive_design.py --help。
```

```text
/goal 修复当前测试失败。要求先复现，再定位，再最小修复，最后跑 python3 -m pytest -q。
```

```text
/goal 为 design-run 增加 <功能>。要求先补测试，保持 dry-run 可用，不能引入未确认的真实 LLM 调用。
```

```text
/goal 接入真实 LLM hook。要求新增独立 hook 示例，不提交 API key，不默认联网；主 pipeline 仍支持 dry-run。
```

```text
/goal 基于 references/10_Projects/prj_acme_q4_campaign/project.md 和指定 manifest 生成 plan.md / plan.jsonl。先 dry-run，输出文件写到我指定的 staging 目录。
```

```text
/goal review 当前 diff。要求按严重程度列问题，引用文件行号，不直接改代码。
```

```text
/goal 完成开发后自动 commit + push。要求测试通过、diff 已审阅、只提交本任务相关文件，push 到 origin main。
```

```text
/goal 发布 vX.Y.Z。要求检查 clean tree、确认 HEAD、更新必要文档、跑测试、打 tag，并在我确认后 push tag。
```

## 5. 必须人工确认的操作

以下操作必须先停下来确认：

- 删除、移动或批量覆盖文件，尤其是 `references/`、`imports/`、`repos/`、`docs/`、历史 Run 和 Pattern。
- 对真实素材目录、Obsidian Vault、客户项目目录写入或同步。
- 使用 `archive_design.py` 的回写能力修改 Project、Plan、Asset notes，除非明确指定允许。
- 执行真实 LLM hook、联网请求、安装依赖、使用 API key 或可能产生费用的命令。
- 提交包含密钥、客户敏感信息、素材路径、真实素材摘要的 diff。
- `git push origin main`、push tag、创建 release。
- force push、rebase、reset、checkout 覆盖本地修改、删除 tag、改写历史。
- 提交前发现工作区有无关改动，尤其是用户手动改过的文件。
- 修改 `repos/` 下外部仓库副本，除非任务明确要求。
- 把 generated output 当作 canonical references 覆盖原文件。

建议 Codex 在这些动作前输出：

```text
我将要执行 <具体动作>，影响 <文件/远程/目录>。这一步不可自动推断为安全，请确认是否继续。
```

## 6. 安全工作流建议

常规开发顺序：

```text
scan -> plan -> test -> implement -> test -> review diff -> commit -> push
```

推荐检查门禁：

```bash
git status --short --branch
git diff --stat
python3 -m pytest -q
```

发布门禁：

```bash
git status --short --branch
git log --oneline --decorate -5
python3 -m pytest -q
git ls-remote origin refs/heads/main
```

对这个仓库最重要的原则：

- dry-run 是默认安全路径。
- 真实 LLM 走 hook，避免污染核心 pipeline。
- `references/` 是实体和规则的主语料，修改要小心。
- `shared/schema.py` 是数据契约，改 schema 必须同步测试和样例。
- `archive_design.py` 有回写副作用，默认先用临时目录验证。
- commit 和 push 前必须看 `git status`、`git diff --stat` 和测试结果。
