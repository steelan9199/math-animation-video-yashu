---
name: math-animation-video-yashu
description: 用 math-animation 连接器把数学/物理/论文知识点与题目渲染成教学动画视频（MP4、无配音）。激活条件：用户消息须包含以下关键词之一：`生成数学动画`、`数学动画视频`、`把 XX 做成动画视频`、`做数学讲解动画`、`真 3D 立体动画`、`排查 Manim 报错`、`论文动画`、`公式可视化`、`动画讲解`、`可视化这个原理`、`manim`。
version: 0.2.0
agent_created: true
---

# 数学动画视频（math-animation-video）

## 定位与硬约束

用 math-animation 连接器(MCP)把知识点渲染成教学动画片。**只出画面，不做配音。**

- **不出配音、不做 TTS**
- **默认 720p**（`quality="medium"`）、`mp4`、16:9、无字幕。用户另说才改。
- **默认风格 `khan_academy`**（白底、可汗蓝），面向中国高三的老师。
- 每次交付必须走完：**写代码 → 480p 预览 → 抽帧自检 → 720p 出片 → 抽帧复检 → 复制到工作目录 + 展示文件**。不得跳过自检直接说"做好了"。

## 本机固定事实（不要重新探测，除非报错）

| 项 | 值 |
|---|---|
| MCP 服务名 | `math-animation` |
| 渲染引擎 Python | `D:\software\uv\envs\py314-cpu\Scripts\python_direct.exe` |
| 引擎仓库 | `D:\github\math-animation-mcp`（源码在 `src\math_animation_mcp`） |
| 连接器输出目录 | `D:\github\math-animation-mcp\animation_output`（**固定，不可改**） |
| 默认中文字体 | `LXGW WenKai GB`（启动器注入为 `Text`/`MarkupText`） |
| ffmpeg / ffprobe | `D:\software\ffmpeg\ffmpeg-2024-09-26-git-f43916e217-full_build\bin\` |
| LaTeX | MiKTeX：`D:\software\MiKTeX\miktex\bin\x64\`（`MathTex` 可用） |
| Manim 版本 | **0.21.0（固定，勿升级）** |
| Manim 发行版 | **Manim Community Edition**（`Author: The Manim Community Developers`），非 3b1b 版 |
| **唯一官方仓库** | **https://github.com/ManimCommunity/manim**（社区版，`main` 即 0.21.0） |
| **Manim 依赖（版本权威）** | `D:\software\uv\envs\py314-cpu\Lib\site-packages\manim` |
| **Manim 源码** | `D:\github\manim` |

- 可用中文字体：`LXGW WenKai GB`、`Noto Sans SC`。查字体是否安装用 `windows-font-finder-yashu` 技能。

## 🔒 版本规则（硬约束，不可协商）

**本技能的版本固定为「Manim Community Edition 0.21.0」。** 所有 API 结论、所有模板代码
都只在这个版本上成立。**不要升级、不要混用其他发行版。**

开工前跑一次守门脚本，输出 `0.21.0` 才能继续：

```powershell
& "D:\software\uv\envs\py314-cpu\Scripts\python_direct.exe" "<本技能目录>/scripts/check_manim_version.py"
```

不是 `0.21.0` 就停下，提示用户：`当前manim版本号：xxx, 不是0.21.0，停止对本技能的的任何调用`。

## ⚠️ 遇到 Manim API 问题时（必读）

**不要凭记忆写 Manim API。** 本技能里的 API 论断都是在 **0.21.0 实测**过的，
但 Manim 迭代快。拿不准就按下面三步查证。

### 30 秒自查法（比翻文档还快）

```powershell
$P = "D:\software\uv\envs\py314-cpu\Scripts\python_direct.exe"
# 某个常量/类是否存在
& $P -c "import manim; print([n for n in dir(manim) if 'CYAN' in n])"
# 某个类有没有某个属性
& $P -c "from manim import Scene; print(hasattr(Scene,'time'))"
# 某个函数的准确签名
& $P -c "import inspect; from manim import interpolate_color; print(inspect.signature(interpolate_color))"
# 版本 + 锚点总校验
& $P "<本技能目录>/scripts/check_manim_version.py"
```

**已实测的 0.21.0 结论**：

| 论断 | 验证方式 |
|---|---|
| `from manim import *` **没有** `CYAN`/`MAGENTA`，但**有** `TEAL`/`PINK`/`GOLD`/`PURPLE` | `dir(manim)` 大写常量共 158 个 |
| `Scene` **没有** `time_since_start`；但**有** `self.time`（float，随 play 推进） | `hasattr` + `wait(0.3)` 后为 0.3 |
| `set_camera_orientation(phi=,theta=)` / `move_camera()` / `add_fixed_in_frame_mobjects()` 均为官方 API | 核对一致 |
| `interpolate_color(color1, color2, alpha)` 返回 `ManimColor` | `inspect.signature` |
| `Dot3D` 位于 `manim.mobject.three_d.three_dimensions` | import 成功 |

完整查证流程、本机源码位置表、性能实测见**`references/manim-api-troubleshooting.md`**。

## 渲染执行纪律（三条，都是踩过坑换来的）

### 1. 渲染一律 `run_in_background`，禁止前台执行

用 Bash/PowerShell 跑 `render_video.py` 时，**一律加 `dangerouslyDisableSandbox=true` + `run_in_background=true`**。

原因：**工具调用一旦返回/超时，它派生的子进程会一起被 SIGTERM 杀掉**，
Manim 渲染到一半就断，白等一整轮。

| 现象 | 真实原因 |
|---|---|
| 调用返回 `Exit Code: 1 / Signal: SIGTERM`，日志空 | 不是渲染失败，是**调用先结束，把 Manim 一起带走了** |
| `_render_spawn.log` 里某次 `SPAWN` **永远没有对应的 `DONE`** | 铁证：那次渲染被中途杀掉，从未跑完 |

- **判据**：`SPAWN` 与 `DONE` 必须成对。只有 `SPAWN` ⇒ 被误杀。
- **正确姿势**：`run_in_background=true` 启动 → 用 `TaskOutput` 阻塞等待（会自动收到完成通知），
  或按修改时间在 `animation_output` 找新文件。**不要用 `sleep` 硬等**。
- 若撞上「批量删除钩子」导致非零退出码：**不要重跑**，直接去 `animation_output` 看有没有新文件，
  有就按成功处理（注意 `_1` `_2` 后缀，用返回值的 `file_path` 或按修改时间挑最新的）。

### 2. 渲染「看起来卡住」时，先看临时目录，不要轮询干等

**这是本项目最大的一次时间浪费：一次失误导致约 27 分钟纯空转（占总时长 68%）。**

场景：Manim 场景里有 **20 万个 `Dot3D`**（每点一个 mobject），渲染在启动阶段就卡死不产出任何帧。
误判为「只是慢」，于是轮询 200 秒 + 两次 `sleep 45` 秒 —— 全部白等。

**卡住 30 秒后的正确动作（30 秒判定法）**：

```powershell
Get-ChildItem "D:\github\math-animation-mcp\_render_tmp\" -Directory |
  Sort-Object LastWriteTime -Descending | Select-Object -First 1 |
  ForEach-Object { Get-ChildItem $_.FullName -Recurse -File | Measure-Object }
