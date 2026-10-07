# 图表生成（manim 通用图表路线）

**触发**：用户要「画图表 / 做数据图 / 柱状图 / 折线图 / 饼图 / 流程图 / 思维导图 /
鱼骨图 / 甘特图 / 组织架构图 / 漏斗图 / 桑基图 / 热力图 / 雷达图」等**任何信息图**。

> **核心认知：manim 不只是做数学动画的。**
> 任何信息图拆开都是「坐标 + 图元 + 文字」。柱状图是 `Rectangle`，
> 折线图是 `VMobject.set_points_smoothly`，流程图是 `Rectangle + Arrow`，
> 思维导图是 `CurveArrow` 放射——**难度不在图形，在于版面对齐和避坑**。
> 本文档就是那份避坑手册。

---

## 一、标准流程（六步，不许跳）

| 步骤 | 动作 | 工具 | 耗时 |
|---|---|---|---|
| 1 | 跑 manim 版本守门 | `scripts/check_manim_version.py` | 秒 |
| 2 | 从本文件 + 模板抄一版场景代码 | `charts_lib.py`（见第六节） | 分钟 |
| 3 | **探针校验语法**（不渲染像素） | `scripts/probe_charts.py` | 秒 |
| 4 | 真渲染出图 | `manim render --format=png -s` | 3~6 s/张 |
| 5 | **版面自检**（压标题 / 溢出画布） | `scripts/check_chart_layout.py` | 4 s/张 |
| 6 | 亲眼看图 + 交付 | 读图工具 | 分钟 |

**核心纪律：第 3 步和第 5 步是本技能图表路线的核心，不可跳过。**

- 第 3 步解决「代码报错但看不到报错行」——`manim render` 的回溯是**截断的**，
  只显示 `ValueError: operands could not be broadcast together with shapes (4,3) (2,)`
  这类无信息量的尾巴，你根本不知道是哪一行。探针给的是 Python 原生完整 traceback。
- 第 5 步解决「代码不报错、渲染成功、但画面压标题/溢出」——这类问题**只有看图或
  像素检测才能发现**，人眼看 N 张图一定漏。

---

## 二、渲染命令

```bash
cd <工作目录>
"D:/software/uv/envs/py314-cpu/Scripts/python_direct.exe" -m manim render \
  --renderer=cairo --format=png -s --resolution 1920,1080 \
  --media_dir "./_media" <scene.py> <ClassName> <ClassName2> ... > _r.log 2>&1
```

- `--renderer=cairo`：纯 CPU、抗锯齿、无 GPU 依赖
- `--format=png -s`：静态图，只保存最后一帧（**不要** `--quality`、不要 mp4）
- **一次可以传多个类名**，批量出图比一个一个快得多
- **执行纪律**：`run_in_background=true`（渲染纪律第 1 条）
- 日志必查：`grep -icE "falling back|Traceback" _r.log` **必须为 0**
  （`falling back` = 字体静默回退，中文字形会错）

**画布**：图表默认 16:9。文件顶部锁：

```python
config.frame_width = 14.222
config.frame_height = 8.0
```

封面另用 2.35:1，见 `wechat-cover.md`。

---

## 三、⚠️ 本次实战踩过的坑（全部已修，全部复现过）

### 坑 1｜角度参数是**弧度**，不是角度

```python
AnnularSector(start_angle=0, angle=90)        # ❌ 90 弧度 = 25 圈，形状全乱
AnnularSector(start_angle=0, angle=np.radians(90))   # ✅
```

报错长这样：`ValueError: operands could not be broadcast together with shapes (4,3) (2,)`
——它把 `90` 当弧度算出超大坐标，和中心点一减就炸了。**这个报错信息完全看不出
「角度单位错了」，是这个坑最恶心的地方。**

已实测：`AnnularSector.__init__(inner_radius, outer_radius, angle=π/2, start_angle=0, ...)`，
`Arc`、`ArcBetweenPoints` 同样。

### 坑 2｜类名是 `AnnularSector`（**双 r**），且**顶层不导出**

```python
from manim import *
AnnularSector(...)          # ❌ NameError
```

0.21 的 `from manim import *` **不导出**它，必须显式：

```python
from manim.mobject.geometry.arc import AnnularSector
```

写错成 `AnnulusSector`（单 r）报 `ImportError: cannot import name ... Did you mean: 'AnnularSector'?`。

