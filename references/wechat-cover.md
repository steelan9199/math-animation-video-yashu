# 微信公众号封面（manim 路线）

**触发**：用户说「做公众号封面」「配封面图」「文章头图」「公众号配图」「金句卡」「要点卡」，
不论封面里有没有公式、图表、插画——**公众号封面全部由本技能产出**。

**能力边界**：manim 是矢量排版引擎，文字 + 图形都能画，所以以下类型都走本技能：

| 封面类型| 做法 |
| -------------------------------- | ------------------------------------------------------- |
| **公式 / 函数图像 / 柱状折线图 / 几何图形 / 三维结构** | 左文右图版式（见 §六），右侧图卡放公式与图表 |
| **纯文字排版 / 金句卡 / 要点卡** | 单卡居中版式：大字主标 + 细分割线 + 底部落款，靠 `fit_board` 兜底缩放（见 §6.2） |
| **人物 / 场景插画** | 用几何图元拼装示意性图形；**照片级 / 手绘级插画本技能做不了**，直接告诉用户这个限制，不要硬凑 |

---

## 一、尺寸：只有两个规格，别自创

| 用途                      | 比例       | 实际输出（本机统一出 2 倍） |
| ----------------------- | -------- | --------------- |
| **大图 / 头条封面**（默认，几乎都这个） | 2.35 : 1 | **1800 × 766**  |
| 小图 / 次条列表缩略             | 1 : 1    | 1080 × 1080     |

- 出 2 倍分辨率是给后台压缩留余量，比例不变。**不要出 4 倍**，文件白大一倍没人看得出。
- 比例不对 = 微信后台会裁。发布前若不确定，以后台实际裁切框为准。
- 只做大图时不必问用户；用户明确说「次条」「小图」才切 1:1。

## 二、字体授权：两款都可商用，但封面只用黑体

公众号封面会公开发布、有商业属性，**字体必须可商用**。白名单两款都是 SIL OFL 1.1，
用户级安装，差别只在**封面适用性**：

| 字体 | 封面适用 | 理由 |
|---|---|---|
| **`Noto Sans SC`** | ✅ **封面默认** | 黑体系，远看清爽，列表页缩略图辨识度好 |
| **`LXGW WenKai GB`** | ❌ 封面别用 | 楷体笔画在 1080/1800 宽的小尺寸下发虚；它是**视频正文/字幕**的字体 |

规则：

- **白名单只有两个名字，一律照抄**（`SKILL.md` 硬约束 1）。
  想查某个名字能不能用、装没装，问 `windows-font-finder-yashu`，别凭印象写进 `font=`。
- **SIL OFL 1.1 允许**：商用、修改字体、把字体渲染进图片/视频。
  唯一义务是**不得单独售卖字体文件本身**。「渲染成公众号封面」属于正常使用，完全合规。
- **封面固定用 `Noto Sans SC`**：黑体系，适合远看，公众号列表页缩略图下辨识度最好。
  白名单里的楷体**笔画在小尺寸下发虚，封面别用**（视频正文/字幕才是它的适用场景）。
- 本机两款均已安装于**用户目录** `AppData\Local\Microsoft\Windows\Fonts`
  （不在 `C:\Windows\Fonts`，只扫系统目录会误判「没装」）。

## 三、渲染命令：直接跑 manim，不走 MCP、不走 render_video.py

```powershell
cd <工作目录>
& "D:\software\uv\envs\py314-cpu\Scripts\python_direct.exe" -m manim render `
  --renderer=cairo --format=png -s --resolution 1800,766 `
  --media_dir "<工作目录>/_cover_media" <scene.py> <ClassName> > _cover_render.log 2>&1
```

或用封装脚本（推荐：自动把 `x` 转成 `,`、校验产物是不是本次新生成的、检查字体回退、拷贝成品）：

