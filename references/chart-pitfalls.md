# 图表路线实战坑（全部已修、全部复现过）

> 图表路线专属的坑，按需查。**通用坑（配色/字体/动画机制/三维/构造类硬性写法）
> 在 `references/pitfalls.md`**，本文不重复。
> 排查流程、探针脚本、耗时判性质也见那篇。

## 一、图表路线实战坑（坑 1~15，全部已复现并修好）

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

### 坑 2｜类名是 `AnnularSector`（**双 r**）

```python
from manim import *
AnnularSector(...)# ✅ 0.21.0 顶层导出，from manim import * 直接可用
```

写错成 `AnnulusSector`（单 r）报
`ImportError: cannot import name ... Did you mean: 'AnnularSector'?`。
（实测 0.21.0：`manim.AnnularSector` 与 `manim.mobject.geometry.arc.AnnularSector`
是同一个类对象，显式从子模块 import 也可行但没必要。）

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

场景文件没改动时 manim 直接跳过渲染（用时 1~2 s 就是命中了，真实渲一张端到端约 3 s），
`media_dir` 里留着上次的 PNG。**每轮换一个全新的 `--media_dir` 目录名**
（`./_media_r1`、`./_media_r2`…），并按 mtime ≥ 本次启动时间过滤产物。

> **不要 `rm -rf` 整个 `media_dir`**：批量删除钩子会给非零退出码，还可能连带删掉同批次的其它产物。
> **换目录名是零风险做法**——旧目录留着不影响交付，交付前清理即可。
> 封面路线的同源问题与处置见 `wechat-cover.md` §三 渲染命令 的「哈希缓存导致假成功」。

---