### 坑 3｜`move_to(a, b, c)` 三个位置参数会崩

```python
lab.move_to(x, y, 0)                # ❌ IndexError: invalid index to scalar variable
lab.move_to(np.array([x, y, 0]))    # ✅
```

签名是 `move_to(point_or_mobject, aligned_edge=ORIGIN, ...)`——
你传的 `y` 会被当成 `aligned_edge`，然后去取 `direction[dim]` 就炸了。
**所有二维定位一律用 `at(x, y)` 转三维。**

### 坑 4｜`shift()` 传二维向量会崩

```python
VGroup(g, ax).shift((0, 0))          # ❌ ValueError: broadcast (4,3) (2,)
VGroup(g, ax).shift(np.array([0, 0, 0]))   # ✅
```

和坑 1 的报错**一模一样**，极易误判。记住：**任何 `shift` 位移都是三维。**

### 坑 5｜`Axes.get_area` 的 `x_range` 只收 2 元组

```python
ax.get_area(curve, x_range=[0, 12, 0.15])     # ❌ too many values to unpack (expected 2, got 3)
ax.get_area(curve, x_range=(0, 12))           # ✅  只给上下界
```

堆叠面积图要用 `bounded_graph` 指定**下界那条曲线**，**没有 `y_range` 参数**：

```python
B = ax.get_area(ax.plot(f_top, x_range=[0,12,0.15]),
                x_range=(0, 12), color=TEAL, opacity=0.66,
                bounded_graph=ax.plot(f_bottom, x_range=[0,12,0.15]))
```

### 坑 6｜别拿 numpy 向量做比较

```python
if side == UP:      # ❌ ValueError: truth value of an array ... is ambiguous
```

`UP` / `DOWN` 是 numpy 数组。方向判断用 `+1 / -1` 数字标记，不要用 `UP`/`DOWN` 比较。

### 坑 7｜柱子的底边会「浮空」

```python
b = Rectangle(width=0.52, height=some_value)
b.move_to(ax.c2p(i + 0.5, 0), aligned_edge=DOWN)     # ❌ 底边跟着中心走，柱子悬空/入地
```

`move_to` 移动的是**包围盒中心**。正确做法是先算出像素高度，再定中心：

```python
base = ax.c2p(0, 0)[1]                # 基线像素 y
y = ax.c2p(0, value)[1]               # 顶端像素 y
h = abs(y - base)
b = Rectangle(width=w, height=h)
b.move_to(at(ax.c2p(i + 0.5, 0)[0], base + h / 2))   # 中心在基线 + 半高
```

**柱状图/瀑布图/甘特图条/柱状进度条全都要这么写。** 库里的 `bars_on_axis()` 就是干这个的。

### 坑 8｜子节点间距小于卡片宽度 ⇒ 重叠

组织架构图里三个卡片中心间距 1.2、卡宽 1.32 → 必然叠在一起。
**规则：卡片中心间距必须 > 卡片宽度 + 0.2。** 排布前先定卡宽，再按宽度算间距。

### 坑 9｜`title_bar` 里各元素分别贴左上角 ⇒ 标签压标题

```python
p.to_corner(UL, buff=0.34)      # ❌ 每个都贴左上角 → 标签和标题重叠
t.to_corner(UL, buff=0.34)      # ❌
```

正确：先 `arrange` 再整体贴：

```python
g = VGroup(*gs).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
g.to_corner(UL, buff=0.34)
```

### 坑 10｜绝对定位算出来的宽度会溢出画布

字号 × 字数算中文宽度极不可靠（本次实测同一条副标题从「刚好贴边」到「被裁掉半行」
只差一次字号调整）。**不要估，用 `safe_board()` 自动兜底。**

### 坑 11｜数据里的小数没向上取整 ⇒ 顶部出界

瀑布图算完最终值 166，y 轴只设到 120 ⇒ 柱子戳出图外。
**算完数据先取 max 再定 y_range，并留 10~20% 余量。**

### 坑 12｜热力图行标签压住色块

行标签 x 偏移量小于色块半宽就会叠上。偏移量 = 色块宽/2 + 标签宽/2 + 间隙。

### 坑 13｜SWOT/矩阵类四象限内容「都一样」

复用同一个 items 列表给四个格子 → 四格内容完全相同，图表毫无意义。
**四象限的每一格必须是独立内容。**

