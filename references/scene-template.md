# 场景模板与常用片段（二维）

从下面这个模板改，比从零写快，且自带本机已验证的配色与正确写法。

> **版本锁定：Manim Community Edition 0.21.0**（勿升级、勿混用 3b1b 版）
> 模板里的 API 结论都在该版本实测过。开工前可跑
> `<本技能目录>/scripts/check_manim_version.py` 确认锚点未漂移。

> **要做真 3D（`ThreeDScene`）？** 本文只讲二维，整篇改读
> **`references/scene-template-3d.md`**（3D-1~3D-10）。
> 3D 的居中、运镜、配色插值都有独立的坑，白底二维模板里的经验不能直接套用。

## 最小可靠模板（白底 / 可汗学院风）

```python
from manim import *
import numpy as np

INK = "#21242C"      # 正文深色（白底必须显式上色）
BLUE = "#1865F2"     # 主曲线 / 主色
TEAL = "#14BF96"     # 第二色
ORAN = "#FF914D"     # 强调色
RED = "#D92916"      # 高亮色
AXC = "#7B8794"      # 坐标轴
GRIDC = "#E4E7EE"    # 网格
FONT = "Noto Sans SC"   # 中文必须显式指定字体

XLEN, YLEN = 10.8, 4.4
YSHIFT = DOWN * 0.75


class MyScene(Scene):          # 类名必须 ASCII，渲染器靠它取场景名
    def construct(self):
        self.camera.background_color = "#FFFFFF"

        grid = NumberPlane(
            x_range=[-PI, 2 * PI, PI / 2], y_range=[-2.5, 2.5, 1],
            x_length=XLEN, y_length=YLEN,
            background_line_style={"stroke_color": GRIDC, "stroke_width": 1},
            axis_config={"stroke_opacity": 0},
        ).shift(YSHIFT)

        ax = Axes(
            x_range=[-PI, 2 * PI, PI / 2], y_range=[-2.5, 2.5, 1],
            x_length=XLEN, y_length=YLEN,
            axis_config={"color": AXC, "stroke_width": 2.5,
                         "include_tip": True, "include_numbers": False},
        ).shift(YSHIFT)

        title = Text("标题", font=FONT, font_size=38, color=INK).to_corner(UL, buff=0.45)

        # MathTex 默认白色：白底必须先整组压深色，再给子串上色
        formula = MathTex(r"y=", r"A", r"\sin(", r"\omega", r"x+", r"\varphi", r")",
                          font_size=46)
        formula.set_color(INK)
        formula[1].set_color(ORAN)
        formula.to_corner(UR, buff=0.45)

        self.play(FadeIn(title), run_time=1.0)
        self.play(Create(grid), Create(ax), run_time=1.0)
        self.play(Write(formula), run_time=1.0)

        # 参数扫描：一个 ValueTracker + 一个 always_redraw（每幕至少要有一个）
        a = ValueTracker(1.0)
        wave = always_redraw(lambda: ax.plot(
            lambda x: a.get_value() * np.sin(x),
            x_range=[-PI, 2 * PI], color=BLUE, stroke_width=4.5))
        self.add(wave)
        self.play(a.animate.set_value(2.0), run_time=2.0, rate_func=smooth)
        self.wait(0.8)

        # 清理 always_redraw 对象用 remove，不要 FadeOut
        self.remove(wave)
        self.wait(1.2)          # 结尾留白，避免突然黑屏
```

## 常用片段

### 卡片式布局（流程图 / 对比图最好用）

⚠️ 卡片内文字用 `fill_card()` 换算成场景坐标，别手填 `move_to([0, y, 0])`。
`Line`/`Arrow` 端点必须三维、`always_redraw` 回调必须零参数、
`VGroup` 只有 `.add()` 没有 `.append()`——这几个坑的完整解释见
`references/pitfalls.md`「构造类三个硬性写法」与「动画机制」表。

