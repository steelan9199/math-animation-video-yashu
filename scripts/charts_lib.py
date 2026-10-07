"""manim 图表生成公共库（math-animation-video-yashu 技能配套）

用法：把本文件复制到你的场景文件同目录，然后
    from charts_lib import *

提供：配色常量、16:9 画布、标准坐标轴、柱状图辅助、中文刻度、标题区、
图例、卡片/菱形/胶囊/标注、箭头、安全区兜底。

⚠️ 配套文档：references/chart-generation.md
⚠️ 所有角度参数是**弧度**；所有 shift/move_to 位移是**三维**。
"""
from manim import *
import numpy as np

# ⚠️ manim 0.21 的 `from manim import *` **不导出** AnnularSector（环形扇形），
# 必须从子模块显式 import。类名是 **AnnularSector（双 r）**，不是 AnnulusSector。
from manim.mobject.geometry.arc import AnnularSector

# ---------------- 配色（浅色公众号风） ----------------
INK = "#21242C"
BLUE = "#1865F2"
TEAL = "#14BF96"
ORAN = "#FF914D"
RED = "#D92916"
PURPLE = "#7C4DFF"
PINK = "#F44393"
GOLD = "#F5A623"
AXC = "#98A2B3"
GRIDC = "#E4E7EE"
GRAY = "#6B7280"
BG = "#FFFFFF"
FONT = "Noto Sans SC"        # SIL OFL 1.1，可商用

PALETTE = [BLUE, TEAL, ORAN, PURPLE, RED, PINK, GOLD]

# 16:9 画布
config.frame_width = 14.222
config.frame_height = 8.0
config.background_color = BG


# ---------------- 通用零件 ----------------
def card(w, h, fill="#F7F9FD", stroke=GRIDC, radius=0.18, sw=1.4):
    r = RoundedRectangle(width=w, height=h, corner_radius=radius)
    r.set_fill(fill, opacity=1.0).set_stroke(stroke, width=sw)
    return r


def pill(txt, size, fg, bg, pad=0.42, hp=0.22):
    t = Text(txt, font=FONT, font_size=size, color=fg)
    h = t.height + hp
    r = RoundedRectangle(width=t.width + pad, height=h, corner_radius=h / 2)
    r.set_fill(bg, opacity=1.0).set_stroke(width=0)
    return VGroup(r, t.move_to(r.get_center()))


def title_bar(main, sub=None, tag=None):
    """左上角标题区：标签 + 主标题 + 副标题，纵向排列后整体贴左上角。

    ⚠️ 不要分别 to_corner(UL)，那样标签和标题会**重叠**（各自都贴左上角）。
    """
    gs = []
    if tag:
        gs.append(pill(tag, 20, BG, BLUE))
    gs.append(Text(main, font=FONT, font_size=40, color=INK))
    if sub:
        gs.append(Text(sub, font=FONT, font_size=21, color=GRAY))
    g = VGroup(*gs).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
    g.to_corner(UL, buff=0.34)
    return g


def legend(items, size=20, gap=0.42, marker="dot"):
    """items = [(文本, 颜色), ...] 横向图例，返回 VGroup。"""
    gs = []
    for txt, col in items:
        if marker == "dot":
            m = Dot(radius=0.075, color=col)
        elif marker == "square":
            m = Square(side_length=0.16, stroke_width=0).set_fill(col, opacity=1.0)
        else:
            m = Line(LEFT * 0.11, RIGHT * 0.11, stroke_width=4.5, color=col)
        lab = Text(txt, font=FONT, font_size=size, color=GRAY)
        gs.append(VGroup(m, lab).arrange(RIGHT, buff=0.13))
    return VGroup(*gs).arrange(RIGHT, buff=gap, aligned_edge=DOWN)