### 坑 14｜图例压住坐标轴刻度

图例 `move_to(at(0, -3.05))` 放在轴下方，正好盖住 x 轴数字。
**图例优先放右上/右下空白区，放轴下方前先确认那里没刻度。**

### 坑 15｜哈希缓存导致「拿到上一轮旧图」

场景文件没改动时 manim 直接跳过渲染，`media_dir` 里留着上次的 PNG。
**批量脚本每次必须先 `rm -rf media_dir`**，否则你会把旧图当成新图交付。

---

## 四、版面对齐：三层安全区机制（照抄）

这是本次最有价值的沉淀，**所有图表都用它**。

```python
# 1. 画布锁 16:9
config.frame_width = 14.222
config.frame_height = 8.0

# 2. 内容包成一个组，收尾统一过安全区
content = VGroup(所有内容元素)
safe_board(content, move_to=(-0.35, -0.25))

# 3. 标题单独添加，不进 content
self.add(title_bar("主标题", "副标题", "标签"), content)
```

`safe_board` 做的事：算出内容包围盒 → 超出安全区就整体缩放 → 移到目标位置。
**这是防溢出、防压标题的最后一道闸。**

安全区范围（16:9 画布）：

```python
SAFE = {"x_min": -6.95, "x_max": 6.95, "y_min": -3.72, "y_max": 3.90}
```

> ⚠️ **但 `safe_board` 只能防溢出，防不了"压标题"**——
> 因为它按整体包围盒缩放，内容里某个元素伸到左上角它不一定察觉。
> 所以第五步的**像素级版面自检**依然必需。

---

## 五、工具脚本（已实测，24/24 通过）

### 探针：拿到完整 traceback

```bash
& $PY "<技能目录>\scripts\probe_charts.py" <scene.py> [类名 ...]
# 不传类名 ⇒ 自动发现该文件里所有自己定义的 Scene 子类
```

- 在 `dry_run` 下直接跑 construct，**秒级**返回
- **自动发现会排除基类**（`ThreeDScene` 等）：判据是 `cls.__module__ == 本文件名`。
  踩过这个坑——不排除会把 `from manim import *` 带进来的基类一起跑，
  它们缺 `renderer` 属性直接 AttributeError，**纯误报**
- 退出码非 0 表示有场景没过

### 版面自检：像素级检测压标题 / 溢出

```bash
& $PY "<技能目录>\scripts\check_chart_layout.py" --manifest manifest.json --dir .
```

manifest 格式：

```json
[["charts_01_basic.py", [["ChartBar", "01_柱状图"], ["ChartLine", "02_折线图"]]]]
```

判据：裁出左上角标题区，统计非白像素占比。
**实测正常值 6~19%**；超过 26% 说明有东西压上来了，超过 40% 严重压。
（可先用 `--only ChartBar` 单张调试）

---

## 六、公共库 `scripts/charts_lib.py`（直接复制去用）

**位置**：`<技能目录>/scripts/charts_lib.py`。把它复制到场景文件同目录，然后
`from charts_lib import *`，配色/画布/坐标轴/卡片/安全区全都现成。

提供：配色常量、`std_axes`、`bars_on_axis`、`add_x_ticks`/`add_y_ticks`、
`title_bar`、`legend`、`box_text`、`diamond`、`card`、`pill`、`note`、
`arrow`、`at`/`put`、`safe_board`。

核心零件（本次全部实测过）：

