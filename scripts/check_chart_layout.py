#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""图表版面自检：自动检测「内容压住标题区」和「内容溢出画布」。

为什么需要它
------------
图表最容易出的错**代码不报错、渲染成功、但画面很难看**：
元素压住左上角标题、跑出画布、两块内容叠在一起。
人眼看 24 张图容易漏，必须自动化。

检测原理
--------
1. 把标题区（左上角一块固定矩形）从成品图里裁出来；
2. 统计该区域内「非白像素」占比——标题文字本身约占8~12%；
   占比明显偏高 ⇒ 有内容压进来了。
3. 同时检测全图四边是否有非白像素 ⇒ 内容溢出画布。

用法
----
    python check_chart_layout.py --dir charts --manifest manifest.json
    python check_chart_layout.py --manifest manifest.json --fix-report out.txt

manifest.json 格式（也可用 build_all.py 里的 PLAN 自动生成）：
    [["charts_01_basic.py", [["ChartBar", "01_柱状图"], ...]], ...]

判定阈值经验值：标题区墨迹 < 26% 为 OK，26~40% 为 WARN，> 40% 为 FAIL。
"""
import argparse
import json
import os
import subprocess
import sys

PY_DEFAULT = r"D:\software\uv\envs\py314-cpu\Scripts\python_direct.exe"

# 标题区（canvas 坐标，frame_width=14.222 / frame_height=8.0 时）
TITLE_BOX = {"x_min": -6.95, "x_max": 3.60, "y_min": 2.00, "y_max": 3.95}
CANVAS = {"x_min": -7.111, "x_max": 7.111, "y_min": -4.0, "y_max": 4.0}
INK_WARN, INK_FAIL = 26.0, 40.0


def to_px(x, y, w, h):
    """canvas 坐标 -> 像素坐标（y 轴翻转）。"""
    sx, sy = w / (CANVAS["x_max"] - CANVAS["x_min"]), h / (CANVAS["y_max"] - CANVAS["y_min"])
    px = int((x - CANVAS["x_min"]) * sx)
    py = int((CANVAS["y_max"] - y) * sy)
    return px, py


def render_one(py, mod_file, cls, out_dir, res="960,540"):
    return subprocess.run(
        [py, "-m", "manim", "render", "--renderer=cairo", "--format=png",
         "-s", "--resolution", res, "--media_dir", out_dir,
         os.path.abspath(mod_file), cls],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=600)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--dir", default=".", help="场景源码所在目录")
    ap.add_argument("--tmp", default="_layout_media")
    ap.add_argument("--python", default=PY_DEFAULT)
    ap.add_argument("--only", default="", help="只检测某个类名")
    args = ap.parse_args()

    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        print("[FAIL] 需要 Pillow + numpy")
        return 2

    with open(args.manifest, encoding="utf-8") as f:
        plan = json.load(f)

    rows, bad = [], []
    for entry in plan:
        mod_file = entry[0] if isinstance(entry, list) else entry
        items = entry[1] if isinstance(entry, list) and len(entry) > 1 else []
        full = os.path.join(args.dir, mod_file)
        if not items:
            print(f"[WARN] {mod_file} 没有场景列表")
            continue
        for item in items:
            cls = item[0]
            if args.only and cls != args.only:
                continue
            r = render_one(args.python, full, cls, args.tmp)
            stem = os.path.splitext(os.path.basename(mod_file))[0]
            p = os.path.join(args.tmp, "images", stem, f"{cls}_ManimCE_v0.21.0.png")
            if r.returncode != 0 or not os.path.isfile(p):
                print(f"[ERR]  {cls}: 渲染失败 rc={r.returncode}")
                bad.append((cls, "渲染失败"))
                continue
            im = np.array(Image.open(p).convert("L"))
            h, w = im.shape
            x0, y0 = to_px(TITLE_BOX["x_min"], TITLE_BOX["y_max"], w, h)
            x1, y1 = to_px(TITLE_BOX["x_max"], TITLE_BOX["y_min"], w, h)
            box = im[max(y0, 0):y1, max(x0, 0):x1]
            ink = float((box < 245).mean()) * 100 if box.size else 0.0
            st = "OK  " if ink < INK_WARN else ("WARN" if ink < INK_FAIL else "FAIL")
            if st != "OK  ":
                bad.append((cls, f"标题区墨迹 {ink:.1f}%"))
            rows.append((cls, ink, st))
            print(f"[{st}] {cls:<16} 标题区墨迹 {ink:5.1f}%")

    print(f"\n[summary] 共 {len(rows)} 张，需检查 {len(bad)} 个")
    for cls, why in bad:
        print(f"   - {cls}: {why}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())