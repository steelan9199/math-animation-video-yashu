#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""版本 + API 锚点守门：确认 0.21.0 的关键结论在本机仍然成立。

为什么要守锚点
------------
`references/manim-api-troubleshooting.md` §3 里那些论断（`Scene.time` 存在、
`CYAN` 不导出、`CENTER` 不存在、`AnnularSector` 顶层已导出…）是**实测结论**，
不是文档抄录。Manim 一升级它们就可能失效，而失效方式是**静默的**：
`hasattr` 变成 False 只在运行时炸，代码看着完全正常。

所以开工前跑一次：版本号不对、或任一锚点漂移 ⇒ 退出码 1，先修文档再开工。

⚠️ 本文件自身的注释也可能写错——注释与检查项同源，不能拿代码互证。
改结论前先实跑本脚本看真实输出，别靠读代码推断
（见 `references/自进化与维护.md` §11.1 循环论证陷阱）。

用法:
    python check_manim_version.py          # 人读的报告
    python check_manim_version.py --json   # 机器可读
退出码:
    0  版本与全部锚点均符合
    1  版本不符或有锚点漂移（此时不要相信 references/ 里的 API 论断）
    2  脚本自身没跑起来（没装 manim 等）
"""
from __future__ import annotations

import json
import sys

EXPECTED_VERSION = "0.21.0"


def probe_manim():
    """返回 (manim, [(锚点名, 是否符合预期, 实测值), ...])。"""
    import manim

    checks = []

    def check(name, ok, actual):
        checks.append((name, bool(ok), actual))

    # 1. Scene 有 time，没有 time_since_start
    from manim import Scene

    check("Scene.time 存在", hasattr(Scene, "time"), hasattr(Scene, "time"))
    check(
        "Scene.time_since_start 不存在",
        not hasattr(Scene, "time_since_start"),
        hasattr(Scene, "time_since_start"),
    )

    # 2. 颜色常量：CYAN/MAGENTA 不导出，TEAL/PINK/GOLD/PURPLE 导出
    for name, should_exist in [
        ("CYAN", False),
        ("MAGENTA", False),
        ("TEAL", True),
        ("PINK", True),
        ("GOLD", True),
        ("PURPLE", True),
    ]:
        present = name in dir(manim)
        check(
            f"manim 导出 {name} == {should_exist}",
            present == should_exist,
            f"实际 {present}",
        )

    # 3. CENTER 常量不存在
    check("无 CENTER 常量", not hasattr(manim, "CENTER"), hasattr(manim, "CENTER"))

    # 4. AnnularSector 顶层已导出（0.21.0 实测），且类名是双 r
    top_level = hasattr(manim, "AnnularSector")
    check("AnnularSector 顶层已导出", top_level, f"实际 {top_level}")
    check(
        "无 AnnulusSector（单 r 错拼）",
        not hasattr(manim, "AnnulusSector"),
        hasattr(manim, "AnnulusSector"),
    )
    try:
        from manim.mobject.geometry.arc import AnnularSector as _Arc

        same = getattr(manim, "AnnularSector", None) is _Arc
        check("顶层与子模块是同一个类对象", same, f"同一对象 {same}")
    except Exception as exc:  # pragma: no cover - 环境异常
        check("AnnularSector 可从子模块 import", False,
              f"{type(exc).__name__}: {exc}")

    # 5. 大写常量总数（文档记录 158 个，仅用于发现命名空间大幅变动）
    upper_count = sum(1 for n in dir(manim) if n.isupper())
    check("大写常量数量级未剧变(>=150)", upper_count >= 150, upper_count)

    return manim, checks


def main() -> int:
    json_mode = "--json" in sys.argv

    try:
        manim, checks = probe_manim()
    except Exception as exc:
        if json_mode:
            print(json.dumps({"ok": False, "fatal": f"{type(exc).__name__}: {exc}"},
                             ensure_ascii=False, indent=2))
        else:
            print(f"[FATAL] 脚本自身跑不起来：{type(exc).__name__}: {exc}")
            print("        确认用的是装了 Manim 的解释器"
                  "（D:\\software\\uv\\envs\\py314-cpu\\Scripts\\python_direct.exe）。")
        return 2

    version = manim.__version__
    version_ok = version == EXPECTED_VERSION
    failed = [c for c in checks if not c[1]]

    if json_mode:
        print(json.dumps(
            {
                "ok": version_ok and not failed,
                "version": version,
                "expected_version": EXPECTED_VERSION,
                "version_ok": version_ok,
                "anchors_total": len(checks),
                "anchors_failed": len(failed),
                "failed": [{"anchor": n, "actual": a} for n, _, a in failed],
            },
            ensure_ascii=False, indent=2))
        return 0 if (version_ok and not failed) else 1

    print(f"Manim 版本：{version}（期望 {EXPECTED_VERSION}） "
          f"{'✅' if version_ok else '❌'}")
    print(f"发行版：{getattr(manim, '__version__', '')} / "
          f"{manim.__file__}")

    width = max(len(n) for n, _, _ in checks)
    print(f"\nAPI 锚点校验（共 {len(checks)} 项）：")
    for name, ok, actual in checks:
        print(f"  {'✅' if ok else '❌'} {name.ljust(width)}   {actual}")

    if version_ok and not failed:
        print("\n✅ 版本与全部锚点均符合，references/ 里的 API 论断仍可信。")
        return 0

    print()
    if not version_ok:
        print(f"🚫 版本不符：{version} != {EXPECTED_VERSION}")
        print(f"   停止对本技能的渲染调用。当前 manim 版本号：{version}，"
              f"不是{EXPECTED_VERSION}，停止对本技能的任何调用。")
    for name, _, actual in failed:
        print(f"🚫 锚点漂移：{name}（实测 {actual}）")
    print("   先到 references/manim-api-troubleshooting.md §3 更新对应结论，"
          "再开工——否则 references 里的 API 写法会静默失效。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())