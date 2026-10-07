---
name: math-animation-video-yashu
description: 用 math-animation 连接器(MCP)把数学/物理/论文知识点与题目渲染成教学动画视频（MP4、无配音），并能用同一套manim 管线生成微信公众号封面图与各类数据/结构图表（柱状图、折线图、饼图、流程图、思维导图、鱼骨图、甘特图、桑基图、热力图、雷达图、组织架构图等，清单见 references/chart-generation.md）。激活条件：用户消息含以下关键词之一：`生成数学动画`、`数学动画视频`、`把 XX 做成动画视频`、`做数学讲解动画`、`真 3D 立体动画`、`排查 Manim 报错`、`论文动画`、`公式可视化`、`动画讲解`、`可视化这个原理`、`manim`、`公众号封面`、`公众号配图`、`做封面`、`文章头图`、`封面图`、`画图表`、`做图表`、`生成图表`、`数据可视化`。
version: 1.8.1
---

# 数学动画视频（math-animation-video）

## 一、先判断要什么产物（走错路线 = 全部白做）

| 用户要什么 | 走哪条 | **开工必读** |
|---|---|---|
| 教学动画视频（MP4） | 主线流程（见 §四 标准流程） | `references/scene-template.md` |
| 公众号封面 / 文章头图（PNG）——含公式、图表、几何结构，以及纯文字排版 / 金句卡 / 要点卡 | 封面路线 | `references/wechat-cover.md` |
| 数据图表 / 结构图 | 图表路线 | `references/chart-generation.md` |

两条静态图路线**不走** MCP `render_animation`、**不走** `render_video.py` / `contact_sheet.py`，
各有自己的命令与坑。**所有公众号封面都归本技能**，无论有没有公式图表。

**能力边界（先判断能不能做，别硬凑）**：产物**只有上表三类**，全是manim 矢量绘制——
**零 AI 生图、无配音**。做不了：照片级/手绘级插画、真实数据统计结论、音频。
落在边界外直接说明限制，别用近似图形凑。
**核心认知：manim 不止做数学动画**——任何信息图都是「坐标 + 图元 + 文字」，
难点在**版面**不在图形（详见 `references/chart-generation.md` 开头）。

## 二、不可违反的硬约束

1. **🔒 字体白名单（全库唯一两个字体名）**：**只允许 `Noto Sans SC` 与 `LXGW WenKai GB`**（后者**带 GB**）。
   这两个名字之外的一切字体名——不论是否可商用、是否已安装、**是否只是反例**——**一律不得出现在本技能任何文件里**
   （`font=`、正文、表格、注释都算，门禁自动拦）。需要英文数字**照样写 `Noto Sans SC`**。
   漏掉 ` GB` 会静默回退；粗体用 `weight="BOLD"`。详见 `references/pitfalls.md`。
2. **🔒 版本锁定 Manim Community Edition 0.21.0**，勿升级、勿混用 3b1b 版。
   **三条路线开工前都跑** `scripts/check_manim_version.py`（校验版本号 + API 锚点）。
   **退出码非 0 就停下**，按脚本提示先修 `references/manim-api-troubleshooting.md` §三 实战校验记录 的结论。
3. **🔶 渲染一律 `run_in_background` + `dangerouslyDisableSandbox`**。工具调用一返回/超时，
   它派生的子进程会被一起 SIGTERM 杀掉 ⇒ 表现为 `Exit Code: 1 / SIGTERM` 而日志空。
   **这不是渲染失败，是调用先结束把 Manim 带走了。** 后台启动 → `TaskOutput` 阻塞等待
   （会收到完成通知），**不要 `sleep` 硬等**。
   ⚠️ **MCP 的 `render_animation` 走不到这条**：MCP 工具调用不支持后台参数，
   必须**先按 §三 预估耗时**（≥110 s 就别调 MCP），再选 `render_video.py`。
4. **卡住 30 秒后先取证据，不要干等**（复盘见 `references/incidents/mandelbulb-postmortem.md`）。
   判据：MCP 的临时工作目录（`<引擎仓库>/_render_tmp/manim_render_*/`）下**只有 `scene.py`、
   `media/` 目录里零个文件 ⇒ 不是慢，是跑不动**（实测正常渲染会往
   `media/videos/<模块>/<画质>/partial_movie_files/` 里持续写 `.mp4` 分段）。
   目录建了但一个文件都没有 = 场景还没进渲染阶段。
   **「慢」和「跑不动」是两件事。**
