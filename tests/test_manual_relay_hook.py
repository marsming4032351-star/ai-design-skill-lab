from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "manual_relay_hook.py"


def _run_hook(
    *,
    stdin: str,
    mode: str,
    request_file: Path,
    response_file: Path,
) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "HOOK_MODE": mode,
        "HOOK_REQUEST_FILE": str(request_file),
        "HOOK_RESPONSE_FILE": str(response_file),
    }
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=stdin,
        text=True,
        capture_output=True,
        check=False,
        cwd=ROOT,
        env=env,
    )


def test_manual_relay_dump_writes_prompt_and_exits_with_manual_code(tmp_path: Path) -> None:
    request_file = tmp_path / "request.json"
    response_file = tmp_path / "response.json"
    prompt = '{"system":"x","user":"y"}'

    result = _run_hook(
        stdin=prompt,
        mode="dump",
        request_file=request_file,
        response_file=response_file,
    )

    assert result.returncode == 2
    assert request_file.read_text(encoding="utf-8") == prompt
    assert result.stdout == ""
    assert f"Prompt 已写到 {request_file}" in result.stderr
    assert f"回复存到 {response_file}" in result.stderr


def test_manual_relay_load_outputs_saved_response(tmp_path: Path) -> None:
    request_file = tmp_path / "request.json"
    response_file = tmp_path / "response.json"
    response = '{"result": "ok"}'
    response_file.write_text(response, encoding="utf-8")

    result = _run_hook(
        stdin="{}",
        mode="load",
        request_file=request_file,
        response_file=response_file,
    )

    assert result.returncode == 0
    assert result.stdout == response
    assert result.stderr == ""


def test_manual_relay_rejects_unknown_mode(tmp_path: Path) -> None:
    result = _run_hook(
        stdin="{}",
        mode="bogus",
        request_file=tmp_path / "request.json",
        response_file=tmp_path / "response.json",
    )

    assert result.returncode == 1
    assert "未知 HOOK_MODE='bogus'" in result.stderr
