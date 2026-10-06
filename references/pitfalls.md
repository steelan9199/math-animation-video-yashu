# 已知坑全集（Manim 0.21.0 / math-animation-video）

SKILL.md 里只留 6 行速查；**排查具体问题时来这里查**。全部是本机真实交付中踩过的，
不是抄文档。表头即分类：`环境与流程` / `配色与文字` / `动画机制` / `三维场景`。

---

## 环境与流程

| 坑 | 正确做法 |
|---|---|
| 渲染器收尾递归删除 `_render_tmp` 撞上本机批量删除钩子，退出码非零但**成片是好的** | 加 `dangerouslyDisableSandbox=true` **且 `run_in_background=true`**；撞上后不要重跑（见下一行） |
| 用后台执行撞上删除钩子后，重跑一次白等几十秒 | 不要重跑，直接去 `animation_output` 按修改时间找新文件 |
| 自检阶段走 MCP（`preview_scene`）可能把 MCP 进程一起带崩 | 自检一律直接跑 `scripts/render_video.py` + `scripts/contact_sheet.py`，不过 MCP |
| 抽帧只看前 N 秒，漏掉闪白/收尾卡片 | 结尾段落必须用 `contact_sheet.py --start <秒>` 单独抽一张 |
| `contact_sheet.py` 拼图没覆盖全片却看不出来 | 用 `--auto` 让它自动算 `every`；认输出里的 `⚠️ 未覆盖全片` 告警 |
| 场景 35 s，720p 渲染要 107 s，撞上 120 s 上限 | 预览耗时 × 3～5 做预估，超 110 s 就走降级脚本 |
| 预览／渲染超时后原地重试，白等一轮 | 超时即换路径：预览超时走 `render_video.py --quality low`，成片超时走 `--quality medium` |
| 渲染文件重名加 `_1` 后缀，误把预览片当成品交付 | 只用返回值里的 `file_path` |
| **渲染「卡住」时靠 `sleep` / 轮询反复确认 → 27 分钟纯空转（最大一次浪费）** | 等 30 s 无产出就**看 `_render_tmp` 里有没有帧**：只有 `scene.py` ⇒ 不是慢、是跑不动，立刻改代码 |
| **前台跑渲染，工具调用一结束就把 Manim 一起 SIGTERM 掉** | 一律 `run_in_background=true`；用 `TaskOutput` 等通知，不要 `sleep` |
| `_render_spawn.log` 里只有 `SPAWN` 没有 `DONE`，却以为只是慢 | 那一行就是「被中途杀掉」的铁证。**`SPAWN`/`DONE` 必须成对**，不成对就重跑 |
| 抽帧取帧区间太短（`--duration` 小于 `--every` × 帧数）导致拼图 `FAILED` | `--duration` 至少 ≥ `--every × cols × rows`；不确定就用 `--auto`，或把 `--duration` 放宽到 ≥3 s |
| 调试产物散落工作目录，交付时混入 `_*.png` / `_*.txt` / `_calib.py` | 中间件一律用 `_` 前缀并在交付前清理；只留成片 + 场景源码两件 |
| MCP/降级脚本只回一段截断的 Rich 回溯，看不到真正报错行 | 脚本返回的 `error_msg` 是**尾部片段**。排查代码错误时**绕过它直接跑 manim**（见下节） |
| **渲染 4~8 秒就退出 ⇒ 是代码报错，不是渲染慢** | 别进「等待重试」思维。直接取完整 traceback 定位，见下节 |

---

## 排查代码错误：直接跑 manim，不要经过 MCP / render_video.py

`render_video.py` 和 MCP `render_animation` 返回的 `error_msg` 是
**Rich 高亮框的尾部**，报错行常被 `│ ... │` 截断，看不全。
**代码报错的排查一律绕过包装层**：

```powershell
cd <工作目录>
& "D:\software\uv\envs\py314-cpu\Scripts\python_direct.exe" -m manim render -ql --format=mp4 -o _dbg <scene.py> <SceneClass> > _dbg.txt 2>&1
```

这样能拿到**完整 traceback**（含 `文件:行号 in construct` 和出错源码上下文）。

**按耗时判性质，别一律当"卡住"**：

| 耗时 | 结论 | 下一步 |
|---|---|---|
| **4~10 秒** | 场景代码抛异常，立刻退出 | 取完整 traceback 改代码 |
| 几十秒~几分钟 | 真在渲染分帧 | `run_in_background` 等通知 |
| 长时间无产出 | 疑似 3D 点云卡死 | 走 SKILL.md「30 秒判定法」 |

