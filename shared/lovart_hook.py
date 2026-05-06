"""Lovart hook — 生图引擎适配层。

封装 Lovart API 调用，作为 Design Data Factory 的视觉生产环节。
支持两种模式：
  1. live: 直接调用 Lovart API
  2. mock: 生成占位图（纯色块 + 文字标注）

不依赖 lovart-helper skill，独立调用 Lovart OpenClaw endpoint。
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


class LovartError(RuntimeError):
    pass


class LovartHook:
    """Lovart 生图 hook。"""

    def __init__(
        self,
        access_key: str | None = None,
        secret_key: str | None = None,
        workspace_id: str | None = None,
        api_url: str = "https://api.lovart.ai/openclaw/v1/posters",
        output_dir: str = "data/posters",
    ) -> None:
        self.access_key = access_key or os.environ.get("LOVART_ACCESS_KEY", "")
        self.secret_key = secret_key or os.environ.get("LOVART_SECRET_KEY", "")
        self.workspace_id = workspace_id or os.environ.get("LOVART_WORKSPACE_ID", "")
        self.api_url = api_url
        self.output_dir = output_dir

    @property
    def configured(self) -> bool:
        return bool(self.access_key and self.secret_key)

    def generate_image(
        self,
        prompt: str,
        reference_images: list[str] | None = None,
        model: str = "generate_image_seedream_v4_5",
        output_format: str = "png",
    ) -> dict[str, Any]:
        """生成图片。

        Args:
            prompt: 发送给模型的提示词
            reference_images: 可选参考图本地路径列表（图生图）
            model: Lovart 模型名
            output_format: 输出格式 png/jpeg/webp

        Returns:
            {
                "image_path": "/path/to/image.png",
                "image_hash": "sha256...",
                "image_size_bytes": 12345,
                "output_format": "png",
                "model": "generate_image_seedream_v4_5",
                "prompt_used": "...",
                "metadata": {"width": ..., "height": ..., "thread_id": ...}
            }
        """
        if not self.configured:
            return self._generate_mock(prompt, output_format)

        payload: dict = {
            "skill": "OpenClaw",
            "task": "generate_poster",
            "workspace_id": self.workspace_id,
            "prompt": prompt,
            "inputs": {
                "title": "",
                "subtitle": "",
                "slogan": "",
                "price": "",
                "style": "",
            },
        }

        # 图生图：附加参考图
        if reference_images:
            ref_path = reference_images[0]  # 先支持单张参考图
            ref_data = base64.b64encode(Path(ref_path).read_bytes()).decode("ascii")
            payload["inputs"]["image_base64"] = ref_data
            payload["inputs"]["image_name"] = Path(ref_path).name

        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            self.api_url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "X-Lovart-Access-Key": self.access_key,
                "X-Lovart-Secret-Key": self.secret_key,
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")
            raise LovartError(f"Lovart API 错误 ({e.code}): {detail}") from e
        except Exception as e:
            raise LovartError(f"Lovart 调用失败: {e}") from e

        if body.get("code") not in (0, None) and body.get("success") is not True:
            raise LovartError(f"Lovart 生图失败: {body.get('msg', body)}")

        image_url = body.get("image_url") or body.get("output_url") or body.get("data", {}).get("image_url")
        image_data = body.get("image_base64") or body.get("data", {}).get("image_base64")
        if not image_url and not image_data:
            raise LovartError("Lovart 响应中没有图片")

        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        suffix = f".{output_format}"
        ts = int(time.time() * 1000)
        output_path = Path(self.output_dir) / f"lovart_{ts}{suffix}"

        if image_data:
            output_path.write_bytes(base64.b64decode(image_data))
        else:
            with urllib.request.urlopen(image_url, timeout=60) as resp:
                output_path.write_bytes(resp.read())

        return self._build_result(str(output_path), prompt, model, output_format, body)

    def _build_result(
        self,
        image_path: str,
        prompt: str,
        model: str,
        output_format: str,
        api_response: dict,
    ) -> dict[str, Any]:
        img = Path(image_path)
        content = img.read_bytes()
        return {
            "image_path": str(img),
            "image_hash": hashlib.sha256(content).hexdigest(),
            "image_size_bytes": len(content),
            "output_format": output_format,
            "model": model,
            "prompt_used": prompt,
            "metadata": {
                "thread_id": api_response.get("thread_id"),
            },
        }

    def _generate_mock(
        self,
        prompt: str,
        output_format: str = "png",
    ) -> dict[str, Any]:
        """生成 mock 占位图 — 640x960 纯色块 + 文字标注。

        不依赖 PIL，用最简单的方式写一个 PNG 文件头 + 纯色数据。
        实际上生成一个最小的合法 PNG。
        """
        width, height = 640, 960
        suffix = f".{output_format}"
        ts = int(time.time() * 1000)
        output_path = Path(self.output_dir) / f"mock_visual_{ts}{suffix}"

        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

        # 最小 PNG：1x1 灰色像素，实际这里用一个简化的占位方案
        # 因为没有 PIL，我们直接写一个最小的合法 PNG
        png_data = _minimal_png(width, height, r=64, g=64, b=64)
        output_path.write_bytes(png_data)

        content = output_path.read_bytes()
        return {
            "image_path": str(output_path),
            "image_hash": hashlib.sha256(content).hexdigest(),
            "image_size_bytes": len(content),
            "output_format": output_format,
            "model": "mock",
            "prompt_used": prompt,
            "metadata": {
                "width": width,
                "height": height,
                "note": "mock placeholder — no PIL available for text rendering",
            },
        }


def _minimal_png(width: int, height: int, r: int, g: int, b: int) -> bytes:
    """生成一个最小的合法 PNG 文件（无 zlib 依赖问题）。"""
    import io
    import struct
    import zlib

    def chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    buf = io.BytesIO()
    # PNG signature
    buf.write(b"\x89PNG\r\n\x1a\n")
    # IHDR
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)  # 8bit RGB
    buf.write(chunk(b"IHDR", ihdr_data))
    # IDAT — 每行: filter_byte(0) + RGB pixels
    raw = b""
    scanline = bytes([0, r, g, b]) * width  # filter=0 + pixels
    for _ in range(height):
        raw += scanline
    compressed = zlib.compress(raw, 9)
    buf.write(chunk(b"IDAT", compressed))
    # IEND
    buf.write(chunk(b"IEND", b""))
    return buf.getvalue()


def generate_image(
    prompt: str,
    reference_images: list[str] | None = None,
    model: str = "generate_image_seedream_v4_5",
    output_format: str = "png",
    output_dir: str = "data/posters",
) -> dict[str, Any]:
    """模块级便捷函数。"""
    hook = LovartHook(output_dir=output_dir)
    return hook.generate_image(prompt, reference_images, model, output_format)
