#!/usr/bin/env python3
"""
lint_map.py — MAP.md 校验脚本

按 MAP.md 第 7.2 节的 7 条规则校验仓库导航地图与实际代码是否一致。
设计原则：
- 只读，不修改任何文件
- 失败时返回非零退出码，便于本地或 pre-commit 调用
- 每条规则都有明确的报错信息，告诉作者去哪里改

用法：
    python3 scripts/lint_map.py            # 默认从 repo root 找 MAP.md
    python3 scripts/lint_map.py --verbose  # 打印每条规则的检查细节
    python3 scripts/lint_map.py --map PATH # 指定 MAP.md 路径（用于测试）

退出码：
    0  全部通过
    1  存在 FAIL
    2  脚本本身错误（找不到 MAP.md / 仓库根 等）
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


# ---------- 数据结构 ----------

@dataclass
class CheckResult:
    rule_id: str
    name: str
    passed: bool = False
    details: list[str] = field(default_factory=list)

    def render(self, verbose: bool = False) -> str:
        icon = "✅" if self.passed else "❌"
        head = f"{icon} [{self.rule_id}] {self.name}"
        if self.passed and not verbose:
            return head
        if not self.details:
            return head
        body = "\n".join(f"    · {d}" for d in self.details)
        return f"{head}\n{body}"


# ---------- 工具函数 ----------

def find_repo_root(start: Path) -> Path:
    """从 start 向上找第一个含 MAP.md 或 .git 的目录。"""
    p = start.resolve()
    for parent in [p, *p.parents]:
        if (parent / "MAP.md").exists() or (parent / ".git").exists():
            return parent
    raise FileNotFoundError("找不到仓库根目录（未发现 MAP.md 或 .git）")


def extract_backtick_paths(text: str) -> list[str]:
    """从 markdown 文本里提取所有反引号包裹的、看起来像路径的字符串。

    判定为"路径"的启发：
    - 包含 / 或以 .py / .md / .sh / .yaml / .yml / .html 结尾
    - 不含空格
    - 不是纯命令（如 python3 -m pytest）
    """
    matches = re.findall(r"`([^`\n]+)`", text)
    paths: list[str] = []
    for m in matches:
        s = m.strip()
        if " " in s:
            # 像命令，不是单独路径
            continue
        if "/" in s or s.endswith((".py", ".md", ".sh", ".yaml", ".yml", ".html")):
            # 去掉行内的特殊修饰（如末尾标点）
            s = s.rstrip(",.;:)）")
            if s:
                paths.append(s)
    # 去重保序
    seen = set()
    deduped = []
    for p in paths:
        if p not in seen:
            deduped.append(p)
            seen.add(p)
    return deduped


def extract_section(text: str, section_heading_prefix: str) -> str:
    """提取以 section_heading_prefix 开头的章节内容，到下一个 # 级别标题为止。

    例如 section_heading_prefix='## 3.' 会匹配 '## 3. xxx' 这一节。
    """
    lines = text.splitlines()
    out: list[str] = []
    in_section = False
    for line in lines:
        if line.startswith(section_heading_prefix):
            in_section = True
            out.append(line)
            continue
        if in_section and line.startswith("## ") and not line.startswith(section_heading_prefix):
            break
        if in_section:
            out.append(line)
    return "\n".join(out)


# ---------- 规则实现 ----------

def rule_1_map_exists(repo_root: Path, map_path: Path, _: str) -> CheckResult:
    r = CheckResult("R1", "MAP.md 必须存在于 repo root")
    if not map_path.exists():
        r.passed = False
        r.details.append(f"未找到 {map_path}")
        return r
    if map_path.parent.resolve() != repo_root.resolve():
        r.passed = False
        r.details.append(
            f"MAP.md 应在 repo root（期望 {repo_root}，实际 {map_path.parent}）"
        )
        return r
    r.passed = True
    return r


def rule_2_backtick_paths_exist(repo_root: Path, _map_path: Path, text: str) -> CheckResult:
    r = CheckResult("R2", "所有反引号路径在仓库中真实存在")
    paths = extract_backtick_paths(text)
    missing: list[str] = []
    # 一些 MAP 里会出现的"模式占位符"，不应当作真实路径校验
    placeholder_patterns = [
        r"^docs/<.*>/?$",          # docs/<output-type>/
        r"^docs/xiaohongshu-\*/?$",  # docs/xiaohongshu-*/
    ]

    def is_placeholder(p: str) -> bool:
        return any(re.match(pat, p) for pat in placeholder_patterns)

    for p in paths:
        if is_placeholder(p):
            continue
        # 去掉 trailing /
        candidate = p.rstrip("/")
        if not (repo_root / candidate).exists():
            missing.append(p)

    if missing:
        r.passed = False
        r.details.append(f"以下反引号路径不存在（共 {len(missing)} 条）：")
        for p in missing:
            r.details.append(f"  - `{p}`")
    else:
        r.passed = True
        r.details.append(f"检查了 {len(paths)} 条路径，全部存在")
    return r


def rule_3_scripts_have_help(repo_root: Path, _map_path: Path, text: str) -> CheckResult:
    r = CheckResult("R3", "MAP 中提到的 scripts/*.py 必须支持 --help")
    paths = extract_backtick_paths(text)
    scripts = [p for p in paths if p.startswith("scripts/") and p.endswith(".py")]
    failures: list[str] = []
    checked = 0
    for s in scripts:
        full = repo_root / s
        if not full.exists():
            # rule_2 会报，这里跳过
            continue
        checked += 1
        try:
            proc = subprocess.run(
                ["python3", str(full), "--help"],
                cwd=repo_root,
                capture_output=True,
                timeout=10,
                text=True,
            )
            if proc.returncode != 0:
                failures.append(
                    f"{s}: --help 退出码 {proc.returncode}（stderr 前 80 字: "
                    f"{proc.stderr.strip()[:80]}）"
                )
        except subprocess.TimeoutExpired:
            failures.append(f"{s}: --help 超过 10 秒未返回")
        except Exception as e:
            failures.append(f"{s}: 调用异常 {e!r}")

    if failures:
        r.passed = False
        r.details.append(f"检查了 {checked} 个 script，{len(failures)} 个失败：")
        for f in failures:
            r.details.append(f"  - {f}")
    else:
        r.passed = True
        r.details.append(f"检查了 {checked} 个 script，全部支持 --help")
    return r


def rule_4_docs_paths_exist(repo_root: Path, _map_path: Path, text: str) -> CheckResult:
    r = CheckResult("R4", "路由表中所有 docs/... 路径必须存在（除显式标 ⚠️ 的）")
    # 找路由表区段
    routing = extract_section(text, "## 2.")
    # 提取 docs/ 开头的反引号路径
    docs_paths = [
        p for p in extract_backtick_paths(routing)
        if p.startswith("docs/")
    ]
    # 标 ⚠️ 的行整行跳过
    warned_lines = {
        line for line in routing.splitlines() if "⚠️" in line
    }
    missing: list[str] = []
    for p in docs_paths:
        # 若该路径在标 ⚠️ 的行里出现过，则跳过
        skip = any(f"`{p}`" in line for line in warned_lines)
        if skip:
            continue
        # 去通配符 *
        candidate = p.rstrip("/")
        if "*" in candidate:
            # 检查父目录有没有匹配项
            parent = (repo_root / candidate).parent
            stem = Path(candidate).name.replace("*", "")
            if not parent.exists() or not any(
                stem in c.name for c in parent.iterdir()
            ):
                missing.append(p)
            continue
        if not (repo_root / candidate).exists():
            missing.append(p)
    if missing:
        r.passed = False
        r.details.append("以下 docs 路径在路由表中但不存在：")
        for p in missing:
            r.details.append(f"  - `{p}`")
    else:
        r.passed = True
        r.details.append(f"检查了 {len(docs_paths)} 条 docs 路径")
    return r


def rule_5_tbd_count(repo_root: Path, _map_path: Path, text: str) -> CheckResult:
    r = CheckResult("R5", '"待补" / "TBD" 出现次数 ≤ 已标 ⚠️ 的条目数')
    tbd_count = len(re.findall(r"(待补|TBD)", text))
    warn_count = text.count("⚠️")
    if tbd_count > warn_count:
        r.passed = False
        r.details.append(
            f"待补/TBD 出现 {tbd_count} 次，⚠️ 标记 {warn_count} 个；"
            f"差额 {tbd_count - warn_count} 个未声明的占位"
        )
    else:
        r.passed = True
        r.details.append(f"待补 {tbd_count} 次，⚠️ {warn_count} 个，合规")
    return r


def rule_6_wording_consistency(repo_root: Path, _map_path: Path, text: str) -> CheckResult:
    r = CheckResult("R6", "措辞一致性：harness 实际行为 vs MAP 描述")
    runtime_file = repo_root / "harness" / "runtime.py"
    if not runtime_file.exists():
        r.passed = True
        r.details.append("harness/runtime.py 不存在，跳过本规则")
        return r

    runtime_text = runtime_file.read_text(encoding="utf-8", errors="ignore")
    # 启发式判断：harness/runtime.py 是否真的调用了 scripts/ 的 CLI
    # 判据 1：import scripts. 或 from scripts
    # 判据 2：subprocess 调用 scripts/...py
    imports_scripts = bool(re.search(
        r"^\s*(from\s+scripts|import\s+scripts)", runtime_text, re.MULTILINE
    ))
    calls_scripts_cli = bool(re.search(
        r"scripts/\w+\.py", runtime_text
    ))
    actually_calls_pipeline = imports_scripts or calls_scripts_cli

    section_31 = extract_section(text, "### 3.1")

    # 禁用词（未来态描述，不应在 3.1 当前状态里出现）
    forbidden_phrases = [
        "Harness 复用 Pipeline 的各步骤",
        "Harness 调度 Pipeline",
        "共享 shared 层",  # 这是 3.2 目标态的措辞，不应进 3.1
    ]
    # 必含词（如果 harness 当前不调用 pipeline）
    required_phrase = "不调用 Pipeline CLI"

    problems: list[str] = []
    if not actually_calls_pipeline:
        # 当前状态确实是 mock，MAP 3.1 必须明示
        if required_phrase not in section_31:
            problems.append(
                f'harness/runtime.py 当前未调用 scripts/*.py，'
                f'但 MAP 3.1 未包含措辞 "{required_phrase}"'
            )
        for phrase in forbidden_phrases:
            if phrase in section_31:
                problems.append(
                    f'harness/runtime.py 当前未调用 scripts/*.py，'
                    f'但 MAP 3.1 出现了未来态措辞 "{phrase}"'
                )
    else:
        # 真的接上了，MAP 3.1 不应再说"不调用 Pipeline CLI"
        if required_phrase in section_31:
            problems.append(
                f"harness/runtime.py 已经调用 scripts/*.py，"
                f"但 MAP 3.1 仍保留陈旧措辞 \"{required_phrase}\"——"
                f"该把当前/目标关系图合并或更新"
            )

    if problems:
        r.passed = False
        r.details.extend(problems)
    else:
        r.passed = True
        r.details.append(
            f"harness 实际调用 pipeline = {actually_calls_pipeline}，"
            f"与 MAP 3.1 描述一致"
        )
    return r


def rule_7_maturity_covers_routes(repo_root: Path, _map_path: Path, text: str) -> CheckResult:
    r = CheckResult("R7", "成熟度地图必须覆盖路由表中所有 scripts 入口")
    routing = extract_section(text, "## 2.")
    maturity = extract_section(text, "## 6.")
    route_scripts = {
        p for p in extract_backtick_paths(routing)
        if p.startswith("scripts/") and p.endswith(".py")
    }
    # 排除元工具
    route_scripts.discard("scripts/lint_map.py")

    missing = [s for s in sorted(route_scripts) if s not in maturity]
    if missing:
        r.passed = False
        r.details.append("以下路由入口未在第 6 节成熟度地图中出现：")
        for s in missing:
            r.details.append(f"  - `{s}`")
    else:
        r.passed = True
        r.details.append(f"路由表 {len(route_scripts)} 个 scripts 入口全部覆盖")
    return r


# ---------- 主流程 ----------

RULES: list[tuple[str, Callable]] = [
    ("R1", rule_1_map_exists),
    ("R2", rule_2_backtick_paths_exist),
    ("R3", rule_3_scripts_have_help),
    ("R4", rule_4_docs_paths_exist),
    ("R5", rule_5_tbd_count),
    ("R6", rule_6_wording_consistency),
    ("R7", rule_7_maturity_covers_routes),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="MAP.md 校验脚本")
    parser.add_argument("--map", type=Path, default=None,
                        help="MAP.md 路径（默认从当前目录向上找）")
    parser.add_argument("--verbose", action="store_true",
                        help="打印每条规则的检查细节")
    parser.add_argument("--skip-help-check", action="store_true",
                        help="跳过 R3（实际调用 scripts --help，可能很慢）")
    args = parser.parse_args()

    try:
        start = args.map.parent if args.map else Path.cwd()
        repo_root = find_repo_root(start)
        map_path = args.map if args.map else (repo_root / "MAP.md")
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 2

    if not map_path.exists():
        print(f"❌ 找不到 MAP.md: {map_path}", file=sys.stderr)
        return 2

    text = map_path.read_text(encoding="utf-8")

    print(f"=== Linting {map_path} (repo: {repo_root}) ===\n")

    results: list[CheckResult] = []
    for rule_id, fn in RULES:
        if rule_id == "R3" and args.skip_help_check:
            r = CheckResult("R3", "MAP 中 scripts/*.py 支持 --help")
            r.passed = True
            r.details.append("已通过 --skip-help-check 跳过")
            results.append(r)
            continue
        try:
            results.append(fn(repo_root, map_path, text))
        except Exception as e:
            r = CheckResult(rule_id, f"规则执行异常")
            r.passed = False
            r.details.append(f"{type(e).__name__}: {e}")
            results.append(r)

    for r in results:
        print(r.render(verbose=args.verbose))

    failed = [r for r in results if not r.passed]
    print()
    if failed:
        print(f"❌ 失败 {len(failed)}/{len(results)} 条规则")
        return 1
    print(f"✅ 全部 {len(results)} 条规则通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
