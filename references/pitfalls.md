# 已知坑全集（Manim 0.21.0 / math-animation-video）

SKILL.md 里只留硬约束与速查指针；**排查具体问题时来这里查**。全部是本机真实交付中踩过的，
不是抄文档。表头即分类：`环境与流程` / `配色与文字` / `动画机制` / `三维场景`。

---

## 环境与流程

| 坑 | 正确做法 |
|---|---|
| 渲染器收尾递归删除临时目录撞上本机批量删除钩子，退出码非零但**产物是好的** | 加 `dangerouslyDisableSandbox=true` **且 `run_in_background=true`**。撞上后**不要重跑**（重跑就是白等几十秒），直接去 `animation_output` 按修改时间找新文件 |
| 自检阶段走 MCP（`preview_scene`）可能把 MCP 进程一起带崩 | 自检一律直接跑 `scripts/render_video.py` + `scripts/contact_sheet.py`，不过 MCP |
| 抽帧只看前 N 秒，漏掉闪白/收尾卡片 | 结尾段落必须用 `contact_sheet.py --start <秒>` 单独抽一张 |
| `contact_sheet.py` 拼图没覆盖全片却看不出来 | 用 `--auto` 让它自动算 `every`；认输出里的 `⚠️ 未覆盖全片` 告警 |
| 成片预估落在 MCP 的 120 s 硬限附近，赌一把就超时 | 本机预览→成片实测倍率约 ×1.3～1.7，排期按 **×3 上限**估。预估 < 110 s 才调 MCP；≥ 110 s 直接走`render_video.py`。区间跨阈值时按上限算，不要赌 |
| 预览／渲染超时后原地重试，白等一轮 | 超时即换路径：预览超时走 `render_video.py --quality low`，成片超时走 `--quality medium` |
| 渲染文件重名加 `_1` 后缀，误把预览片当成品交付 | 只用返回值里的 `file_path` |
| **渲染「卡住」时靠 `sleep` / 轮询反复确认 → 27 分钟纯空转（最大一次浪费）** | 等 30 s 无产出就**查 MCP 临时目录有没有分帧文件**（见下节判性质表）：只有 `scene.py`、`media/` 里零文件 ⇒ 不是慢、是跑不动，立刻改代码 |
| **前台跑渲染，工具调用一结束就把 Manim 一起 SIGTERM 掉** | 一律 `run_in_background=true`；用 `TaskOutput` 等通知，不要 `sleep`。⚠️ **MCP 工具调用没有后台参数**，只能靠预估耗时分流 |
| `_render_spawn.log` 里只有 `SPAWN` 没有 `DONE`，却以为只是慢 | 那一行就是「被中途杀掉」的铁证。**`SPAWN`/`DONE` 必须成对**，不成对就重跑 |
| 抽帧取帧区间太短（`--duration` 小于 `--every` × 帧数）导致拼图 `FAILED` | `--duration` 至少 ≥ `--every × cols × rows`；不确定就用 `--auto`，或把 `--duration` 放宽到 ≥3 s |
| 调试产物散落工作目录，交付时混入 `_*.png` / `_*.txt` / `_calib.py` | 中间件一律用 `_` 前缀并在交付前清理；只留成片 + 场景源码两件 |
| MCP/降级脚本只回一段截断的 Rich 回溯，看不到真正报错行 | 脚本返回的 `error_msg` 是**尾部片段**。排查代码错误时**绕过它直接跑 manim**（见下节） |
| 非零退出码就断定「渲染失败」并重跑 | 先看日志有没有 `Traceback`：没有 Traceback 但 `animation_output` 里有新文件 = 收尾清理撞上删除钩子，**别重跑** |

---

## 排查代码错误：直接跑 manim，不要经过 MCP / render_video.py

`render_video.py` 和 MCP `render_animation` 返回的 `error_msg` 是
**Rich 高亮框的尾部**，报错行常被 `│ ... │` 截断，看不全。
**代码报错的排查一律绕过包装层**，按报错阶段选工具：

| 报错阶段 | 工具 | 是否渲染像素 | 耗时 |
|---|---|---|---|
| 构造 / 语法（`construct` 里抛异常） | `scripts/probe_charts.py` | ❌ dry_run | 秒 |
| 渲染期（mobject 数量、LaTeX、像素级） | `manim render -ql` | ✅ | 真实渲染耗时 |

```powershell
cd <工作目录>
& "D:\software\uv\envs\py314-cpu\Scripts\python_direct.exe" -m manim render -ql --format=mp4 -o _dbg <scene.py> <SceneClass> > _dbg.txt 2>&1
```

两种方式都能拿到**完整 traceback**（含 `文件:行号 in construct` 和出错源码上下文）。

### 判性质：看「日志有没有 Traceback」和「产物目录有没有文件」，不看耗时

