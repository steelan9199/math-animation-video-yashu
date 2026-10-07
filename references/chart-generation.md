# 图表生成（manim 通用图表路线）

**触发**：用户要「画图表 / 做数据图 / 柱状图 / 折线图 / 饼图 / 流程图 / 思维导图 /
鱼骨图 / 甘特图 / 组织架构图 / 漏斗图 / 桑基图 / 热力图 / 雷达图」等**任何信息图**。
**已支持哪些图表类型见 §六 各类图表的关键实现要点**——先查表，表里没有的按该表的写法新增一个场景类即可。
**踩过的坑见 `references/chart-pitfalls.md`**（通用坑在 `references/pitfalls.md`）。

> **核心认知：manim 不只是做数学动画的。**
> 任何信息图拆开都是「坐标 + 图元 + 文字」。柱状图是 `Rectangle`，
> 折线图是 `VMobject.set_points_smoothly`，流程图是 `Rectangle + Arrow`，
> 思维导图是 `CurveArrow` 放射——**难度不在图形，在于版面对齐和避坑**。

## 一、标准流程（六步，不许跳）

| 步骤 | 动作 | 工具 | 耗时 |
|---|---|---|---|
| 1 | 跑 manim 版本守门 | `scripts/check_manim_version.py` | 秒 |
| 2 | 抄一版场景代码 | `charts_lib.py`（见 §五 公共库） | 分钟 |
| 3 | **探针校验语法**（不渲染像素） | `scripts/probe_charts.py` | 秒 |
| 4 | 真渲染出图 | `manim render --format=png -s` | 首张 ~3 s，后续每张 ~1.5 s |
| 5 | **版面自检**（压标题 / 溢出画布） | `scripts/check_chart_layout.py` | 4 s/张 |
| 6 | 亲眼看图 + 交付 | 读图工具 | 分钟 |

**核心纪律：第 3 步和第 5 步不可跳过。** 第 3 步解决「代码报错但看不到报错行」
（`manim render` 的回溯是截断的，只给无信息量的尾巴，探针给的是完整 traceback）；
第 5 步解决「代码不报错、渲染成功、但画面压标题/溢出」——**这类问题只有看图或
像素检测才能发现**。

---

## 二、渲染命令

```powershell
cd<工作目录>
& "D:\software\uv\envs\py314-cpu\Scripts\python_direct.exe" -m manim render `
  --renderer=cairo --format=png -s --resolution 1920,1080 `
  --media_dir "./_media" <scene.py> <ClassName> <ClassName2> ... > _r.log 2>&1
```

- `--renderer=cairo`：纯 CPU、抗锯齿、无 GPU 依赖
- `--format=png -s`：静态图，只保存最后一帧（**不要** `--quality`、不要 mp4）
- **一次可以传多个类名**，批量出图比一个一个快得多
- **执行纪律**：`run_in_background=true` + `dangerouslyDisableSandbox=true`（`SKILL.md` 硬约束 3）
- 日志必查（无输出 = 干净）：`Select-String -Path _r.log -Pattern 'falling back','Traceback' -SimpleMatch`
  —— `falling back` = 字体静默回退，中文字形会错，**必须为 0**

**画布**：图表默认 16:9。文件顶部锁：

```python
config.frame_width = 14.222
config.frame_height = 8.0
```

封面另用 2.35:1，见 `wechat-cover.md`。

---
## 三、版面对齐：三层安全区机制（照抄）

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

## 四、工具脚本（已实测可用）

### 探针：拿到完整 traceback

```powershell
& $PY "<技能目录>\scripts\probe_charts.py" <scene.py> [类名 ...]
# 不传类名 ⇒ 自动发现该文件里所有自己定义的 Scene 子类
```

- 在 `dry_run` 下直接跑 construct，**秒级**返回
- **自动发现会排除基类**（`ThreeDScene` 等）：判据是 `cls.__module__ == 本文件名`。
  踩过这个坑——不排除会把 `from manim import *` 带进来的基类一起跑，
  它们缺 `renderer` 属性直接 AttributeError，**纯误报**
- 退出码非 0 表示有场景没过

### 版面自检：像素级检测压标题 / 溢出

