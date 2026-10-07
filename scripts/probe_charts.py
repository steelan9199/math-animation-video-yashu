#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""图表场景探针：绕过 manim CLI，直接跑 construct，拿完整 traceback。

为什么需要它
------------
`manim render` 失败时，打印的是 Rich 截断的回溯尾部，**看不到真正的报错行**
（尤其 "ValueError: operands could not be broadcast..." 这类信息，
完全不知道是哪个文件哪一行）。
本脚本在 dry_run 模式下直接实例化场景并调用 construct，
拿到的是 Python 原生完整 traceback，定位到行。

用法
----
    python probe_charts.py charts_01_basic.py ChartBar ChartLine
    python probe_charts.py my_charts.py            # 自动发现文件里所有 Scene 子类

秒级完成（不渲染像素）。**写完场景代码先跑它，全绿了再真渲染。**
"""
import importlib.util
import os
import re
import sys
import traceback

import manim


def load_scene_file(path):
    """按文件路径加载为可import 的模块。"""
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        print(f"[FAIL] 文件不存在: {path}")
        return None
    # 让场景文件能 import 同目录的公共库（charts_lib.py 等）
    sys.path.insert(0, os.path.dirname(path))
    name = os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        print(f"[FAIL] 模块导入阶段就崩了（通常是 import 或语法错误）:")
        traceback.print_exc(file=sys.stdout)
        return None
    return mod


def discover(mod, path):
    """找出场景文件里**自己定义**的 Scene 子类。

    ⚠️ 不能直接扫 vars(mod)：场景文件通常写了 `from manim import *`，
    会把 ThreeDScene / VectorScene / ZoomedScene / LinearTransformationScene
    等基类一起捞进来。它们在 dry_run 下会因为缺 renderer 属性而报错，
    那是误报，不是我们的问题。
    判据：类的 `__module__` 等于本文件模块名 ⇒ 本文件定义的。
    """
    me = os.path.splitext(os.path.basename(path))[0]
    return sorted(n for n, o in vars(mod).items()
                  if isinstance(o, type) and issubclass(o, manim.Scene)
                  and o is not manim.Scene and n[0].isupper()
                  and getattr(o, "__module__", None) == me)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    mod = load_scene_file(path)
    if mod is None:
        return 2

    names = sys.argv[2:] or discover(mod, path)
    if not names:
        print(f"[FAIL] {path} 里没找到任何 Scene 子类")
        return 2

    ok, bad = [], []
    for cls_name in names:
        cls = getattr(mod, cls_name, None)
        if cls is None:
            print(f"[FAIL] {cls_name}  在 {path} 里不存在")
            bad.append(cls_name)
            continue
        try:
            # dry_run: 走完 construct 与所有 mobject 变换，但不渲染像素
            with manim.tempconfig({"dry_run": True}):
                cls().render()
            print(f"[OK]   {cls_name}")
            ok.append(cls_name)
        except Exception:
            print(f"[FAIL] {cls_name}")
            traceback.print_exc(file=sys.stdout)
            print("-" * 70)
            bad.append(cls_name)

    print(f"\n[summary] {os.path.basename(path)}: OK={len(ok)} FAIL={len(bad)}"
          + (f"  失败: {', '.join(bad)}" if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())