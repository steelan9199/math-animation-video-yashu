# 公众号封面版式模板（可复制代码）

> 两套已交付验证的版式：**左文右图**（有公式/图表时用）与
> **单卡居中**（纯文字/金句卡/要点卡时用）。
> 尺寸、渲染命令、防裁切、坑与自检清单在主篇
> `references/wechat-cover.md`，**先读主篇再来挑版式**。

## 六、封面版式模板（左文右图，最稳）

已交付并验证的版式：左侧标题区 + 右侧 2~3 张图卡。

```python
from manim import *

INK = "#21242C"; BLUE = "#1865F2"; TEAL = "#14BF96"; ORAN = "#FF914D"
AXC = "#98A2B3"; GRIDC = "#E4E7EE"; GRAY = "#6B7280"; BG = "#FFFFFF"
FONT = "Noto Sans SC"          # 封面固定用黑体系；白名单里的楷体小尺寸发虚，封面别用（见§二）

config.frame_width = 14.222
config.frame_height = 14.222 * 766 / 1800


def card(w, h, fill="#F7F9FD", stroke=GRIDC, radius=0.2):
    r = RoundedRectangle(width=w, height=h, corner_radius=radius)
    r.set_fill(fill, opacity=1.0).set_stroke(stroke, width=1.6)
    return r


def in_card(cx, cy, items):
    """把 (mobject, dx, dy) 平移到卡片中心 (cx, cy) 的相对位置。
    封面里卡片位置是显式坐标，比视频模板的 fill_card(arrange) 更好控。
    ⚠️ 这是**相对平移**（保留 mobject 自身的卡内局部坐标），所以每个 item
    必须先在原点附近按卡内相对坐标建好形状；别在这里传已全局定位过的对象。"""
    return [m.shift([cx + dx, cy + dy, 0]) for m, dx, dy in items]


def pill(txt, size, fg, bg):
    t = Text(txt, font=FONT, font_size=size, color=fg)
    h = t.height + 0.28
    r = RoundedRectangle(width=t.width + 0.58, height=h, corner_radius=h / 2)
    r.set_fill(bg, opacity=1.0).set_stroke(width=0)
    return VGroup(r, t.move_to(r.get_center()))


def fit_board(board, margin=0.55):
    """把整个版面压进安全区。margin 是四边留白（单位，1 单位 ≈ 126.5 px @1800 宽）。"""
    fw, fh = config.frame_width, config.frame_height
    if board.width + 2 * margin > fw:
        board.scale_to_fit_width(fw - 2 * margin)
    if board.height + 2 * margin > fh:
        board.scale_to_fit_height(fh - 2 * margin)
    return board


class MyCover(Scene):            # 类名必须 ASCII
    def construct(self):
        self.camera.background_color = BG

        # ---- 左区：标签 / 主标题 / 副标 / 分隔线 / 卖点 ----
        LX = -3.95
        tag = pill("MCP 实战", 26, BG, BLUE).move_to([LX + 0.10, 2.32, 0])

        t1 = Text("吊打各种", font=FONT, font_size=62, color=INK)
        t2 = Text("图表", font=FONT, font_size=62, color=BLUE)   # 关键词上色
        title = VGroup(t1, t2).arrange(RIGHT, buff=0.12)
        title.move_to([LX + 0.42, 1.32, 0])

        sub = Text("一个 MCP，图表 / 公式 / 动画全包",
                   font=FONT, font_size=26, color=GRAY)
        sub.move_to([LX + 0.42, 0.36, 0])

        rule = Line([-6.95, -0.24, 0], [-0.95, -0.24, 0],
                    stroke_width=2.6, color=GRIDC)

        foot = VGroup(
            Text("专家版 · 科普版 · 公众号封面", font=FONT, font_size=24, color=INK),
            Text("全部由 manim 生成", font=FONT, font_size=24, color=ORAN),
        ).arrange(DOWN, buff=0.20, aligned_edge=LEFT)
        foot.move_to([LX + 0.42, -0.78, 0])

        left = VGroup(tag, title, sub, rule, foot)

        # ---- 右区：图卡 ----
        right_tag = Text("什么都能画", font=FONT, font_size=25, color=AXC)
        right_tag.move_to([3.50, 2.32, 0])

        CW, CH, CY = 1.98, 3.30, -0.10
        xs = [1.32, 3.50, 5.68]           # 三卡中心，右边界 5.68+0.99=6.67 < 7.11 ✔

        # 卡 1：折线图（坐标轴端点必须三维 [x, y, 0]）
        c1 = card(CW, CH).move_to([xs[0], CY, 0])
        xs_axis = Line([-0.72, -0.48, 0], [0.76, -0.48, 0],
                       stroke_width=2.4, color=AXC)
        ys_axis = Line([-0.72, -0.48, 0], [-0.72, 0.92, 0],
                       stroke_width=2.4, color=AXC)
        t = np.linspace(0, 1, 90)
        pts = np.stack([-0.66 + 1.30 * t,
                        -0.48 + 1.30 * np.abs(np.sin(t * 3.3)),
                        np.zeros_like(t)], axis=1)
        curve = VMobject(stroke_width=4.2, color=BLUE)
        curve.set_points_smoothly(pts)
        tip = Dot(pts[-1], radius=0.055, color=ORAN)
        c1.add(*in_card(xs[0], CY, [(xs_axis, 0, 0), (ys_axis, 0, 0),
                                    (curve, 0, 0), (tip, 0, 0)]))
        c1.add(Text("函数曲线", font=FONT, font_size=23, color=GRAY)
               .move_to([xs[0], CY - 1.22, 0]))

        # 卡 2：柱状图
        c2 = card(CW, CH).move_to([xs[1], CY, 0])
        heights, cols = [0.66, 1.10, 0.84], [BLUE, TEAL, ORAN]
        bars = VGroup()
        for i, (h, col) in enumerate(zip(heights, cols)):
            xc = -0.56 + i * 0.56
            b = Rectangle(width=0.32, height=h, stroke_width=0)
            b.set_fill(col, opacity=1.0).move_to([xc, -0.48 + h / 2, 0])
            bars.add(b)
        c2.add(*in_card(xs[1], CY, [
            (Line([-0.78, -0.48, 0], [0.78, -0.48, 0],
                  stroke_width=2.4, color=AXC), 0, 0),
            (bars, 0, 0),
            (DashedLine([-0.78, 0.44, 0], [0.78, 0.44, 0], stroke_width=1.8,
                        color=ORAN, dash_length=0.10), 0, 0)]))
        c2.add(Text("数据图表", font=FONT, font_size=23, color=GRAY)
               .move_to([xs[1], CY - 1.22, 0]))

        # 卡 3：公式（MathTex 需 LaTeX；白底必须 set_color，否则纯白看不见）
        c3 = card(CW, CH).move_to([xs[2], CY, 0])
        fml = MathTex(r"e^{i\pi}+1=0", font_size=24)
        fml.set_color(INK).move_to([xs[2], CY + 0.55, 0])
        fml2 = MathTex(r"\nabla \cdot \vec{E} = \rho", font_size=20)
        fml2.set_color(GRAY).move_to([xs[2], CY - 0.10, 0])
        c3.add(fml, fml2)
        c3.add(Text("论文公式", font=FONT, font_size=23, color=GRAY)
               .move_to([xs[2], CY - 1.22, 0]))

        right = VGroup(right_tag, c1, c2, c3)

        # ---- 组装 ----
        board = VGroup(left, right)
        print(f"[cover] board {board.width:.2f}x{board.height:.2f} / "
              f"frame {config.frame_width:.2f}x{config.frame_height:.2f}")
        fit_board(board)
        board.shift(DOWN * 0.30)
        self.add(board)
```