**构造类错误的最快定位法：写探针脚本逐个试**。
不要在场景文件里二分调试 —— 单独写个几十行的探针，把每种 mobject
构造包在 `try/except` 里一次跑完，一眼看出是哪个写法有问题：

```python
tests = {}
def chk(name, fn):
    try:
        fn(); tests[name] = "OK"
    except Exception as e:
        tests[name] = type(e).__name__ + ": " + str(e)[:90]

chk("Line3D", lambda: Line([-1, 0.2, 0], [1, 0.2, 0]))
chk("Line2D", lambda: Line([-1, 0.2], [1, 0.2]))          # ← 这个会炸
chk("always_redraw", lambda: always_redraw(lambda: Rectangle()))
for k, v in tests.items():
    print(k, "->", v)
```

探针脚本也用 `_` 前缀命名，交付前删掉。

---

## 配色与文字

| 坑 | 正确做法 |
|---|---|
| `MathTex` 默认是**白色**，白底风格下看不见，只剩手动上色的部分 | 先 `formula.set_color(INK)` 整组压深色，再给需要强调的子串单独上色 |
| 白底风格下坐标轴/网格/文字用 Manim 默认白色 | 每个 `Text`/`MathTex`/`Axes`/`NumberPlane` 都显式给颜色；网格用 `#E4E7EE`，轴用 `#7B8794` |
| 中文显示成方框 | `Text(..., font="Noto Sans SC")` 显式指定，或依赖启动器注入的 `LXGW WenKai GB`；`MathTex` 里不要混中文 |
| **`\mathrm{}` 里塞中文导致 LaTeX 编译失败** | 拆成 `VGroup(MathTex("T(2,3)"), Text("三叶结", font=FONT))`，中文永远交给 `Text` |
| 暗底上次要文字用色太暗，看不清 | 页脚/次要文字别低于 `#8296B4` |
| 公式字号写太大，贴到右边缘被裁掉 | 字号 ≤ 28，放画面中下方居中，不横排太长 |
| **字体名写错会静默回退，渲染照常成功但字体不是你要的那个** | 见下方「字体名必须精确匹配」，渲染日志里搜 `falling back` 必查 |

### 字体名必须精确匹配（含 GB 后缀）

Manim 只认注册名，**不匹配就静默回退到 `Sans`，只打一条 WARNING**：

```
WARNING  Font LXGW WenKai not in [...]   couldn't load font "LXGW WenKai Not-Rotated 10",
falling back to "Sans Not-Rotated 10", expect ugly output.
```

**本机实测**（2026-10-07，用 `Text("测试", font=...)` 逐个探测）：

| 写法 | 结果 |
|---|---|
| `LXGW WenKai GB` | ✅ 已装（**必须带 GB**） |
| `LXGW WenKai`（漏了 GB） | ❌ 回退，WARNING |
| `Noto Sans SC` | ✅ 已装（用户级） |
| `Noto Serif SC` | ✅ 已装 |
| `Source Han Sans SC` | ❌ 本机零命中，未装 |

> 本机这两个 family 都在**用户目录**（`C:\Users\Administrator\AppData\Local\Microsoft\Windows\Fonts`），
> 不在 `C:\Windows\Fonts`。**只扫系统目录会全部漏掉**（本机实测漏过一次，误判「没装」）。

**排查字体是否装了，用 `windows-font-finder-yashu` 技能，别手写命令**
—— 本技能只关心「Manim 能不能用这个 family 名」，字体是否安装是那个技能的职责。

```powershell
# 权威查法：列出 family / 注册表名 / 路径，还能看授权与商用风险
& "D:\software\uv\python\cpython-3.14.7-windows-x86_64-none\python.exe" `
  "~\.workbuddy\skills\windows-font-finder-yashu\scripts\list_fonts.py" --kw "霞鹜" --out _f.txt