5. **抽帧自检必做（步骤 3），且不过 MCP**：`preview_scene` / `render_gif` 在 MCP 进程内跑
   subprocess，遇到删除钩子问题会把 MCP 一起带崩。**「代码逻辑看着对」不等于「画面对」**——
   双层 `LaggedStart` 不同步、RGB 插值变灰、卡片文字堆原点三类问题代码都不报错。
6. **排查代码错误绕过包装层**：MCP 与 `render_video.py` 的 `error_msg` 是**截断的 Rich 回溯尾部**，
   看不到真正报错行 ⇒ 绕过它们直跑 manim。**按阶段选工具**：构造/语法错误跑
   `scripts/probe_charts.py`（dry_run **不渲染像素**，秒级，适用于任何路线的场景文件）；
   渲染期问题（mobject 数量、LaTeX、像素级）跑 `manim render -ql`。
   **判性质看「日志里有没有 Traceback」，不要看耗时**——本机实测两者区间重叠：
   代码报错 1.9 s 退出，最简成功场景 2.5 s 完成，**耗时区分不出报错与成功**。
7. **点云一律用单个 `PMobject` + `add_points()`，禁用逐点 `Dot3D`——不设规模例外**。
   本机实测（1000 点）：构建 11.6 s vs 0.001 s（**约 1 万倍**）、出帧 31.1 s vs 0.008 s（约 3900 倍）；
   `Dot3D` 线性增长（11.6 ms/点），10 万点仅构建就需 ~19 min。它**磁盘上一个帧都没有**，
   易误判成「卡住」——这正是那次 20 万点空转的事故机制。数据见 `references/pitfalls.md`。
8. **只出画面，不做配音、不做 TTS。** 默认 720p / 16:9 / 无字幕 / `khan_academy`（白底）。
   风格只改**背景色**，前景颜色必须在场景代码里写死（白底下 `MathTex` 默认白色会看不见）。
9. **交付必须走完所在路线的全流程**（视频见 §四 标准流程，图表见
   `chart-generation.md` §一 标准流程，封面见 `wechat-cover.md` §三 渲染命令 → §七 自检清单），
   不得跳过自检直接说"做好了"。**必须用返回值的 `file_path`**，别猜文件名
   （重名会带 `_1`/`_2` 后缀）。
10. **📏 体量红线：`SKILL.md` 与每篇 `references/*.md` 都 ≤10000 字符，超了必须拆分**——
    **不调阈值**。拆分依据是**共享性**：**公共部分**（所有路线/任务都要用）留本文件，
    **非公共部分**（只属于某条路线或某个场景）留在各自文档，本文件只留一行指针。
   **唯一例外**：非公共但**漏读即静默返工**的内容（如 §五 真 3D场景 的专属要求）可留常驻层。
   新增内容先判断它是否公共、漏读是否会返工。完整判据见维护文档 §九 体量红线。
11. **本技能是活文档——只留正确的知识**：进文档须过五道门槛（G0~G4），证伪的删干净。
    **G0 硬证据 = 本次会话亲自跑过并看到输出**（定义见 `mcp-repo-rules.md` §一 取证门槛，
    删错门槛见维护文档 §三 删错门槛）。
12. **🔧 取证充分就直接改，不必请示**——卡住自进化的请示成本比改错更高。只有不可逆或会削弱
    安全网的动作才先问（删脚本 / 删 git tag / 改推送目标 / 绕门禁 / 改接口签名 / 换 remote /
    升级依赖）。判断口径：**能不能靠 git 回滚 + 门禁能不能拦住**。能 ⇒ 直接改。
    完整授权分级表见维护文档 §四 授权分级；改 MCP 侧仓库时的细化分级见
    `mcp-repo-rules.md` §二 可直接改 vs 必须报备。

## 三、成片渲染路径选择（仅用于步骤 4；预览见 §四 标准流程 步骤 2）

预览→成片（720p30 vs 480p15）**本机实测倍率约 ×1.3～1.7**，排期按 **×3 上限**估。
MCP `render_animation` 硬超时 **120 s** ⇒ 预估 < 110 s 才调 MCP；**≥ 110 s 或区间跨过 110 s
直接用 `scripts/render_video.py`**（同一套注入与风格管线，超时放宽到 900 s）。
MCP 工具调用**不支持后台参数**（硬约束 3 的 `run_in_background` 只对 Bash/PowerShell 有效），
所以这一步只能靠预估分流，没有「后台兜底」这个选项。

拿到非零退出码时**先分清两种情况再决定要不要重跑**：