```

- **只有 `scene.py`、没有任何媒体文件 ⇒ 不是慢，是根本跑不动**，立刻停手改代码。
- 正常渲染在几十秒内就会在 `media\videos\...` 下堆出成百上千个 PNG 分帧。

> ⛔ **禁止**：`sleep 45` / 轮询 20 次这类「干等确认」。**等之前先取一次证据。**
> 本机经验值：同一个场景，选对图元后 **5.5 s 出图**（对比卡死版），差 3 个数量级 ——
> 「慢」和「跑不动」是两件事，用临时目录一秒就能区分。

### 3. 何时用连接器、何时用降级脚本

预估渲染耗时 ≈ **预览耗时 × 3～5**（720p30 相对 480p15）。MCP `render_animation` 硬超时 **120 s**（已核实签名）。

- 预估 < 110 s → 直接调 MCP `render_animation`。
- 预估 ≥ 110 s，或**预览这一步本身就超过 100 s** → 直接用 `scripts/render_video.py`（同一套注入与风格管线，超时放宽到 900 s）。

**抽帧自检一律不过 MCP**：`preview_scene` / `render_gif` 都在 MCP 进程内跑 subprocess，
遇到删除钩子问题会把 MCP 一起带崩。自检直接跑 `scripts/contact_sheet.py`。

### 4. 排查代码错误：绕过包装层直接跑 manim

MCP 和 `render_video.py` 返回的 `error_msg` 是**截断的 Rich 回溯尾部**，看不到真正报错行。
完整排查流程、探针脚本写法、按耗时判性质（4~10 s = 代码报错 / 几十秒~几分钟 = 真在渲染）
见 **`references/pitfalls.md`**。

## 已知坑速查（6 条最高频）

**完整三张长表（环境与流程 / 配色与文字 / 动画机制 / 三维场景，共 40+ 条）全在
`references/pitfalls.md`。** 这里只留最容易忘的：

| 坑 | 一句话正确做法 |
|---|---|
| **逐点建 `Dot3D` 渲染点云** | 10 万个 mobject 必卡死。改单个 `PMobject` + `add_points()`，秒出 |
| **前台跑渲染** | 一律 `run_in_background`，否则工具调用一结束就把 Manim 带走 |
| **卡住靠 sleep 干等** | 等 30 s 无产出就看 `_render_tmp` 有没有帧，只有 `scene.py` = 跑不动 |
| **`MathTex` 默认白色** | 白底风格下先 `formula.set_color(INK)` 整组压深色 |
| **`Line`/`Arrow` 端点二维坐标会崩** | 必须写三维 `[x, y, 0]` |
| **卡片文字 `move_to([0, y, 0])` 全堆到原点** | 用 `fill_card()` 换算卡片中心坐标 |

其他高频项：字体名必须精确匹配（`LXGW WenKai GB` **带 GB**，漏了静默回退）、
`\mathrm{}` 里不能塞中文、`always_redraw` 回调必须零参数、`VGroup` 只有 `.add()` 没有 `.append()`、
两套配色渐变要用 HSV 转色相（RGB 插值中途掉进灰，实测彩度 0.083）。

## 真 3D 场景（ThreeDScene）

用户要「真 3D、相机环绕、立体感」时走这条路，不要用二维模板硬凑。
**完整可复制代码见 `references/scene-template.md` 的「三维场景模板」（3D-1 ~ 3D-10）。**

### 3D 场景的六个硬性要求

1. **必须先渲染标定场景**（20 秒廉价渲染）。`ThreeDScene` 是透视投影，
   「包围盒中点」≠ 画面中心，偏移严重程度靠推理判断不了。
2. **zoom 必须用 `cam.project_points()` 反算**。拟合区间按「这一幕实际会走到的机位」给；
   按全角度最坏情况拟合会让主体偏小约 25%。
3. **形变动画要把中间态也纳入拟合**（`lerp` 的中点），否则形变中主体冲出画面。
4. **文字一律 `add_fixed_in_frame_mobjects()`**，用完 `remove_fixed_in_frame_mobjects()`。
5. **运镜直接改 `cam.phi_tracker` / `theta_tracker` / `zoom_tracker`**，比反复调
   `set_camera_orientation()` 好控制。俯角要主动设计（如 `phi=68°`），别用默认视角。
6. **点云/分形类主体一律用 `PMobject` 承载**（>1 万点禁用 `Dot3D`）。

### 3D 配色过渡：转色相，不要 RGB 插值

两套配色之间做渐变时，**RGB 线性插值走到中途必然掉进灰**。
实测彩度最低掉到 **0.083**（肉眼就是一条灰带）；改用 HSV 旋转色相后全程稳定 **≥0.82**。
模板里有现成的 `band_color(frac, g)` 函数可直接用。

### 大批量点云的正确写法

```python
from manim.mobject.types.point_cloud_mobject import PMobject   # 顶层不导出，需显式 import