**耗时不是判据**——本机实测（Manim 0.21.0，480p）：代码报错 **1.9 s** 退出，
最简成功场景 **2.5 s** 完成，**两个区间完全重叠**。任何「几秒内退出 = 报错」的规则都会误判。

| 证据 | 结论 | 下一步 |
|---|---|---|
| 日志含 `Traceback` / `Error` | 场景代码抛异常 | 取完整 traceback 改代码 |
| 无 Traceback，临时目录 `media/` 里**零文件** | 场景卡在构造阶段（典型：点云规模选型错） | 停下改代码 |
| 无 Traceback，`media/videos/<模块>/<画质>/partial_movie_files/` 里有 `.mp4` 分段且在增长 | 真在渲染 | `run_in_background` 等通知，别问 |

**「慢」与「跑不动」的分辨**：渲染卡住时不要 sleep、不要轮询，直接查 MCP 临时工作目录
`<引擎仓库>/_render_tmp/manim_render_*/`——里面只有 `scene.py`、`media/` 零文件 ⇒ 不是慢，
是**跑不动**（正常渲染会往 `partial_movie_files/` 持续写 `.mp4` 分段，本机实测 6 秒时已写 225 个）。
一行查法：

```powershell
Get-ChildItem "D:\github\math-animation-mcp\_render_tmp" -Directory |
  Sort-Object LastWriteTime -Descending | Select-Object -First 1 |
  ForEach-Object { Get-ChildItem $_.FullName -Recurse -File | Measure-Object }
```

**探针脚本**：构造类错误不用自己手写——`scripts/probe_charts.py` 已经做了这件事
（自动发现文件里所有场景类、逐个 `dry_run`、打印完整 traceback）。直接用它。

---

## 配色与文字

| 坑 | 正确做法 |
|---|---|
| `MathTex` 默认是**白色**，白底风格下看不见，只剩手动上色的部分 | 先 `formula.set_color(INK)` 整组压深色，再给需要强调的子串单独上色 |
| 白底风格下坐标轴/网格/文字用 Manim 默认白色 | 每个 `Text`/`MathTex`/`Axes`/`NumberPlane` 都显式给颜色；网格用 `#E4E7EE`，轴用 `#7B8794` |
| 中文显示成方框 | `Text(..., font="Noto Sans SC")` 显式指定，或依赖启动器注入的 `LXGW WenKai GB` |
| **`\mathrm{}` / `\text{}` 里塞中文，或用 `Title()`，导致 LaTeX 编译失败** | 本机 LaTeX **没装 ctex 中文支持**，报 `latex error converting to dvi` ⇒ **一张图都不产出**。中文标题/词组一律 `Text(..., font=FONT)`，公式用纯英文 `MathTex`。本机实测：`Text`（中/英）、纯英文 `MathTex` 均正常，只有 `Title()` 和 `\text{中文}` 会炸 |
| 暗底上次要文字用色太暗，看不清 | 页脚/次要文字别低于 `#8296B4` |
| 公式字号写太大，贴到右边缘被裁掉 | 字号 ≤ 28，放画面中下方居中，不横排太长 |
| **字体名写错会静默回退，渲染照常成功但字体不是你要的那个** | 见下方「字体名必须精确匹配」，渲染日志里搜 `falling back` 必查 |

### 字体名必须精确匹配（含 GB 后缀）

Manim 只认注册名，**不匹配就静默回退到系统默认无衬线字体，只打一条 WARNING**
（WARNING 走 logger，不落 stdout/stderr —— 想自动判定必须捕获 logging，不是 `sys.stderr`）。
日志形态如下（`<X>` 代表一个**拼错的 family 名**，本技能规定不把非白名单字体名写进任何文件，
所以这里用占位符代替真实名字）：

```
WARNING  Font <X> not in [...]   couldn't load font "<X> Not-Rotated 10",
falling back to "Sans Not-Rotated 10", expect ugly output.
```

**本机实测**（复查安装用 `windows-font-finder-yashu`；Manim 认不认用 `Text` 探测）：

| 白名单字体 | 安装 | Manim 可用 |
|---|---|---|
| `Noto Sans SC` | ✅ 用户级 | ✅ 无 WARNING |
| `LXGW WenKai GB` | ✅ 用户级 | ✅ 无 WARNING |
| 上述楷体名**去掉尾部 ` GB` 后缀** | — | ❌ 回退 + WARNING |

> 两个 family 都在**用户目录**（`AppData\Local\Microsoft\Windows\Fonts`），
> 不在 `C:\Windows\Fonts`。**只扫系统目录会全部漏掉**（本机实测漏过一次，误判「没装」）。
> 查是否安装用 `windows-font-finder-yashu` 技能（它还列授权与商用风险）。

若只想确认「Manim 认不认白名单这两个」，让 Manim 自己报：