```powershell
& "D:\software\uv\envs\py314-cpu\Scripts\python_direct.exe" `
  "<技能目录>\scripts\render_cover.py" <scene.py> <ClassName> `
  --res 1800x766 --out "公众号封面_主题_1800x766.png"
```

> ⚠️ **`--resolution` 只认逗号，不认字母 x**。传 `1800x766` 会报  
> `Resolution option is invalid` 且**一个文件都不产出**，但退出码仍是 0 ——  
> 极易误判成"渲染成功"。`render_cover.py` 已内置这个转换。

执行纪律：

- **一律 `run_in_background=true` + `dangerouslyDisableSandbox=true`**（`SKILL.md` 硬约束 3）。
  只给 `run_in_background` 而没关沙箱，会撞上本机批量删除钩子，退出码非零但**产物是好的**。
- **`--renderer=cairo`**：纯 CPU、无 GPU 依赖、PNG 带抗锯齿，比 opengl 稳。
- **`-s`**：只保存最后一帧。封面是静态图，不要 mp4、不要 `--quality`。
- **不要用 `scripts/render_video.py`**：它会注入默认中文字体 `LXGW WenKai GB`，  
  封面需要自己指定 `Noto Sans SC`，走它字体会被改掉。
- **不要用 MCP 的 `render_animation`**：那是视频接口，输出 mp4。
- **不要用 `contact_sheet.py`**：它处理 mp4 抽帧，PNG 用不着。封面自检就是**直接看图**。

### ⚠️ 哈希缓存导致「假成功」（做封面最容易踩）

manim 按场景文件哈希判断是否需要重渲染。**场景文件没改动时它会直接跳过**，  
`media_dir` 里留着上一轮的 PNG。如果只按「文件名取最新」去找产物，就会把  
**上一轮的旧图**当成新图交付——图看着挺好，其实根本没重渲染，改动全没生效。

判断依据：用时 **1~2 秒** = 命中缓存；真实渲染约 **4~6 秒**。

对策（三选一）：

1. **改了场景代码后再跑**（加个空行都能解除缓存）；
2. 直接删 `<media_dir>/images/<场景模块名>/` 再跑；
3. **拿产物时按 mtime ≥ 本次启动时间过滤**（`render_cover.py` 已这样做，  
   只发现旧产物时会明确报错，不会静默交付旧图）。

产物路径：`<media_dir>/images/<模块名>/<ClassName>_ManimCE_v0.21.0.png`  
—— 文件名由**场景文件名**决定，所以场景文件名的 ASCII 名字要起得有意义（如 `chart_mcp_cover_scene.py`）。

日志必查两件事（别看整份日志，直接跑）：

```powershell
Select-String -Path _cover_render.log -Pattern 'falling back','Error','Traceback' -SimpleMatch
```

- 无输出 = 干净。`falling back` = 字体没找到、静默回退成默认字体 → 中文会变成非预期字形，**必须为 0**。
- `Error` / `Traceback` = 代码错。

## 四、画面比例：必须重设 frame（最大的坑）

Manim 默认 `frame_width = 14.222`、`frame_height = 8`，是 16:9。**直接用它渲染 2.35:1 的图，  
画面会被上下压扁 / 主体缩在中间一条**——代码不报错，只是难看。必须在 **import 之后、模块顶层**改：

```python
from manim import *

config.frame_width = 14.222
config.frame_height = 14.222 * 766 / 1800      # = 6.052，严格锁 2.35:1
```

- **写在模块顶层**（已验证）。不要挪进 `construct()`——那时 camera 已按旧尺寸建立。
- 比例算对了，`font_size` / `card(w,h)` 的手感才和视频模板一致。1 单位 ≈ 126.5 px（@1800 宽）。

## 五、防裁切：靠代码断言，不靠目测估文字宽度

封面最常见的事故是**文字溢出画布被裁掉一截**。原因：中文宽度随字号线性增长，  
而 `frame_width=14.222` 下留白只有十来个单位，凭感觉估不准。