pm = PMobject(stroke_width=1.9)
rgba = np.concatenate([cols, np.ones((len(cols), 1))], axis=1)   # cols: (n,3) 0~1
pm.add_points(np.ascontiguousarray(P), rgbas=rgba, color=None)   # P: (n,3)
```

**根因**：Manim 每个 mobject 都要走单独的初始化 / 变换 / 排序流程。
`Dot3D` 逐点构造会把 mobject 数量推到 10 万级，渲染前的准备阶段就再也走不完
（**注意：不是渲染慢，是根本没开始渲染** —— 所以日志里连 frame 都没有，很容易误判成「卡住」）。

- **点数上限经验值**：单场景 `PMobject` 承载 **15 万点**实测流畅（渲染 35~49 s 全片）。
  超过就随机降采样（固定 `seed` 保证可复现）。
- `PGroup` 用于组合多个 `PMobject`；确定只需要一片点时用单个 `PMobject` 即可。

### 三维分形/隐式曲面的点云生成套路（曼德球实践）

用 numpy 在规则网格上算场、筛出「表面点」，再喂给 `PMobject`。以曼德球为例：

1. **网格分辨率**：`n=112`（`112³ ≈ 1.4M` 体素）→ **约 2 s** 出 14 万点，够用。
   `n=140` 要 4 s，收益不明显。
2. **只保留「贴表面」的点 —— 这一步不做，画出来就是个实心块。**
   判据：**首次越界的迭代步数 ≥ `min_steps`**。越界越晚 ⇒ 越贴近分形表面。
   ```python
   newly = alive & (r > 2.0)
   if k >= min_steps:          # 丢掉「第一步就飞出去」的外围点
       hit |= newly; steps[newly] = k; rfin[newly] = r[newly]
   alive &= ~newly             # 逃逸后必须冻结，防 inf/NaN 污染
   ```
3. **上色用两个物理量**：`steps`（逃逸步数）+ `rfin`（越界那一刻的半径）。
   步数越大、`rfin` 越接近 bail（2.0）⇒ 越亮，天然形成「表面高光」。
   再乘一个整体明暗因子，点云才有体积感而不是一层均匀的雾。
4. **不同参数的场半径可差很多**（实测 p=2 半径 1.83 vs p=8 的 1.15），
   必须**各自拟合 zoom**，否则沿用上一个参数的 zoom 会把主体顶出画面。

## 六种风格

| 风格 | 背景 | 适合 |
|---|---|---|
| `khan_academy` | 白 `#FFFFFF` | **默认**，中小学/高中 |
| `three_blue_one_brown` | 深灰 `#1C1C1C` | 科普、大学 |
| `textbook` | 浅灰 `#F5F5F5` | 正式教材 |
| `playful` | 暖黄 `#FFF8E1` | 小学低龄 |
| `dark_tech` | 纯黑 `#000000` | 竞赛、CS、真 3D |
| `blackboard` | 深绿 `#2D5016` | 模拟课堂 |

