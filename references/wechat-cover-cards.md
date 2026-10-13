# 公众号封面右卡变体（清单 / 横评 / 编号列表）

> 右卡不是图卡时看本篇：工具横评、Top N、清单类文章用这三套。
> 尺寸、渲染命令、防裁切、通用坑在主篇 `wechat-cover.md`；左文右图骨架与单卡居中在
> `wechat-cover-layouts.md`。**先读那两篇再挑变体。**

## 通用前提：卡内左右安全线

三套变体都靠两条固定线定位，**不按文字宽度推**（长度不可控，推了会随文案抖动）：

```python
IL, IR = CX - CW / 2 + 0.36, CX + CW / 2 - 0.36      # 卡内左右安全线
MCX = (IL + IR) / 2                                   # 卡内水平中点，标题/caption 用它居中
```

卡高 `CH` 一般 4.2~4.7；行数越多 `CH` 越大、字号越小，先定行数再定 `CH`。

---

## 变体一：清单 / 横评卡（仿浏览器窗口）

工具横评、Top N 类文章用得上：右卡做成仿浏览器窗口（交通灯 + 地址栏 + 分隔线），卡内若干行清单。

⚠️ **圆角窗体不能靠「在圆角矩形上叠一个方形标题栏」来做**——方形矩形的角会戳出圆角外沿，
`CW` 一大（≥6）就肉眼可见。正确三层叠法（实测无穿帮）：

```python
shell = RoundedRectangle(width=CW, height=CH, corner_radius=0.20)  # 浅底，带圆角
body  = Rectangle(width=CW, height=CH - bar_h, stroke_width=0)      # 白底方块，盖掉下半
outline = RoundedRectangle(width=CW, height=CH, corner_radius=0.20) # 透明填充，只描边压顶
win = VGroup(shell, body, outline)      # 之后所有卡内元素 win.add(...) 即可
```

实测参数（卡 6.45×4.26，5 行）：

- 行高 `dy=0.56`，行底 `RoundedRectangle(w=CW-0.60, h=0.46, r=0.09)` 做斑马纹（隔行 `#F7F9FD`，末行可用浅主色 `#EAF1FE` 突出文中的结论项）；
- 左端 `0.12` 小色块标分类；名称 19 号 `move_to([IL+0.42, y, 0], aligned_edge=LEFT)`，两列数值 15 号；
- **两列数值分别右对齐到两条固定线**（如 A 工具列 `CM` 与 B 工具列 `IR`），表头同名对齐同一条线；
- 卡下留一行 caption，16 号 `AXC` 灰字注明数据口径。

行内别在两处写同一信息（如 A 列写"浏览器本体"、右侧又写一遍）。

#### ⚠️ 右对齐用 `next_to(pt, LEFT)`，不是 `RIGHT`

`next_to` 的第二个参数是**「把对象放到参照点的哪一侧」**，不是「对齐方式」。
`a.next_to(p, RIGHT)` 把 `a` 的**左边缘**贴到 `p`，整段文字往右长——想右对齐反而会冲出卡片。

```python
a.next_to([CM - 0.14, y, 0], LEFT, buff=0.0)   # ✅ 右边缘贴 CM-0.14
a.next_to([CM - 0.14, y, 0], RIGHT, buff=0.0)  # ❌ 左边缘贴 CM-0.14，往右溢出
```

#### ⚠️ 列值过长也要有宽度上限

右侧值是工具名时长度不可控（长名与短名能差 4 倍）。**不设上限，最长那条必然压出卡片**；
而 `fit_board` 对此**一次都不触发**——它算的是左右两大块的整体 bbox，右卡内部"列值越过 `IR`
伸出卡片"根本不在它的视野里（实测 `gap` 打印 +1.82、board 也在安全区内，图照样穿帮）。
定位办法见主篇 `wechat-cover.md` §五 方案 D。