| 现象 | 含义 | 动作 |
|---|---|---|
| `Exit Code: 1` + 日志里 `Traceback` | 场景代码真的报错了 | 取完整 traceback 改代码 |
| 非零退出码 + **日志里没有 Traceback** + `animation_output` 里有新文件 | 渲染完了，收尾清理撞上批量删除钩子 | **不要重跑**，按成功处理 |

## 四、标准流程（视频路线）

### 步骤 0：确认要讲什么
收集三件事：**讲哪个知识点/题目、受众年级、分几幕**。缺信息时最多问 1～3 个问题，
其余按默认静默决定：可汗学院白底风、高中生、每幕只讲一件事、总时长 30～50 s、结尾给小结卡片。

### 步骤 1：写场景代码
写到 **`<用户当前工作目录>/<ascii_name>_scene.py`**，类名必须 ASCII（渲染器靠 `class Xxx(Scene)`
正则取场景名）。从 `references/scene-template.md` 的最小可靠模板改，比从零写快且少踩坑。

### 步骤 2：480p 预览
```powershell
$P = "D:\software\uv\envs\py314-cpu\Scripts\python_direct.exe"
& $P "<技能目录>\scripts\render_video.py" <scene.py> `
  --quality low --style khan_academy --timeout 900
```
加 `run_in_background=true` + `dangerouslyDisableSandbox=true`。**3D 场景须先做完 §五 真 3D场景 的标定要求**。

### 步骤 3：抽帧自检（必做）
```powershell
& $P "<技能目录>\scripts\contact_sheet.py" <预览mp4> --auto --cols 3 --rows 5 --out sheet.png
& $P "<技能目录>\scripts\contact_sheet.py" <预览mp4> --start <尾段起始秒> --auto --cols 3 --rows 2 --out tail.png
```
`--auto` 自动算 every 保证覆盖全片（出现 `⚠️ 未覆盖全片` 就加大 `--rows`）；**结尾段落必须单独再看**
（闪白、收尾卡片最易漏检）。然后**亲眼看**拼图逐项核对：中文不是方框、文字在背景上可见、
元素不重叠/不出界/不压边缘（同一时刻画面上只应有一行标题）、图形数值与讲解一致、
每幕都有真实运动、渐变形变中颜色没掉进灰色。有问题 → 改代码 → 重跑步骤 2、3。

### 步骤 4：720p 出片
按 §三 成片渲染路径选择 选路径。MCP 参数 `code`/`quality="medium"`/`format="mp4"`/`style`；
降级脚本 `render_video.py <scene.py> --quality medium --style khan_academy`。

### 步骤 5：复检与交付
对成片再跑一次 `contact_sheet.py --auto`（真实时长与预览不同，逐帧位置会变），结尾同样单独复检；
`ffprobe` 核对分辨率/帧率/时长；复制到工作目录起中文名（如
`正弦函数的图像变换_可汗学院风_720p.mp4`）；`present_files` 交付（**mp4 第一、场景源码 .py 第二**）；
回复里说清时长、分辨率、每一幕讲了什么，以及**没配音**这一事实。

## 五、真 3D 场景（用户要「立体、相机环绕」时）

**不要用二维模板硬凑。** 完整可复制代码与六条硬性要求（标定场景、`fit_zoom` 反算、
形变中点纳入拟合、固定字幕、tracker 运镜、HSV 配色）在
**`references/scene-template-3d.md`（3D-1~3D-10）**，动手前先读。

> **为什么非公共的内容还留在本文件**：3D 专属，但**漏读代价高**——不知道要标定、
> 要反算 zoom 就会返工。这类「非公共但漏读即事故」的内容按例外留在常驻层，
> 其余非公共内容一律下沉（见硬约束 10）。**确实要下沉时，先确认漏读不会静默返工。**

## 六、本机固定事实（不要重新探测，除非报错）

| 项 | 值 |
|---|---|
| MCP 服务名 | `math-animation` |
| 渲染引擎 Python | `D:\software\uv\envs\py314-cpu\Scripts\python_direct.exe` |
| 引擎仓库 / 输出目录 | `D:\github\math-animation-mcp` / `animation_output`（**固定不可改**） |
| 默认中文字体 | `render_video.py` 启动器注入楷体（覆盖 `Text`/`MarkupText` 默认）；场景内显式写了 `FONT=` 的以场景为准。**封面固定用黑体**，见 `references/wechat-cover.md` §二 字体授权 |
| ffmpeg / ffprobe | `D:\software\ffmpeg\ffmpeg-2024-09-26-git-f43916e217-full_build\bin\` |
| LaTeX | MiKTeX：`D:\software\MiKTeX\miktex\bin\x64\`，**ctex 已装（v2.6.5）**。**走 MCP / `render_video.py` 时中文 `Title`/`Tex`/`MathTex` 可直接用**（MCP 已注入 `config.tex_template = TexTemplateLibrary.ctex`）；**直跑 `manim` / `probe_charts.py` 时必须自己写这一行**，否则报 `latex error converting to dvi` ⇒ 零产物。根因见 `references/pitfalls.md` |
| Manim 依赖（版本权威） | `D:\software\uv\envs\py314-cpu\Lib\site-packages\manim` |

**六种风格**（只改背景色，前景色仍须在代码里写死）：`khan_academy` 白`#FFFFFF`（**默认**，中小学/高中）、
`three_blue_one_brown` 深灰`#1C1C1C`（科普/大学）、`textbook` 浅灰`#F5F5F5`（教材）、
`playful` 暖黄`#FFF8E1`（小学低龄）、`dark_tech` 纯黑`#000000`（竞赛/CS/真 3D）、
`blackboard` 深绿`#2D5016`（模拟课堂）。