```python
INK = "#21242C"; GRIDC = "#E4E7EE"; GRAY = "#6B7280"
# 中文字体：讲论文/学术内容用 Noto Sans SC（黑体，正式）；讲基础数学用 LXGW WenKai GB（楷体，教材感）。
# ⚠️ family 名必须精确匹配（含尾部 GB），写错会静默回退到 Sans —— 渲染日志搜"falling back"必查。
FONT = "Noto Sans SC"

# fill_card() 的实现见 references/pitfalls.md「构造类三个硬性写法」第 3 条
# （为什么不能手填 move_to([0, y, 0])），此处只给用法。


def card(w, h, fill="#F4F6FB", stroke=GRIDC, radius=0.18):
    r = RoundedRectangle(width=w, height=h, corner_radius=radius)
    r.set_fill(fill, opacity=1.0).set_stroke(stroke, width=1.4)
    return r


# 用法：先定位 → 再填字 → 最后整体 arrange
a = card(2.9, 2.1).move_to([-3.55, 0.55, 0])
fill_card(a, [("基础模型", 25, INK, 0.5),
              ("W0", 32, BLUE, -0.08),
              ("指令遵循正常", 18, GRAY, -0.68)])

b = card(2.9, 2.1).move_to([0.0, 0.55, 0])
fill_card(b, [("创意写作预训练", 24, INK, 0.5)])

plus = Text("+", font=FONT, font_size=34, color=GRAY).move_to([-1.75, 0.55, 0])
row = VGroup(a, plus, b).arrange(RIGHT, buff=0.42)
```

注意 `VGroup.arrange()` 会移动整个组：**填字必须在 arrange 之前**，
否则组内绝对坐标会错位。要在 arrange 之后填，就按最终 `get_center()` 重算。

### 参数扫描 + 实时读数

```python
t = ValueTracker(1.0)
curve = always_redraw(lambda: ax.plot(
    lambda x: t.get_value() * np.sin(x), x_range=[-PI, 2 * PI],
    color=BLUE, stroke_width=4.5))

lbl = Text("A =", font=FONT, font_size=30, color=ORAN)
num = DecimalNumber(1.0, num_decimal_places=1, color=ORAN, font_size=34)
num.add_updater(lambda m: m.set_value(t.get_value()).next_to(lbl, RIGHT, buff=0.12))
readout = VGroup(lbl, num).arrange(RIGHT, buff=0.12).next_to(formula, DOWN,
                                                             aligned_edge=RIGHT, buff=0.2)

self.add(curve)
self.play(FadeIn(readout), run_time=0.5)
self.play(t.animate.set_value(2.0), run_time=1.8, rate_func=smooth)
```

### 随参数变化的标注（双箭头量周期 / 量振幅）

```python
# 注意：两端点不能重合，取值范围不要包含 0
per = always_redraw(lambda: DoubleArrow(
    ax.c2p(0, 1.4), ax.c2p(2 * PI / w.get_value(), 1.4),
    buff=0, color=TEAL, stroke_width=4, tip_length=0.18))
```

### 跟随某点的标记（最高点、动点）

```python
dot = always_redraw(lambda: Dot(ax.c2p(PI / 2 - p.get_value(), 1.0),
                                radius=0.09, color=TEAL))
```

### 换一条曲线（无缝切换）

```python
new = always_redraw(lambda: ax.plot(lambda x: np.sin(w.get_value() * x),
                                    x_range=[-PI, 2 * PI], color=BLUE, stroke_width=4.5))
self.remove(old)   # 同一时刻两条曲线数值相同 -> 视觉无跳变
self.add(new)
```

### 小结卡片收尾

```python
end = VGroup(
    Text("振幅 A", font=FONT, font_size=34, color=ORAN),
    Text("角频率 ω", font=FONT, font_size=34, color=TEAL),
    Text("初相 φ", font=FONT, font_size=34, color=RED),
).arrange(RIGHT, buff=0.9)
end2 = Text("决定图像的高低、疏密、位置", font=FONT, font_size=30, color=INK)
end2.next_to(end, DOWN, buff=0.5)
self.play(FadeIn(end, shift=UP * 0.2), FadeIn(end2, shift=UP * 0.2), run_time=1.0)
```

## 分幕与时长经验值

- 总时长 30～50 s 最稳；超过 50 s 基本必然要走降级脚本渲染。
- 单幕 5～8 s；`self.play(..., run_time=1.8~2.5)` 做参数扫描，`self.wait(0.5~1.2)` 做停顿。
- 一帧里同时存在的 `always_redraw` 对象控制在 2～3 个以内，多了渲染时间会明显变长。
- 幕数 4～6 幕，每幕一个结论，最后加小结卡。

---
