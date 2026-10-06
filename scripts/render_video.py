#!/usr/bin/env python
"""按 math-animation 连接器同款管线渲染 Manim 场景。

与连接器内部完全一致的三步注入：中文字体 -> ctex -> 风格背景色，
唯一区别是把渲染超时从 120s 放宽（默认 900s），用于 720p 长片。

用法:
    python render_video.py <scene.py> [--quality medium] [--style khan_academy]
                           [--format mp4] [--timeout 900] [--out-dir <dir>]

推荐用装了 Manim 的那个环境跑（脚本自身不需要 Manim，但要import引擎包）：
    D:\\software\\uv\\envs\\py314-cpu\\Scripts\\python_direct.exe

注意：脚本会用 MAMCP_PYTHON 指定「真正跑 Manim 的解释器」。该路径必须存在，
否则引擎会静默回退到 PATH 里的 python（多半没装 Manim，表现为
`No module named 'manim'`）。换环境时必须同步改 ENGINE_PYTHON。
"""
from __future__ import annotations

import argparse
import json
import os
import sys

REPO = r"D:\github\math-animation-mcp"
DEFAULT_OUT = os.path.join(REPO, "animation_output")
ENGINE_PYTHON = r"D:\software\uv\envs\py314-cpu\Scripts\python_direct.exe"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("scene", help="场景 .py 文件路径")
    ap.add_argument("--quality", default="medium",
                    choices=["low", "medium", "high", "4k"])
    ap.add_argument("--style", default="khan_academy",
                    help="风格名，传 none 表示不加风格")
    ap.add_argument("--format", default="mp4", choices=["mp4", "gif", "webm"])
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--out-dir", default=DEFAULT_OUT)
    ap.add_argument("--font", default="LXGW WenKai GB",
                    help="Text()/MarkupText() 的默认中文字体")
    args = ap.parse_args()

    if not os.path.exists(ENGINE_PYTHON):
        sys.exit(
            f"[FATAL] MAMCP_PYTHON 指向的解释器不存在：{ENGINE_PYTHON}\n"
            f"引擎会静默回退到 PATH 里的 python（多半没装 Manim）。\n"
            f"请改本文件顶部的 ENGINE_PYTHON，指向装了 Manim 的解释器。"
        )

    os.environ.setdefault("MAMCP_FONT", args.font)
    os.environ.setdefault("MAMCP_TMP_DIR", os.path.join(REPO, "_render_tmp"))
    os.environ.setdefault("MAMCP_PYTHON", ENGINE_PYTHON)
    sys.path.insert(0, os.path.join(REPO, "src"))

    from math_animation_mcp.tools.render_tools import render_animation

    with open(args.scene, encoding="utf-8") as f:
        code = f.read()

    style = None if args.style.lower() in ("none", "null", "") else args.style

    res = render_animation(
        code,
        quality=args.quality,
        fmt=args.format,
        style=style,
        output_dir=args.out_dir,
        timeout=args.timeout,
    )

    print(json.dumps(
        {
            "success": res.get("success"),
            "file_path": res.get("file_path"),
            "error_msg": (res.get("error_msg") or "")[-1500:],
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0 if res.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
