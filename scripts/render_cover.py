#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""渲染微信公众号封面（静态 PNG，走 manim cairo 单帧）。

与 render_video.py 的区别：
  - 只出 PNG，不出 mp4（-s 只保存最后一帧）
  - 不注入默认中文字体（封面由场景代码自己指定字体）
  - 额外打印 board 尺寸、检查字体回退、并把成品拷贝到 --out

用法：
  python render_cover.py <scene.py> <ClassName> [--res 1800x766] [--out 输出.png]
                       [--media-dir 目录] [--timeout 900]

例：
  python render_cover.py chart_mcp_cover_scene.py CoverScene ^
      --res 1800x766 --out "公众号封面_吊打各种图表的MCP_1800x766.png"
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import time

PY_DEFAULT = r"D:\software\uv\envs\py314-cpu\Scripts\python_direct.exe"


def main():
    ap = argparse.ArgumentParser(description="manim 微信公众号封面渲染")
    ap.add_argument("scene", help="场景 .py 路径")
    ap.add_argument("cls", help="场景类名（ASCII，必须是 class Xxx(Scene)）")
    ap.add_argument("--res", default="1800x766",
                    help="分辨率 宽x高，默认 1800x766（2.35:1 微信大图）")
    ap.add_argument("--out", default="", help="成品拷贝目标（PNG）")
    ap.add_argument("--media-dir", default="_cover_media", help="manim 中间产物目录")
    ap.add_argument("--timeout", type=int, default=900, help="超时秒数")
    ap.add_argument("--python", default=PY_DEFAULT, help="渲染用 Python")
    args = ap.parse_args()

    scene = os.path.abspath(args.scene)
    if not os.path.isfile(scene):
        print(f"[cover][FAIL] 场景文件不存在: {scene}")
        return 2

    # 解析分辨率并反推 frame 比例（写进日志，便于核对）
    try:
        w, h = (int(x) for x in args.res.lower().split("x"))
    except ValueError:
        print(f"[cover][FAIL] --res 格式应为 宽x高，如 1800x766，收到: {args.res}")
        return 2
    print(f"[cover] 目标 {w}x{h}  比例 {w / h:.3f}:1"
          f"  （2.35=微信大图 1:1=小图）")

    media_dir = os.path.abspath(args.media_dir)
    # ⚠️ manim 的 --resolution 只接受 "宽,高"（逗号），传 "1800x766" 会报
    #    "Resolution option is invalid" 且**不产出任何文件**。
    res_arg = f"{w},{h}"
    cmd = [
        args.python, "-m", "manim", "render",
        "--renderer=cairo",          # 纯 CPU、抗锯齿、无 GPU 依赖
        "--format=png",              # 静态图
        "-s",                        # 只保存最后一帧
        "--resolution", res_arg,
        "--media_dir", media_dir,
        scene, args.cls,
    ]
    print("[cover] " + subprocess.list2cmdline(cmd))

    t0 = time.time()
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=args.timeout, env=env)
    except subprocess.TimeoutExpired:
        print(f"[cover][FAIL] 超时 {args.timeout}s仍未完成")
        return 3
    dt = time.time() - t0

    log = (proc.stdout or b"").decode("utf-8", "replace") + \
          (proc.stderr or b"").decode("utf-8", "replace")
    # stdout 不回传的机器上，靠日志文本判定成败
    with open("_cover_render.log", "w", encoding="utf-8") as f:
        f.write(log)

    # --- 必查项 ---
    fallback = re.findall(r"falling back[^\n]*", log, flags=re.I)
    if fallback:
        print(f"[cover][WARN] 字体回退 {len(fallback)} 处，中文可能不是指定字体：")
        for line in fallback[:5]:
            print("   ", line.strip())
    errs = [ln for ln in log.splitlines()
            if re.search(r"\bError\b|Traceback", ln)]
    if errs:
        print(f"[cover][WARN] 日志含 {len(errs)} 行报错，前 5 行：")
        for line in errs[:5]:
            print("   ", line.strip())

    # --- 定位产物：<media_dir>/images/<模块名>/<Class>_ManimCE_v0.21.0.png ---
    # ⚠️ 必须按「本次渲染之后才生成」过滤。manim 有哈希缓存：场景文件没改时它会
    #    跳过重渲染，media_dir 里留着上一轮的 PNG。若只按文件名取最新的，
    #    就会把**上一轮的旧图**当成新产物交付（假成功，最坑的一种）。
    stale = 2.0        # 允许 2 秒时钟/写入精度误差
    imgs = []
    for root, _, files in os.walk(media_dir):
        for fn in files:
            if fn.lower().endswith(".png") and fn.startswith(args.cls):
                p = os.path.join(root, fn)
                if os.path.getmtime(p) >= t0 - stale:
                    imgs.append((os.path.getmtime(p), p))
    if not imgs:
        # 缓存跳过 or 渲染失败，都会走到这里
        recent = []
        for root, _, files in os.walk(media_dir):
            for fn in files:
                if fn.lower().endswith(".png") and fn.startswith(args.cls):
                    p = os.path.join(root, fn)
                    recent.append((os.path.getmtime(p), p))
        if recent:
            print("[cover][FAIL] media_dir 里只有旧产物，本次没有重新渲染。")
            print("        原因：manim 对未改动的场景文件会命中哈希缓存并跳过渲染。")
            print("        处理：改一下场景文件（加个空行也算），或删掉 media_dir 再跑。")
        else:
            print("[cover][FAIL] 没找到产物 PNG，检查 _cover_render.log")
        if errs:
            print("        日志报错行：")
            for line in errs[:5]:
                print("   ", line.strip())
            print("        常见原因：--resolution 必须是 '宽,高'（逗号）而不是 '宽x高'；"
                  "类名必须 ASCII 且与文件中 class 名一致。")
        return 4
    src = max(imgs)[1]

    print(f"[cover] 渲染完成 用时 {dt:.1f}s  产物 {src}")

    # --- 拷贝成品 ---
    if args.out:
        dst = os.path.abspath(args.out)
        shutil.copy2(src, dst)
        size = os.path.getsize(dst) // 1024
        print(f"[cover][OK] 已交付 {dst}  ({size} KB)")
    else:
        print("[cover] 未指定 --out，产物留在 media_dir")

    print("[cover] 提醒：必须用读图工具亲眼看一遍成品，核对"
          "「中文字形 / 四边留白不被裁 / 公式可见 / 元素不重叠」四项。")
    return 0


if __name__ == "__main__":
    sys.exit(main())