```python
config.frame_width, config.frame_height = 14.222, 8.0
INK, BLUE, TEAL, ORAN, RED, PURPLE = "#21242C", "#1865F2", "#14BF96", "#FF914D", "#D92916", "#7C4DFF"
GRAY, GRIDC, AXC, BG = "#6B7280", "#E4E7EE", "#98A2B3", "#FFFFFF"
FONT = "Noto Sans SC"     # SIL OFL 1.1，可商用。禁用微软雅黑
PALETTE = [BLUE, TEAL, ORAN, PURPLE, RED, PINK, GOLD]


def at(x, y):
    return np.array([x, y, 0.0])       # 坑 3/4 的解药


def card(w, h, fill="#F7F9FD", stroke=GRIDC, radius=0.18, sw=1.4):
    r = RoundedRectangle(width=w, height=h, corner_radius=radius)
    r.set_fill(fill, opacity=1.0).set_stroke(stroke, width=sw)
    return r


def box_text(txt, size=22, color=INK, fill="#F7F9FD", stroke=GRIDC,
             w=None, h=None, pad=(0.34, 0.22), radius=0.14):
    t = Text(txt, font=FONT, font_size=size, color=color)
    c = RoundedRectangle(
        width=w if w else t.width + pad[0],
        height=h if h else t.height + pad[1],
        corner_radius=radius)
    c.set_fill(fill, opacity=1.0).set_stroke(stroke, width=1.6)
    return VGroup(c, t.move_to(c.get_center()))   # 坑：文字必须按卡片中心算，不能 move_to([0,dy,0])


def diamond(txt, size=20, color=INK, fill="#FFF7ED", stroke=ORAN, w=2.0, h=1.1):
    t = Text(txt, font=FONT, font_size=size, color=color)
    d = Polygon([-w/2,0,0], [0,h/2,0], [w/2,0,0], [0,-h/2,0])
    d.set_fill(fill, opacity=1.0).set_stroke(stroke, width=1.8)
    t.scale(0.62)                     # 文字缩小才放得进菱形
    return VGroup(d, t.move_to(d.get_center()))


def std_axes(x_range, y_range, x_len=8.6, y_len=4.3, c2p_shift=(0, 0, 0)):
    """标准坐标轴：浅网格 + 深轴线 + 隐藏数字（刻度自行加）。shift 必须三维。"""
    grid = NumberPlane(x_range=x_range, y_range=y_range,
                       x_length=x_len, y_length=y_len,
                       background_line_style={"stroke_color": GRIDC, "stroke_width": 1},
                       axis_config={"stroke_opacity": 0})
    ax = Axes(x_range=x_range, y_range=y_range,
              x_length=x_len, y_length=y_len,
              axis_config={"color": AXC, "stroke_width": 2.4,
                           "include_tip": True, "include_numbers": False})
    g = VGroup(grid, ax).shift(np.array(c2p_shift, dtype=float))
    return g[0], g[1]


def bars_on_axis(ax, values, labels, colors=None, x_offset=0.0, width=0.52,
                 highlight=None, hi_color=ORAN):
    """柱状图专用：底边钉轴、顶端按 c2p 求高（坑 7 的解药）。"""
    base = ax.c2p(0, 0)[1]
    gs = []
    for i, v in enumerate(values):
        y = ax.c2p(0, v)[1]
        c = (colors[i] if isinstance(colors, (list, tuple)) else colors) if colors else BLUE
        if highlight is not None and i == highlight:
            c = hi_color
        b = Rectangle(width=width, height=abs(y - base), stroke_width=0)
        b.set_fill(c, opacity=1.0)
        b.move_to(at(ax.c2p(i + x_offset, 0)[0], base + (y - base) / 2))
        gs.append(VGroup(b, Text(str(v), font=FONT, font_size=21,
                                 color=INK).next_to(b, UP, buff=0.11)))
        nm = Text(labels[i], font=FONT, font_size=19, color=GRAY)
        nm.next_to(ax.c2p(i + x_offset, 0), DOWN, buff=0.18)
        gs.append(nm)
    return VGroup(*gs)


def title_bar(main, sub=None, tag=None):
    """标签 + 主标题 + 副标题。先 arrange 再整体贴左上角（坑 9 的解药）。"""
    gs = []
    if tag:
        gs.append(pill(tag, 20, BG, BLUE))
    gs.append(Text(main, font=FONT, font_size=40, color=INK))
    if sub:
        gs.append(Text(sub, font=FONT, font_size=21, color=GRAY))
    g = VGroup(*gs).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
    g.to_corner(UL, buff=0.34)
    return g


SAFE = {"x_min": -6.95, "x_max": 6.95, "y_min": -3.72, "y_max": 3.90}


def safe_board(board, move_to=None, scale=True):
    """所有图表收尾必过：超界自动缩放 + 定位（坑 10 的解药）。"""
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
```

---

## 七、各类图表的关键实现要点