def std_axes(x_range, y_range, x_len=8.6, y_len=4.3,
             x_step=None, y_step=None, y_fmt=None, c2p_shift=(0, 0, 0)):
    """标准坐标轴：浅色网格 + 深色轴线 + 隐藏数字（刻度自行添加）。

    ⚠️ shift 的位移**必须三维**，传 (0, 0) 会报
    ValueError: operands could not be broadcast together with shapes (4,3) (2,)。
    """
    grid = NumberPlane(
        x_range=x_range, y_range=y_range,
        x_length=x_len, y_length=y_len,
        background_line_style={"stroke_color": GRIDC, "stroke_width": 1},
        axis_config={"stroke_opacity": 0},
    )
    ax = Axes(
        x_range=x_range, y_range=y_range,
        x_length=x_len, y_length=y_len,
        axis_config={"color": AXC, "stroke_width": 2.4,
                     "include_tip": True, "include_numbers": False},
    )
    grp = VGroup(grid, ax).shift(np.array(c2p_shift, dtype=float))
    return grp[0], grp[1]


def add_x_ticks(ax, values, labels=None, size=18, buff=0.20, color=GRAY):
    """在 x 轴上加中文/自定义刻度标签。"""
    labs = []
    for i, v in enumerate(values):
        s = labels[i] if labels else str(v)
        t = Text(s, font=FONT, font_size=size, color=color)
        t.next_to(ax.c2p(v, ax.y_range[0]), DOWN, buff=buff)
        labs.append(t)
    return VGroup(*labs)


def add_y_ticks(ax, values, labels=None, size=18, buff=0.20, color=GRAY):
    labs = []
    for i, v in enumerate(values):
        s = labels[i] if labels else str(v)
        t = Text(s, font=FONT, font_size=size, color=color)
        t.next_to(ax.c2p(ax.x_range[0], v), LEFT, buff=buff)
        labs.append(t)
    return VGroup(*labs)


def dashed_guide(ax, y, color=GRAY, w=1.8):
    """水平参考虚线（从 y 轴画到右端）。"""
    x0, x1 = ax.x_range[0], ax.x_range[1]
    return DashedLine(ax.c2p(x0, y), ax.c2p(x1, y),
                      stroke_width=w, color=color, dash_length=0.14)


def vline(ax, x, color=GRAY, w=1.8):
    y0, y1 = ax.y_range[0], ax.y_range[1]
    return DashedLine(ax.c2p(x, y0), ax.c2p(x, y1),
                      stroke_width=w, color=color, dash_length=0.14)


def note(txt, size=19, color=BLUE, bg="#EEF3FE"):
    """图上的一行小标注（带浅底）。"""
    t = Text(txt, font=FONT, font_size=size, color=color)
    r = RoundedRectangle(width=t.width + 0.34, height=t.height + 0.20,
                         corner_radius=0.10)
    r.set_fill(bg, opacity=1.0).set_stroke(width=0)
    return VGroup(r, t.move_to(r.get_center()))


def arrow(p0, p1, color=GRAY, w=2.2, tip=0.16):
    """两点箭头。端点支持二维/三维，函数内统一补成三维。"""
    a = np.array(p0, dtype=float)
    b = np.array(p1, dtype=float)
    if a.shape[0] == 2:
        a = np.append(a, 0.0)
    if b.shape[0] == 2:
        b = np.append(b, 0.0)
    return Arrow(a, b, color=color, stroke_width=w, tip_length=tip,
                 buff=0, max_stroke_width_to_length_ratio=99)


def box_text(txt, size=22, color=INK, fill="#F7F9FD", stroke=GRIDC,
             w=None, h=None, pad=(0.34, 0.22), radius=0.14, sw=1.6):
    """一块带文字的圆角卡片（流程图/思维导图的基本单元）。"""
    t = Text(txt, font=FONT, font_size=size, color=color)
    ww = w if w is not None else t.width + pad[0]
    hh = h if h is not None else t.height + pad[1]
    c = RoundedRectangle(width=ww, height=hh, corner_radius=radius)
    c.set_fill(fill, opacity=1.0).set_stroke(stroke, width=sw)
    return VGroup(c, t.move_to(c.get_center()))


def diamond(txt, size=20, color=INK, fill="#FFF7ED", stroke=ORAN, w=2.0, h=1.1):
    """判断菱形（流程图用）。"""
    t = Text(txt, font=FONT, font_size=size, color=color)
    d = Polygon([-w / 2, 0, 0], [0, h / 2, 0], [w / 2, 0, 0], [0, -h / 2, 0],
                stroke_width=1.8)
    d.set_fill(fill, opacity=1.0).set_stroke(stroke, width=1.8)
    t.scale(0.62)
    return VGroup(d, t.move_to(d.get_center()))