```powershell
& "D:\software\uv\envs\py314-cpu\Scripts\python_direct.exe" -c "from manim import *; [print(n, '-> OK' if Text('测试', font=n) else '') for n in ['LXGW WenKai GB','Noto Sans SC']]" > _fchk.txt 2>&1
```

日志里出现 `falling back` 就是没装/名字写错了。**顺带一条**：Manim 的 WARNING 里会
列出**本机全部可用 family 名**，排查时直接看这段列表最快，不用另跑命令。

**选哪种**：讲论文/学术内容优先 `Noto Sans SC`（黑体，正式排版），
讲基础数学/给中学生看用 `LXGW WenKai GB`（楷体，教材手写感）。
**封面一律用黑体**，理由与授权结论见 `wechat-cover.md` §二 字体授权。

---

## 动画机制

| 坑 | 正确做法 |
|---|---|
| `always_redraw` 的对象用 `FadeOut` 淡出无效（每帧被重绘覆盖） | 用 `self.remove(obj)` 直接移除；换曲线时 `self.remove(old); self.add(new)`，同参数值下可无缝切换 |
| `DoubleArrow`/`Arrow` 两端点重合时长度为 0 报错 | 扫描参数的取值范围不要包含 0（如振幅最低取 0.4） |
| `lambda` 里引用的变量在 `always_redraw`/`add_updater` 里没定义就被调用 | 先在 `construct` 里定义变量再创建 `always_redraw`，且把 `add_updater` 放在被引用对象之后 |
| **写了 `self.time_since_start`，`Scene` 根本没这个属性** | 用 `self.time`（float，随 play 推进，已实测）或 `ValueTracker`。写「某 API 不存在」前先 `hasattr` 验一遍，结论见 `manim-api-troubleshooting.md` §3.2 `Scene` 的时间属性 |
| **三个静默失败的构造写法**（`move_to([0,y,0])` 让卡片文字堆到原点 / `Line` 端点传二维 / `always_redraw` 回调带参） | 见下方「构造类三个硬性写法」 |
| **`VGroup` 没有 `.append()`，只有 `.add()`** | 收集 mobject 一律 `VGroup()` + `.add()`；`list` 才有 `.append()` |
| **同一变量先当 `list` 后当 `VGroup` 用 → 渲染时才炸** | 声明时就定好类型。`cards = []` 后又想 `.arrange()` 会报 `'list' object has no attribute 'arrange'` |
| **两个独立 `LaggedStart` 分别控制辉光层和亮线层，节奏对不上** | 轨迹会画成**虚线**。改为逐色带交错播放：同一色带的辉光与亮线放进同一个 `LaggedStart` |
| **两套配色做 RGB 线性插值，中途掉进灰色** | 实测彩度最低 0.083。改用 HSV 旋转色相（`band_color(frac, g)`），全程 ≥0.82 |
| 每一幕只是"多出一条线、多一个标签"，画面没在动 | 每幕至少一个连续参数扫描（`ValueTracker` + `always_redraw`/`add_updater`），这是本连接器最值钱的部分 |
| 结尾突然黑屏 | 最后 `self.wait(1.0~1.5)` 留白 |

---

## 三维场景（`ThreeDScene`）

| 坑 | 正确做法 |
|---|---|
| **`from manim import *` 不导出某些大写颜色常量**（如 `CYAN`/`MAGENTA`） | 想要精确霓虹色一律自己定义十六进制常量，不要赌名字是否存在。完整实测清单见 `manim-api-troubleshooting.md` §3.1 `from manim import *` 到底导出了什么颜色常量 |
| **以为「把物体摆到原点 + 设 zoom」就能居中** | 透视投影下包围盒中点 ≠ 画面中心。必须用 `cam.project_points()` 反算 zoom（实现见 `scene-template-3d.md` 3D-2 `fit_zoom`） |
| zoom 按**全角度最坏情况**拟合 | 主体偏小约 25%。改为按这一幕实际运镜区间 `[th0, th1]` 拟合；形变还要把 `lerp` 中点塞进拟合列表 |
| `np.linspace(0, n, k+1).astype(int)` 末位索引等于 `n` | 越界 `IndexError`。手动 `idx[-1] = n - 1` |
| 3D 里的文字随相机倾斜变形/翻到背面 | 一律 `add_fixed_in_frame_mobjects()`，用完 `remove_fixed_in_frame_mobjects()` |
| 同一时刻画面上有两行标题（新字幕 + 旧标题没删） | 先 `FadeOut` 旧标题，再 `FadeIn` 新字幕 |
| 色带 updater 塞在 `VGroup` 里当子对象 | `clear_updaters()` / `self.remove()` 容易漏。**updater 对象一律放场景顶层** |
| 不先验证居中算法就直接写正式场景 | 先渲染 20 秒标定场景：画面正中钉一个十字，看曲线是否稳稳穿过（见 `scene-template-3d.md` 3D-10） |
| **逐点建 `Dot3D` 渲染点云 → 启动阶段就卡死** | 改单个 `PMobject` + `add_points(P, rgbas=...)`。**不设规模例外**，见下方实测 |
| **3D 场景里点云读起来像「实心块」** | 只保留「首次越界步数 ≥ `min_steps`」的贴表面点；否则外围一步就飞出去的点会把内部全遮住 |
| **点云像一层均匀的雾，没有体积** | 上色乘一个整体明暗因子（按 `w` 或深度），让近处壳层更亮 |
| **公式/读数与主体或标题带打架** | 3D 主体先按 `cap_frac` 压到画面中下部，把**上方留作公式/字幕带**；字幕用 `add_fixed_in_frame_mobjects` 钉在 `SUB_Y`（`UP * SUB_Y`），公式固定在 `FORM_Y≈1.7`，**都不要放画面正中** |
| **同一参数扫描，不同取值的形态几乎一样（观众看不出差别）** | 检查配色是否**已饱和**：若各取值都被映到最亮端，视觉自然无差。改为按**各自形态范围**归一化配色，并配一个实时读数（`p = N`）强化差异 |
| **参数扫描时主体冲出画面** | 每个取值**各自拟合 zoom**（不同参数的点云半径可能相差 60%+），而不是全程沿用同一个 zoom |