| 图表 | 核心做法 | 必踩坑 |
|---|---|---|
| **柱状图** | `bars_on_axis()` | 坑 7（底边浮空） |
| **折线图** | `VMobject(stroke_width=w).set_points_smoothly(np.array([c2p(t,y) for ...]))` | `x_range` 必须带步长 |
| **环形/饼图** | `AnnularSector(inner_radius=..., outer_radius=..., start_angle=radians(a0), angle=radians(a1-a0))`，逐段累加角度 | **坑 1 弧度**、**坑 2 类名双 r 且不导出** |
| **散点/气泡** | `Dot(c2p(x,y), radius=映射第三变量)` + `VMobject` 趋势线 | 半径映射要注意视觉放大 |
| **热力图** | `Rectangle` 网格 + `interpolate_color(ManimColor(c1), ManimColor(c2), t)`；数值色深自适应黑白字 | 坑 12（行标签压块） |
| **雷达图** | `Polygon(*[pt(i, v) for i,v in enumerate(vals)])` + `set_fill(c, opacity).set_stroke` | 多边形顶点顺序要跟角度一致 |
| **瀑布图** | 逐项累加 `lo/hi`，中心点 = `(yA+yB)/2`；虚线连下一柱 | **坑 11（y_range 没留余量）** |
| **面积图** | `ax.get_area(curve, x_range=(0,12), bounded_graph=下界曲线)` | **坑 5（只能 2 元组）** |
| **直方图** | `np.histogram` 分箱 + `Rectangle` + 密度曲线叠加 | 箱宽换算 `c2p(0.4,0)-c2p(0,0)` |
| **箱线图** | `Rectangle`(Q1–Q3) + `Line`(须) + 红线(中位) + `Dot`(离群) | 须线端点写法 |
| **仪表盘** | `AnnularSector` 半环分段 + `Line` 指针（长度 < 内半径） | 指针长度超内环会穿出去 |
| **流程图** | `box_text` + `diamond` + `arrow()`，分支标"是/否" | 箭头端点必须三维 |
| **思维导图** | `dirv = [cos a, sin a, 0]`，节点 = 中心 + dirv×半径，`CurvedArrow` 连线 | 叶子卡片要放在节点**外侧**并留足距离 |
| **鱼骨图** | 主骨 `Line` + 上下交替斜骨 + 分类色块 + 子原因 | 主骨 y 要**下移**避开标题区 |
| **漏斗图** | `Polygon` 逐层收敛，`arrange` 不适用，全用绝对坐标 | 层间转化率标在层右侧 |
| **桑基图** | 每节点维护「已用高度游标」，色带 = 上曲线 + 下曲线反向 `set_points_as_corners` | **各节点出入总和必须都为 1.0**，否则填不满/溢出 |
| **组织架构** | 父→子：竖下来 → 横向汇流线 → 竖下去 | **坑 8（间距 < 卡宽）** |
| **甘特图** | 条 = `RoundedRectangle(width=dur*u)`，任务名**单独成列**右对齐在轴左 | 任务名跟条形起点排会被压 / 出界 |
| **时间轴** | 主轴 `Line` + 节点 `Dot` + 上下交替（`±1` 数字标记） | **坑 6（别拿 UP/DOWN 比较）** |
| **韦恩图** | `Circle(radius)` × `set_fill(c, opacity=.3)`，交叠区标数值 | 标签位置按象限手算 |
| **网络关系图** | 节点极坐标环形排布 + 概率连边 | 边太多会糊，调 `p` 阈值 |
| **四象限/SWOT** | 底色块 + 十字轴 + 每象限**独立内容** | **坑 13（四格内容雷同）** |

---

## 八、交付

1. 图片放到用户指定目录，起中文名（`01_柱状图.png` 这种序号前缀便于排序）
2. `present_files`：图片按浏览优先级排，源码放后面
3. 回复里说清：**纯 manim 代码绘制、零 AI 生图**、字体授权（SIL OFL 1.1 可商用）、
   实际画了哪几类图

---

## 九、实战记录（2026-10-07）

一次做完 **24 类图表**（12 统计 + 10 结构关系 + 2 项目管理），1920×1080 全 16:9。

- 探针拦截 **6 个真 bug**（弧度制、类名双 r、move_to 多参数、shift 二维、
  get_area 三元组、numpy 比较），全部秒级定位到行
- 版面自检拦截 **5 处压标题/溢出**，靠人眼很难稳定发现
- 单张渲染 3~6 s，**24 张全渲 35 秒**
- 最终 24/24 探针通过、24/24 版面通过

参考成品：`D:\software\workBuddyWorkspace\manim_charts\`
（含 `charts_lib.py` 完整公共库 + 4 个场景文件 + `README.md`）。
需要新类型时，照第七节的要点表加一个场景类即可。