**可复用图元**：曲线 `ax.plot` / `VMobject.set_points_smoothly`、面积填充  
（`set_points_as_corners` 拼上底边两点，`fill_opacity=0.12`）、柱状 `Rectangle` 组、
`DashedLine` 均值参考线、`MathTex` 公式、`Dot` 端点高亮。图卡标签统一放在卡片底部
`CY - 1.22` 左右，字号 23、灰色 `GRAY`。

### 6.2 纯文字 / 金句卡 / 要点卡（单卡居中版式）

没有公式图表时不要硬塞图卡，改用**单卡居中**：大字主标 + 副标 + 细分割线 + 底部落款。
**关键：用 `next_to` 按实际边界排版，不要手填 `move_to` 坐标**——手填坐标换文案必重叠。

```python
from manim import *

INK = "#21242C"; BLUE = "#1865F2"; AXC = "#98A2B3"; GRIDC = "#E4E7EE"
GRAY = "#6B7280"; BG = "#FFFFFF"
FONT = "Noto Sans SC"          # 封面固定用黑体系；白名单里的楷体小尺寸发虚，封面别用（见§二）

config.frame_width = 14.222
config.frame_height = 14.222 * 766 / 1800     # = 6.052，严格锁 2.35:1


class QuoteCover(Scene):            # 类名必须 ASCII
    def construct(self):
        self.camera.background_color = BG

        # 主标：两行，第二行用主色上色
        t1 = Text("把复杂讲简单", font=FONT, font_size=76, color=INK)
        t2 = Text("把简单讲有趣", font=FONT, font_size=76, color=BLUE)
        title = VGroup(t1, t2).arrange(DOWN, buff=0.30, center=True)

        # 副标 / 分割线 / 落款：全部 next_to 串起来，换文案也不会重叠
        sub = Text("一个 MCP 讲完公式、图表与动画",
                   font=FONT, font_size=28, color=GRAY)
        sub.next_to(title, DOWN, buff=0.52)

        line = Line([-2.60, 0, 0], [2.60, 0, 0], stroke_width=2.2, color=GRIDC)
        foot = Text("公众号 · 每周更新", font=FONT, font_size=23, color=AXC)
        foot.next_to(sub, DOWN, buff=0.62)
        line.next_to(foot, UP, buff=0.26)

        board = VGroup(title, sub, line, foot)
        # 兜底缩放 + 垂直居中：内容少时必须居中，否则整体压在下边缘被裁
        fit_board(board)
        board.move_to([0, 0, 0])
        self.add(board)
```

实测数据：`font_size=76` 两行主标 + 28 副标 + 23 落款，在 1800×766 画布下
不需要缩放（`fit_board` 未触发）。

字号换算参考（画布高仅 6.05 单位，**纵向余量比横向紧张得多**）：
主标 62~88、副标 24~30、落款 22~24。**超过 88 会顶到上下边缘**。