**方案 A（首选，兜底自动缩）**：全场景组装成一个 `VGroup`，收尾统一压进安全区。
`fit_board()` 的可复制实现见 §六模板（8 行），逻辑是「宽高超限就整体缩放」。

**方案 B（调试时先看一眼数）**：

```python
print(f"[cover] board {board.width:.2f}x{board.height:.2f} / "
      f"frame {config.frame_width:.2f}x{config.frame_height:.2f}")
```

`board.width > frame_width` ⇒ 一定会被裁，先改字号/文案再往下走。

**垂直位置最后统一调**，不要每轮重排：内容全部 `add` 完之后

```python
board = VGroup(left, right).shift(DOWN * 0.30)   # 上留白 < 下留白时往下压
self.add(board)
```

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

## 七、封面专属坑（与视频不同的点）

| 坑 | 正确做法 |
|---|---|
| 忘了改 `frame_height`，画面比例错 | 模块顶层锁 `config.frame_height = frame_width * H / W` |
| 文字溢出画布被裁 | `fit_board()` + 打印 board 尺寸，**不要目测估中文宽度** |
| 竖排文字/多行卖点在卡片里堆到原点 | `in_card(cx, cy, [(m, dx, dy)])` 相对摆位，或 `arrange` **后**按 `get_center()` 重算 |
| `MathTex` 在白底上看不见（纯白） | `set_color(INK)`；次要公式用 `GRAY` |
| 公式撑出卡片 | 窄卡（宽 2 单位）公式字号 **20~24**，并预留卡片内边距 |
| 中文静默回退成默认字体 | 日志 grep `falling back`，必须为 0；字体名精确到 `Noto Sans SC` |
| `Line`/`Arrow` 端点写二维会崩 | 必须 `[x, y, 0]` |
| 用 render_video.py 导致字体被注入成楷体 | 封面直接 `python -m manim render` |
| 卡片数量多导致画面碎 | **最多 3 张卡**，封面要一眼看完 |
| 上下留白不均 | 内容 add 完后统一 `shift(DOWN * x)`，最后一次调 |
| **`arrange(aligned_edge=CENTER)` 报 `NameError: CENTER`** | 0.21.0 **没有 `CENTER` 常量**（只有 `UP/DOWN/LEFT/RIGHT/ORIGIN`）。居中用 `arrange(DOWN, buff=0.3, center=True)`——`arrange` 有 `center: bool` 参数 |
| **手填 `move_to` 坐标排版，换文案就重叠/被裁** | 一律用 `next_to(参照物, 方向, buff=…)` 按**实际边界**串版面；最后 `board.move_to([0,0,0])` 垂直居中。金句卡模板见 §6.2 |

## 八、自检清单（渲染后必须亲眼看图）

PNG 是静态图，**不需要抽帧拼图**，直接用读图工具打开成品逐条核对：

1. 中文不是方框、没有缺字、没有回退字形（对照日志 `falling back` = 0）
2. **四边留白完整**：左端/右端的字没有被裁掉半个字
3. 公式可见（不是白字）、不出卡片
4. 元素不重叠、不出界、卡片间距均匀
5. 卡片底部标签都在卡内、同一条基线
6. 竖排层次：标签 → 主标题 → 副标 → 卖点，视觉顺序一眼能读
7. 配色克制：白底 + 1 主色 + 1 强调色，最多再加 1 个辅助色

发现问题 → 改代码 → 重渲染。封面单帧渲染 **3~5 秒**，  
实测一次三轮迭代很正常，**不要因为"多跑一轮"就省掉目检**。

## 九、交付

1. 成品 PNG 复制到用户当前工作目录，起中文名：`公众号封面_<主题>_<宽>x<高>.png`
2. `present_files`：**PNG 放第一位，场景源码 `.py` 放第二位**
3. 回复里说清：尺寸比例、版式要点、**纯 manim 生成无 AI 生图**、
   以及"要 1:1 小图版本就说一声"