## 七、文档路由（按需读，别通读；⚠️ 标记的先 Grep 局部读）
| 文件 | 什么时候读 |
|---|---|
| **`references/自进化与维护.md`** | **改本技能前必读**。收录判据 / 硬证据定义 / 删错门槛 / 授权分级 / 版本号 / push-tag-回滚 / 体量红线 ⚠️ |
| **`references/mcp-repo-rules.md`** | 改 MCP 仓库（`D:\github\math-animation-mcp`）时。取证门槛 / 授权分级 / 回归自检 / 双边记账 |
| **`references/pitfalls.md`** | **排查具体问题时**。通用坑全集 + 排查流程 + 探针脚本 + 字体详解 ⚠️ |
| **`references/scene-template.md`** | 写**二维**场景代码时。最小可靠模板 + 配色常量 + 卡片布局 + 参数扫描 + 小结卡 |
| **`references/scene-template-3d.md`** | 写**真 3D**（`ThreeDScene`）场景时。3D-1~3D-10：反算 zoom、运镜、字幕、色带、HSV 配色、形变、白闪、标定场景 ⚠️ |
| **`references/chart-generation.md`** | **要任何图表/信息图时必读**。标准流程 + 三层安全区 + `charts_lib` + 各类图表实现要点（清单见其 §六 各类图表的关键实现要点） |
| **`references/chart-pitfalls.md`** | 图表路线踩过的坑（坑 1~15）。排查时按需查 |
| **`references/wechat-cover.md`** | **要封面/头图时必读**。尺寸规格、渲染命令、防裁切、封面专属坑、自检清单 |
| **`references/wechat-cover-layouts.md`** | 两套封面版式的可复制代码：左文右图 / 单卡居中（金句卡、要点卡） |
| **`references/manim-api-troubleshooting.md`** | **写拿不准的 API 之前**。30 秒自查法 + 本机源码位置 + 0.21.0 实测结论。**不要凭记忆写 Manim API** |
| **`references/incidents/mandelbulb-postmortem.md`** | 点云/分形场景前，或怀疑自己会"卡住干等"时。27 分钟空转事故链 |

> 体量红线见硬约束 10；各篇当前字符数与 ⚠️ 标记由 `node scripts/skill_audit.js --top`
> 现算，**文档里不写死数字**。

**脚本**

| 文件 | 用途 |
|---|---|
| `scripts/check_manim_version.py` | 开工前的版本守门 |
| `scripts/render_video.py` | 渲染视频。撞 MCP 超时或自检时用 |
| **`scripts/probe_charts.py`** | **图表/封面场景写完先跑它**（用法见硬约束 6）。不传类名则自动发现本文件所有场景 |
| **`scripts/check_chart_layout.py`** | **批量图表版面自检**。像素级检测压标题/溢出，阈值见 `references/chart-generation.md` §四 |
| **`scripts/charts_lib.py`** | **图表公共库**。`from charts_lib import *`，配色/坐标轴/卡片/图例/安全区全套 |
| **`scripts/render_cover.py`** | **渲染封面 PNG**。自动处理 `--resolution` 逗号格式、缓存假成功、字体回退检查 |
| `scripts/contact_sheet.py` | 视频抽帧拼图自检。**必须先跑它再看图**（静态 PNG 不需要） |
| `scripts/skill_audit.js` | 改本技能后的自进化门禁（断链/负向声明/字体/体量） |
| `push.js` | 提交推送 + 打回滚 tag：`node push.js "<说明>"` |