### 点云图元：为什么没有「规模阈值」

`Dot3D` 与 `PMobject + add_points()` 的实测耗时（Manim 0.21.0，CPU，每档取 3 次中位数）：

| 点数 | `Dot3D` 构建 | `PMobject` 构建 | `Dot3D` 出帧 | `PMobject` 出帧 | 构建耗时倍率 |
|---|---|---|---|---|---|
| 1 000 | 11.6 s | 0.001 s | 31.1 s | 0.008 s | ~1 万倍 |
| 2 000 | 23.2 s | 0.001 s | 62.3 s | 0.008 s | ~2 万倍 |

两条规律：

- **`Dot3D` 线性增长**：约 **11.6 ms/点**（1000→2000 点，构建耗时正好翻倍）。
  据此外推：2 万点 ≈ 构建 3.9 min，10 万点 ≈ 构建 19 min。
- **`PMobject` 与点数无关**：构建恒定 ~0.001 s、出帧恒定 ~0.008 s——加点是塞数组，不是造对象。

**结论：不存在交叉点，所以不设阈值。** 1000 点这种"小规模"场景 `Dot3D` 都已经慢到不可接受，
写"> 1 万点才用 `PMobject`"会暗示小规模可以用 `Dot3D`，那是错的。

> 口径提醒：**构建倍率**约 1 万倍（11.6 s vs 0.001 s），**出帧倍率**约 3900 倍（31.1 s vs 0.008 s）。
> 两个数指的是不同阶段，别混着引。实测只做到 2000 点就停（斜率已经完全线性，再往上纯属浪费机时）。
> 这也复演了一遍事故机制——`Dot3D` 的**磁盘上一个帧都没有**，看着像"慢"，实则根本没开始渲染。

## 构造类三个硬性写法（二维/三维通用）

以下三条症状统一是「代码不报错、渲染也成功，只有抽帧看图才能发现」。

**1. `Line` / `Arrow` 的端点必须是三维坐标**

```python
Line([-1, 0.2, 0], [1, 0.2, 0])          # ✅
Line([-1, 0.2], [1, 0.2])                # ❌ ValueError
```

**原因**：二维列表被当成 4D 点处理，锚点维度对不上。报错固定是
`ValueError: could not broadcast input array from shape (1,2) into shape (1,3)`
（`set_anchors_and_handles` 里炸）。**凡是用列表字面量给端点，就补 `, 0`**；
用 `np.array(...)` 或 `.get_center()` 取出的坐标天然是三维，不受影响。

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
# ❌ 所有卡片文字堆到画面原点叠成一团，代码不报任何错
c.add(Text(txt, font=FONT).move_to([0, 0.5, 0]))

# ✅ 按卡片实际中心换算（可复制实现见 scene-template.md 的 fill_card）
cx, cy, _ = c.get_center()
c.add(Text(txt, font=FONT).move_to([cx, cy + dy, 0]))
```

**为什么这条最危险**：错写法**代码不报任何错**，渲染也成功，只是画面糊成一团。

同理，`VGroup.arrange()` 会移动整个组，**组内若有用 `[0, y, 0]` 绝对坐标定位的子 mobject
就会错位**——所以必须**先 `fill_card()` 再 `arrange()`**；要在 arrange 之后填字，
就按最终 `get_center()` 重算，或直接用 `next_to()` / `relative_to()` 这类相对方法。