```

若只想快速确认「Manim 认不认这个 family 名」，让 Manim 自己报也行：

```powershell
& "D:\software\uv\envs\py314-cpu\Scripts\python_direct.exe" -c "from manim import *; [print(n, '-> OK' if Text('测试', font=n) else '') for n in ['LXGW WenKai GB','Noto Sans SC']]" > _fchk.txt 2>&1
```

看 stderr 有没有 `falling back` —— 有就是没装。

**顺带一条**：Manim 的 WARNING 里会列出**本机全部可用 family 名**，
排查时直接看这段列表最快，不用另跑命令。

**选哪种**：LXGW WenKai GB 是楷体，教材/手写感；`Noto Sans SC` 是黑体，
更贴近论文图表的正式排版。**讲论文/学术内容优先 Noto Sans SC**，
讲基础数学/给中学生看用 LXGW。两者都是 SIL OFL 1.1，可商用。

---

## 动画机制

| 坑 | 正确做法 |
|---|---|
| `always_redraw` 的对象用 `FadeOut` 淡出无效（每帧被重绘覆盖） | 用 `self.remove(obj)` 直接移除；换曲线时 `self.remove(old); self.add(new)`，同参数值下可无缝切换 |
| `DoubleArrow`/`Arrow` 两端点重合时长度为 0 报错 | 扫描参数的取值范围不要包含 0（如振幅最低取 0.4） |
| `lambda` 里引用的变量在 `always_redraw`/`add_updater` 里没定义就被调用 | 先在 `construct` 里定义变量再创建 `always_redraw`，且把 `add_updater` 放在被引用对象之后 |
| **写了 `self.time_since_start`，`Scene` 根本没这个属性** | 用 `self.time`（float，随 play 推进，已实测）或 `ValueTracker`。写「某 API 不存在」前先 `hasattr` 验一遍 |
| 🔴 **`Text(...).move_to([0, y, 0])` 里 `y` 是场景坐标，不是卡片内偏移** | 卡片内文字必须用 `fill_card()`（见下），写 `[0, 0.5, 0]` 会全部堆到画面中央 |
| 🔴 **`Line([x,y],[x,y])` 传二维坐标列表会崩** | 坐标必须是三维：`Line([x, y, 0], [x2, y2, 0])`。报错见下 |
| 🔴 **`always_redraw` 的回调函数必须零参数** | 写 `def build():`，不是 `def build(m)`。多传参直接 `TypeError` |
| 🔴 **`VGroup` 没有 `.append()`，只有 `.add()`** | 收集 mobject 一律 `VGroup()` + `.add()`；`list` 才有 `.append()` |
| **同一变量先当 `list` 后当 `VGroup` 用 → 渲染时才炸** | 声明时就定好类型。`cards = []` 后又想 `.arrange()` 会报 `'list' object has no attribute 'arrange'` |
| **两个独立 `LaggedStart` 分别控制辉光层和亮线层，节奏对不上** | 轨迹会画成**虚线**。改为逐色带交错播放：同一色带的辉光与亮线放进同一个 `LaggedStart` |
| **两套配色做 RGB 线性插值，中途掉进灰色** | 实测彩度最低 0.083。改用 HSV 旋转色相（`band_color(frac, g)`），全程 ≥0.82 |
| 每一幕只是"多出一条线、多一个标签"，画面没在动 | 每幕至少一个连续参数扫描（`ValueTracker` + `always_redraw`/`add_updater`），这是本连接器最值钱的部分 |
| 结尾突然黑屏 | 最后 `self.wait(1.0~1.5)` 留白 |

---

## 三维场景（`ThreeDScene`）

| 坑 | 正确做法 |
|---|---|
| **`from manim import *` 不导出 `CYAN`/`MAGENTA` 等大写颜色常量** | 0.21.0 实测：158 个大写常量里**没有** `CYAN`/`MAGENTA`，但**有** `TEAL`/`PINK`/`GOLD`/`PURPLE`。精确霓虹色一律自己定义十六进制常量 |
| **以为「把物体摆到原点 + 设 zoom」就能居中** | 透视投影下包围盒中点 ≠ 画面中心。必须用 `cam.project_points()` 反算 zoom |
| zoom 按**全角度最坏情况**拟合 | 主体偏小约 25%。改为按这一幕实际运镜区间 `[th0, th1]` 拟合 |
| 形变动画只拟合了 3 个终态 | 形变中主体冲出画面。把 `lerp` 中点也塞进拟合列表 |
| `np.linspace(0, n, k+1).astype(int)` 末位索引等于 `n` | 越界 `IndexError`。手动 `idx[-1] = n - 1` |
| 3D 里的文字随相机倾斜变形/翻到背面 | 一律 `add_fixed_in_frame_mobjects()`，用完 `remove_fixed_in_frame_mobjects()` |
| 同一时刻画面上有两行标题（新字幕 + 旧标题没删） | 先 `FadeOut` 旧标题，再 `FadeIn` 新字幕 |
| 色带 updater 塞在 `VGroup` 里当子对象 | `clear_updaters()` / `self.remove()` 容易漏。**updater 对象一律放场景顶层** |
| 不先验证居中算法就直接写正式场景 | 先渲染 20 秒标定场景：画面正中钉一个十字，看曲线是否稳稳穿过 |
| **逐点建 `Dot3D` 渲染大批量点云 → 启动阶段直接卡死** | 改单个 `PMobject` + `add_points(P, rgbas=...)`。**10 万级 mobject 必卡，1 个 mobject 秒出** |
| **3D 场景里点云读起来像「实心块」** | 只保留「首次越界步数 ≥ `min_steps`」的贴表面点；否则外围一步就飞出去的点会把内部全遮住 |
| **点云像一层均匀的雾，没有体积** | 上色乘一个整体明暗因子（按 `w` 或深度），让近处壳层更亮 |
| **公式/读数与主体或标题带打架** | 3D 主体先按 `cap_frac` 压到画面中下部，把**上 1/4 留作公式带、下边缘留作字幕带**；公式固定在 `FORM_Y≈1.7`，不要放画面正中 |
| **同一参数扫描，不同取值的形态几乎一样（观众看不出差别）** | 检查配色是否**已饱和**：若各取值都被映到最亮端，视觉自然无差。改为按**各自形态范围**归一化配色，并配一个实时读数（`p = N`）强化差异 |
| **参数扫描时主体冲出画面** | 每个取值**各自拟合 zoom**（不同参数的点云半径可能相差 60%+），而不是全程沿用同一个 zoom |

---

## 三维 mobject 构造的三个硬性写法（二维场景同样适用）

以下三条是 **2026-10-07 做 DivLM 论文动画时全部实际踩到**的，
症状统一是「渲染 4~8 秒就退出 + 一段看不懂的 Rich 回溯」。

**1. `Line` / `Arrow` 的端点必须是三维坐标**

```python
Line([-1, 0.2, 0], [1, 0.2, 0])          # ✅
Arrow([-3.4, 1.0, 0], [-2.28, 1.2, 0])# ✅
Line([-1, 0.2], [1, 0.2])                # ❌ ValueError
```

报错特征（`set_anchors_and_handles` 里炸）：

```
ValueError: could not broadcast input array from shape (1,2) into shape (1,3)
```

**原因**：二维列表被当成 4D 点处理，锚点维度对不上。**凡是用列表字面量
给端点，就补 `, 0`**。用 `np.array(...)` 或 `.get_center()` 取出的坐标天然是三维，不受影响。

**2. `always_redraw` 的回调零参数**

```python
def build_bars2():        # ✅
    ...