def label_edge(txt, size=17, color=GRAY):
    return Text(txt, font=FONT, font_size=size, color=color)


def at(x, y):
    """把二维坐标凑成 manim 要的三维点。

    ⚠️ `mob.move_to(a, b, c)` 会被解释成 (point, aligned_edge)，三个位置参数直接崩：
       `IndexError: invalid index to scalar variable`。
       所有绝对定位一律用 `at(x, y)`。
    """
    return np.array([x, y, 0.0])


def put(mob, x, y):
    """安全版绝对定位：mob.move_to(at(x, y))"""
    return mob.move_to(at(x, y))


def bars_on_axis(ax, values, labels, colors=None, x_offset=0.0, width=0.52,
                 lab_size=21, name_size=19, name_buff=0.18,
                 highlight=None, hi_color=ORAN):
    """在坐标轴上画一组柱子：底边钉轴、顶端按 c2p 求高、名称钉在轴下。

    柱状图最容易写错的地方：不要先建 Rectangle 再 move_to(x, 0)，
    那样底边跟着中心走，柱子会浮在轴上方/悬空。正确做法是
    「算出像素高度 → 中心点 y = 基线 + 高度/2」。
    """
    base = ax.c2p(0, 0)[1]
    gs = []
    for i, v in enumerate(values):
        y = ax.c2p(0, v)[1]
        if colors is None:
            c = BLUE
        elif isinstance(colors, (list, tuple)):
            c = colors[i]
        else:
            c = colors
        if highlight is not None and i == highlight:
            c = hi_color
        b = Rectangle(width=width, height=abs(y - base), stroke_width=0)
        b.set_fill(c, opacity=1.0)
        b.move_to(at(ax.c2p(i + x_offset, 0)[0], base + (y - base) / 2))
        gs.append(VGroup(b, Text(str(v), font=FONT, font_size=lab_size,
                                 color=INK).next_to(b, UP, buff=0.11)))
        nm = Text(labels[i], font=FONT, font_size=name_size, color=GRAY)
        nm.next_to(ax.c2p(i + x_offset, 0), DOWN, buff=name_buff)
        gs.append(nm)
    return VGroup(*gs)


def stacked_bars(ax, series, labels, colors, width=0.56, lab_size=17):
    """堆叠柱：series = [(名称, [各柱高度...]), ...]。"""
    base = ax.c2p(0, 0)[1]
    tops = np.zeros(len(labels))
    out = VGroup()
    for (nm, vals), c in zip(series, colors):
        g = VGroup()
        for i, v in enumerate(vals):
            y0 = ax.c2p(0, tops[i])[1]
            y1 = ax.c2p(0, tops[i] + v)[1]
            b = Rectangle(width=width, height=abs(y1 - y0), stroke_width=1.2)
            b.set_fill(c, opacity=1.0).set_stroke(BG, width=1.2)
            b.move_to(at(ax.c2p(i, 0)[0], (y0 + y1) / 2))
            g.add(b)
            tops[i] += v
        out.add(g)
    return out, tops


# ---------------- 安全区：所有图表的收尾必过 ----------------
# 标题区占左上角（约 x<3.2 且 y>2.0），内容必须避开。
SAFE = {"x_min": -6.95, "x_max": 6.95, "y_min": -3.72, "y_max": 3.90}


def safe_board(board, move_to=None, scale=True):
    """把内容组压进安全区并按需缩放，最后可选居中。

    **每张图表的 construct 末尾都必须过这一关**，它是防溢出/压标题的最后一道闸。
    做法：先算内容包围盒，超出安全区就整体 scale_to_fit_width/height，
    再把它 move_to 到 (0, 0.1) 之类的目标位置。
    """
    if scale:
        w = SAFE["x_max"] - SAFE["x_min"]
        h = SAFE["y_max"] - SAFE["y_min"]
        if board.width > w:
            board.scale_to_fit_width(w)
        if board.height > h:
            board.scale_to_fit_height(h)
    if move_to is not None:
        board.move_to(at(*move_to))
    return board