```python
COLW = 1.92                        # 单列宽度上限
b = Text(v2, font=FONT, font_size=15, color=BLUE)
if b.width > COLW:
    b.scale_to_fit_width(COLW)     # 超宽整体缩，不要只调字号（会与相邻列不同基线）
b.next_to([IR, y, 0], LEFT, buff=0.0)
```

---

## 变体二：编号清单卡（最常用）

讲清单 / 讲几条原则 / 讲"哪几件事例外"的文章用得上：一行一个编号 + 名称 + 右对齐注解，
卡下一行 caption 收口。比清单/横评卡轻，适合 3~5 条。

```python
win = card(CW, CH).move_to([CX, 0, 0])
head = Text("退不回来的三件事", font=FONT, font_size=26, color=INK)
head.move_to([MCX, win.get_top()[1] - 0.52, 0])      # 按安全线中点定位，别用 next_to 传点
win.add(head)
hline = Line([IL, 0, 0], [IR, 0, 0], stroke_width=1.6, color=GRIDC)
hline.move_to([MCX, head.get_bottom()[1] - 0.26, 0])
win.add(hline)

y0 = hline.get_center()[1] - 0.66
for i, (num, name, desc) in enumerate(rows):
    y = y0 - i * 0.90
    bg = RoundedRectangle(width=0.44, height=0.44, corner_radius=0.09)
    bg.set_fill("#FFF1E6", opacity=1.0).set_stroke(width=0)
    badge = VGroup(bg, Text(num, font=FONT, font_size=21, color=ORAN).move_to(bg.get_center()))
    badge.move_to([IL + 0.22, y, 0])                  # 编号贴 IL
    nm = Text(name, font=FONT, font_size=24, color=INK)
    nm.next_to([badge.get_right()[0] + 0.24, y, 0], RIGHT, buff=0.0)   # 名称贴 badge 右侧
    ds = Text(desc, font=FONT, font_size=19, color=AXC)
    ds.next_to([IR, y, 0], LEFT, buff=0.0)              # 注解右对齐到 IR
    win.add(badge, nm, ds)

cap = Text("危险的不是「改」，是「改不回去」", font=FONT, font_size=19, color=GRAY)
cap.move_to([MCX, win.get_bottom()[1] + 0.42, 0])
win.add(cap)
```

- **名称列位置跟着 `badge.get_right()` 走，不要写死 x**——badge 尺寸变了名称自动跟；
- **注解列右对齐到 `IR`**，形成一条整齐的右边界；名称与注解都设 `COLW` 上限兜长文案；
- 纵向节奏实测（卡高 4.60、3 行）：标题距卡顶 `0.52`、分隔线距标题 `0.26`、行距 `0.90`、
  首行距分隔线 `0.66`、caption 距卡底 `0.42`。比变体一松，因为行内没有斑马纹垫底。
- 行数每加一条，`CH` 加约 `0.90`，或把 `CH` 封顶后压字号——**别压行距**，`0.90` 是可读下限。

---

## 变体三：编号网格卡（条目 ≥ 6 条时用）

变体二的行距下限 `0.90` 是硬的（别压行距），**6 条就要 `CH ≈ 4.60 + 3 × 0.90 ≈ 7.3`，
卡片直接顶穿版面**。条目多、且每条只有 2~6 字短标签时（如「六个误解」「Top 8」），
改 **2 列 × N 行 网格**，一个条目一张小 chip。

实测参数（6 条 / 2 列 × 3 行，卡 `CW 5.60` × `CH 4.75`）：

| 项 | 值 |
|---|---|
| chip 尺寸 | `CHIP_W × CHIP_H` = `2.37 × 0.74`，圆角 `0.14`，fill `#FFF7F0` / stroke `#FFD9BE` |
| 列距 `GX` / 行距 `GY` | `0.14` / `0.20`（行步距 `0.94`） |
| 首行中心 | `hline.get_center()[1] - 0.58` |
| 标签 | `Text(..., font_size=19, color=INK)` |
| 编号 | `Circle(radius=0.17)` 填 `ORAN` + 16 号白字，与标签 `arrange(RIGHT, buff=0.14)` |