风格只改**背景色**。前景元素颜色必须在场景代码里自己写死（见「已知坑速查」第 4、5 条）。

## 标准流程

### 步骤 0：确认要讲什么

收集三件事：**讲哪个知识点/题目、受众年级、分几幕**。缺信息时最多问 1～3 个问题，
其余按默认静默决定：可汗学院白底风、高中生、每幕只讲一件事、总时长 30～50 s、结尾给一张小结卡片。

### 步骤 1：写场景代码

写到 **`<用户当前工作目录>/<ascii_name>_scene.py`**。类名必须 ASCII（渲染器靠 `class Xxx(Scene)` 正则取场景名）。

从 `references/scene-template.md` 的最小可靠模板改，比从零写快且少踩坑。

### 步骤 2：480p 预览

```powershell
& "D:\software\uv\envs\py314-cpu\Scripts\python_direct.exe" `
  "<本技能目录>/scripts/render_video.py" <scene.py> `
  --quality low --style khan_academy --timeout 900
```

加 `run_in_background=true` + `dangerouslyDisableSandbox=true`（见「渲染执行纪律」第 1 条）。

**3D 场景额外要求**：这一步之前必须已经渲染并肉眼确认过标定场景。

### 步骤 3：抽帧自检（必做）

```powershell
# 全片概览：--auto 自动算 every，保证 cols*rows 张图覆盖全片
& $P "<本技能目录>\scripts\contact_sheet.py" <预览mp4> --auto --cols 3 --rows 5 --out sheet.png
# 结尾段落必须单独再看一遍（闪白、收尾卡片最容易漏检）
& $P "<本技能目录>\scripts\contact_sheet.py" <预览mp4> --start 28.5 --auto --cols 3 --rows 2 --out tail.png
```

