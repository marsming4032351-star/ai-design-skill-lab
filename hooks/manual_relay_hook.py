#!/usr/bin/env python3
"""Manual LLM relay hook.

行为分两种模式（通过环境变量控制）：

模式 A: HOOK_MODE=dump
- 从 stdin 读 prompt JSON
- 写到 $HOOK_REQUEST_FILE（默认 /tmp/llm_request.json）
- 在 stderr 打印提示
- exit 2（让 skill 知道是手动模式中断，不是失败）

模式 B: HOOK_MODE=load
- 从 stdin 读 prompt JSON（忽略，仅做 protocol 一致性）
- 读 $HOOK_RESPONSE_FILE（默认 /tmp/llm_response.json）
- 输出到 stdout
"""

import os
import pathlib
import sys


REQ = pathlib.Path(os.getenv("HOOK_REQUEST_FILE", "/tmp/llm_request.json"))
RESP = pathlib.Path(os.getenv("HOOK_RESPONSE_FILE", "/tmp/llm_response.json"))
mode = os.getenv("HOOK_MODE", "dump")

if mode == "dump":
    payload = sys.stdin.read()
    REQ.write_text(payload, encoding="utf-8")
    print(f"\n📋 Prompt 已写到 {REQ}", file=sys.stderr)
    print(f"请把这个文件内容贴给 Claude/GPT，把回复存到 {RESP}", file=sys.stderr)
    print("然后用 HOOK_MODE=load 重跑同样的命令\n", file=sys.stderr)
    sys.exit(2)
elif mode == "load":
    _ = sys.stdin.read()
    if not RESP.exists():
        print(f"ERROR: {RESP} 不存在。先用 HOOK_MODE=dump 模式跑一次。", file=sys.stderr)
        sys.exit(1)
    sys.stdout.write(RESP.read_text(encoding="utf-8"))
    sys.exit(0)
else:
    print(f"ERROR: 未知 HOOK_MODE={mode!r}（应为 dump / load）", file=sys.stderr)
    sys.exit(1)