接在变体二的 `win` / `head` / `hline` 之后：

```python
items = [("1", "越用越强"), ("2", "会自己上网学"),
         ("3", "是在增智"), ("4", "会越改越乱"),
         ("5", "记得越多越好"), ("6", "跟我没关系")]
CHIP_W, CHIP_H, GX, GY = 2.37, 0.74, 0.14, 0.20
x0 = MCX - (2 * CHIP_W + GX) / 2 + CHIP_W / 2
y0 = hline.get_center()[1] - 0.58
for i, (num, txt) in enumerate(items):
    cx = x0 + (i % 2) * (CHIP_W + GX)      # ⚠️ 行优先：读到的是 1 2 / 3 4 / 5 6
    cy = y0 - (i // 2) * (CHIP_H + GY)
    box = RoundedRectangle(width=CHIP_W, height=CHIP_H, corner_radius=0.14)
    box.set_fill("#FFF7F0", opacity=1.0).set_stroke("#FFD9BE", width=1.4)
    box.move_to([cx, cy, 0])
    circ = Circle(radius=0.17).set_fill(ORAN, opacity=1.0).set_stroke(width=0)
    ntx = Text(num, font=FONT, font_size=16, color="#FFFFFF").move_to(circ.get_center())
    lab = Text(txt, font=FONT, font_size=19, color=INK)
    row = VGroup(VGroup(circ, ntx), lab).arrange(RIGHT, buff=0.14)
    if row.width > CHIP_W - 0.28:
        row.scale_to_fit_width(CHIP_W - 0.28)
    row.move_to([cx, cy, 0])               # 只在 chip 内居中，不贴 IL/IR
    win.add(box, row)
```

三条实测结论：

1. **chip 内单行标签上限 = 6 个汉字 @19 号。** 实测 6 字那两行 `row_w = 2.04`，
   上限 `CHIP_W - 0.28 = 2.09`，**余量只剩 `0.05`**；7 字必超（汉字 @19 号实测约
   `0.26` 单位/字）⇒ 触发 `scale_to_fit_width` 把**这一个 chip 整行**缩小，
   六个 chip 字号就不一致了。超字数就换短标签，别放它缩。
2. **`CHIP_W = (卡内宽 − GX) / 列数`**，卡内宽 = `IR − IL` = `4.88` ⇒ 2 列即 `2.37`。
   列数往上加，chip 宽按此式同步缩，**先算一遍再定字号与字数**。
3. **编号按行优先**（`i % 2` 定列、`i // 2` 定行）。按列优先排，读者视线要上下跳。

⚠️ **网格卡内条目的定位逻辑与变体二相反**：变体二是「名称左贴 `IL`、注解右贴 `IR`」的
**跨行对齐**；网格卡每个 chip 自带边框，条目**只在自己 chip 内居中**
（`row.move_to([cx, cy, 0])`），**不要再贴 `IL`/`IR`**——照抄变体二会让编号顶住 chip
左边框、文字与边框不齐，而 `fit_board` 与 `gap` 都看不见（卡内元素不在两者视野里，
见主篇 `wechat-cover.md` §五 防裁切 的方案 D）。

卡下 caption 仍用 `win.get_bottom()[1] + 0.42`，与变体二一致。

---

## 三套变体都适用：垂直居中用 `move_to([0,0,0])` 而非 `shift(DOWN * x)`

卡下方挂了 caption 时整体 bbox 上下不对称（实测上留白 91px / 下留白 41px），
`shift(DOWN * 0.30)` 这类经验偏移是在**对称版面**上量出来的，照搬反而更歪。
内容非对称时直接 `board.move_to([0, 0, 0])` 按真实 bbox 居中。