```powershell
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

## 五、公共库 `scripts/charts_lib.py`（直接复制去用）

**位置**：`<技能目录>/scripts/charts_lib.py`。把它复制到场景文件同目录，然后
`from charts_lib import *`，配色/画布/坐标轴/卡片/安全区全都现成。

| 分组 | 成员 |
|---|---|
| 画布与配色 | `config.frame_width/height`（16:9）、`INK`/`BLUE`/`TEAL`/`ORAN`/`RED`/`PURPLE`/`GRAY`/`AXC`/`GRIDC`/`BG`、`FONT`、`PALETTE` |
| 定位 | `at(x, y)`（二维坐标转三维，坑3/4 的解药）、`put` |
| 坐标轴 | `std_axes(x_range, y_range, x_len, y_len, x_step, y_step, y_fmt, c2p_shift)`（返回 `(grid, ax)`，刻度数字默认隐藏）、`add_x_ticks` / `add_y_ticks`、`dashed_guide(ax, y)`、`vline(ax, x)` |
| 数据图元 | `bars_on_axis(ax, values, labels, colors, x_offset, width, highlight, hi_color)`（柱底钉轴，坑7 的解药） |
| 文字与容器 | `box_text`（文字+卡片一体，文字按卡片中心算）、`card`、`diamond`、`pill`、`note`、`legend(items, marker="dot"/"square"/"line")` |
| 结构 | `arrow(p0, p1)`（端点二维三维都吃，函数内补齐）、`title_bar(main, sub, tag)`（先 arrange 再贴左上角，坑9 的解药） |
| 收尾 | `SAFE`（安全区常量）、`safe_board(board, move_to, scale)`（超界自动缩放 + 定位，坑10 的解药） |

库本体是唯一权威版本，本文档不复刻它的源码——要看实现直接打开脚本。

常用片段：

```python
config.frame_width, config.frame_height = 14.222, 8.0
grid, ax = std_axes([0, 12, 1], [0, 100, 20])
bars = bars_on_axis(ax, [32, 58, 41], ["一月", "二月", "三月"])
content = VGroup(bars)
safe_board(content, move_to=(-0.35, -0.25))
self.add(title_bar("主标题", "副标题", "标签"), content)
```

---

## 六、各类图表的关键实现要点

> 表里的「坑 N」编号指向 `references/chart-pitfalls.md` 的对应条目。

| 图表 | 核心做法 | 必踩坑 |
|---|---|---|
| **柱状图** | `bars_on_axis()` | 坑 7（底边浮空） |
| **折线图** | `VMobject(stroke_width=w).set_points_smoothly(np.array([c2p(t,y) for ...]))` | `x_range` 必须带步长 |
| **环形/饼图** | `AnnularSector(inner_radius=..., outer_radius=..., start_angle=radians(a0), angle=radians(a1-a0))`，逐段累加角度 | **坑 1 弧度**、**坑 2 类名双 r** |
| **散点/气泡** | `Dot(c2p(x,y), radius=映射第三变量)` + `VMobject` 趋势线 | 半径映射要注意视觉放大 |
| **热力图** | `Rectangle` 网格 + `interpolate_color(ManimColor(c1), ManimColor(c2), t)`；数值色深自适应黑白字 | 坑 12（行标签压块） |
| **雷达图** | `Polygon(*[pt(i, v) for i,v in enumerate(vals)])` + `set_fill(c, opacity).set_stroke` | 多边形顶点顺序要跟角度一致 |
| **瀑布图** | 逐项累加 `lo/hi`，中心点 = `(yA+yB)/2`；虚线连下一柱 | **坑 11（y_range 没留余量）** |
| **面积图** | `ax.get_area(curve, x_range=(0,12), bounded_graph=下界曲线)` | **坑 5（只能 2 元组）** |
| **直方图** | `np.histogram` 分箱 + `Rectangle` + 密度曲线叠加 | 箱宽换算 `c2p(0.4,0)-c2p(0,0)` |
| **箱线图** | `Rectangle`(Q1–Q3) + `Line`(须) + 红线(中位) + `Dot`(离群) | 须线端点写法 |
| **帕累托图** | `bars_on_axis` 画降序柱 + 累计百分比折线（右轴 0~100%） | 柱子要按值降序排；两个 y 轴刻度单位不同，别共用 `add_y_ticks` |
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

## 七、交付

图片放到用户指定目录并起中文名（`01_柱状图.png` 这种序号前缀便于排序）；
`present_files` 图片在前、源码在后。回复里说清：**纯manim 代码绘制、零 AI 生图**、
字体授权（SIL OFL 1.1 可商用）、实际画了哪几类图。

---

## 八、性能基线

**成品目录 `D:\software\workBuddyWorkspace\manim_charts\`（含 `charts_lib.py` + 场景文件 + README）已随工作区清理，不再保留**——
需要参考成品时按 §五 公共库 复制 `charts_lib.py` 重写场景即可，不必找回旧目录。

耗时基线（用于按 §一 标准流程 步骤 4 估时）：**解释器启动 + `import manim` 约 1.2 s（每条命令都付）**，
单张渲染净耗时约 1.8 s（实测 1920×1080 柱状图端到端 2.97 s），
所以一次命令渲一张 ≈ 3 s、一次命令渲一批 ≈ 1.5 s/张；探针秒级；版面自检 4 s/张。