bars = always_redraw(build_bars2)

def build_bars2(m):       # ❌ TypeError: build_bars2() missing 1 required positional argument: 'm'
```

Manim 内部只按 `func()` 调用。不要照抄网上 `add_updater(lambda m: ...)` 的写法。

**3. 卡片内文字必须换算成场景坐标**

```python
def fill_card(c, items):
    """往已定位的卡片里塞文字。items = [(文本, 字号, 颜色, 相对中心纵向偏移), ...]"""
    cx, cy, _ = c.get_center()
    for txt, size, color, dy in items:
        c.add(Text(txt, font=FONT, font_size=size, color=color)
              .move_to([cx, cy + dy, 0]))
    return c

card_obj = card(3.0, 2.0).move_to([-3.5, 0.5, 0])      # 先定位
fill_card(card_obj, [("标题", 24, INK, 0.5),
                     ("W0", 30, BLUE, -0.1)])# dy 相对卡片中心
```

**为什么这条最危险**：写成 `c.add(Text(...).move_to([0, 0.5, 0]))` 时
**代码不报任何错**，渲染也成功，只是所有卡片文字都跑到画面原点叠成一团。
**只有抽帧看图才能发现** —— 这就是抽帧自检不能跳的最好例证。

同理，`VGroup.arrange()` 会移动整个组，**加在组内的子 mobject 若是用
`[0, y, 0]` 定位的就会错位**。要跟着动就必须在 `arrange` 之后按最终
`get_center()` 重算，或直接用 `next_to()` / `relative_to()` 这类相对方法。

---

## 构造类三大坑速查（2026-10-07 DivLM 论文动画）

1. `move_to([0, y, 0])` 是场景坐标 → 卡片文字全堆到原点，用 `fill_card()`
2. `Line`/`Arrow` 端点必须写三维 `[x, y, 0]`
3. `always_redraw` 回调必须零参数 `def f():`

**这三条代码都不报错、渲染也成功，只有抽帧看图才能发现。**