脚本会打印「覆盖= X s / 目标= Y s」，出现 `⚠️ 未覆盖全片` 就加大 `--rows` 或减小 `--every` 重跑。

然后用读图工具**亲眼看**这两张拼图，逐项核对：

1. 中文不是方框、没有缺字
2. 公式/文字在背景上**可见**（白底最容易出白字）
3. 元素不重叠、不出界、不压边缘（**同一时刻画面上只应有一行标题**）
4. 图形/数值与讲解内容一致（波形、坐标、标注都在对的位置）
5. 每一幕都有真实运动，不是静态画面
6. 标题、参数读数、小结卡片都在画面内
7. 渐变/形变过程中颜色**没有掉进灰色**，主体没有忽大忽小

发现问题 → 改代码 → 重跑步骤 2、3，**不要带着已知问题往下走**。

> **抽帧自检是唯一能抓到视觉缺陷的手段。** 「代码逻辑看着对」不等于「画面对」——
> 双层`LaggedStart` 不同步、RGB 插值变灰、卡片文字堆到原点，这三类问题代码都不会报错，
> 只有把帧抽出来用眼睛看才能发现。宁可多抽一轮。

### 步骤 4：720p 出片

按「渲染执行纪律」第 3 条判据选路径。

- MCP：工具 `render_animation`，参数 `code`、`quality="medium"`、`format="mp4"`、`style`
- 降级脚本：`render_video.py <scene.py> --quality medium --style khan_academy`

**输出目录固定**，重名会自动加 `_1`、`_2` 后缀。**必须用返回值里的 `file_path`**，不要自己猜文件名。

### 步骤 5：复检与交付

1. 对成片再跑一次 `contact_sheet.py --auto`（真实时长与预览不同，逐帧位置会变），结尾段落同样单独复检。
2. 用 `ffprobe` 核对分辨率/帧率/时长是否符合交付要求。
3. 复制到用户当前工作目录，起个中文名，例如 `正弦函数的图像变换_可汗学院风_720p.mp4`。
4. 用文件展示工具交付：**mp4 放第一位，场景源码 .py 放第二位**。
5. 回复里说清：时长、分辨率、每一幕讲了什么、以及**没配音**这一事实。

## 资源

| 文件 | 什么时候读 |
|---|---|
| `references/scene-template.md` | 写场景代码时。2D 最小模板 + 白底配色常量 + 卡片布局 + 参数扫描片段；**真3D 模板（3D-1~3D-10）** 含 `fit_zoom` 反算、运镜、色带辉光、HSV 配色、形变、光点、白闪、标定场景 |
| `references/pitfalls.md` | **排查具体问题时**。40+ 条已知坑（环境与流程 / 配色与文字 / 动画机制 / 三维场景）+ 代码错误排查流程 + 探针脚本 + 字体详解 |
| `references/manim-api-troubleshooting.md` | **写任何拿不准的 API 之前**。版本规则 + 查证流程 + 本机源码位置表 + 0.21.0 实测结论 + 性能实测 |
| `references/incidents/mandelbulb-postmortem.md` | 做点云/分形类场景前。27 分钟空转的完整事故链与耗时账 |
| `scripts/check_manim_version.py` | 开工前的版本守门 |
| `scripts/render_video.py` | 渲染。撞 MCP 超时或自检时用 |
| `scripts/contact_sheet.py` | 抽帧拼图自检。**必须先跑它再看图** |

> `push.js` 是本仓库的 git 提交脚本（`node push.js "说明"`），与技能功能无关，改完文件可用它提交并打 tag。
