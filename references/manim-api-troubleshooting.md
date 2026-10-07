# Manim API 查证与踩坑记录（math-animation-video 专用）

> **版本锁定：Manim Community Edition 0.21.0**（版本固定，勿升级）
> 本文件记录「怎么查 API」的方法，以及一次真实交付（环面纽结三维动画）
> 中实际校验过的 API 论断。**所有结论都经过本机实测，不是抄文档。**

---

## 零、版本规则（先读这一节）

### 0.1 只认社区版 0.21.0

| 项目 | 值 |
|---|---|
| 发行版 | **Manim Community Edition**（`Author: The Manim Community Developers`） |
| 版本 | **0.21.0**（社区仓库 `main` 分支当前即此版本） |

**不要**混用 3b1b 版（`/3b1b/manim` 是**另一个项目**）或 ManimGL。

---

## 一、为什么要写这份文件

Manim 的 API 迭代很快，而本机**锁定 0.21.0**。凭记忆写代码是本技能最大的风险来源——
真实交付里最贵的两类失败都是 API 层面的：**用了不存在的常量名**
（见 §3.1 `from manim import *` 到底导出了什么颜色常量）与
**写了不存在的属性**（见 §3.2 `Scene` 的时间属性），两者都是 `NameError` / `AttributeError`，
代码逻辑看着完全正确，渲染启动才炸。

这份文件的作用是：**把「猜 API」变成「查 API」，并给出查的顺序。**

---

## 二、30 秒自查法（比翻文档快）

**不确定某个名字是否存在时，直接跑一行 Python**，比查任何文档都快且准。

```powershell
# 1. 某个常量/类是否存在
& "D:\software\uv\envs\py314-cpu\Scripts\python_direct.exe" -c "import manim; print([n for n in dir(manim) if 'CYAN' in n])"

# 2. 某个类有没有某个属性
& "D:\software\uv\envs\py314-cpu\Scripts\python_direct.exe" -c "from manim import Scene; print(hasattr(Scene,'time'))"

# 3. 某个函数的准确签名
& "D:\software\uv\envs\py314-cpu\Scripts\python_direct.exe" -c "import inspect; from manim import interpolate_color; print(inspect.signature(interpolate_color))"

# 4. 某个方法属于哪个类（定位源码文件）
& "D:\software\uv\envs\py314-cpu\Scripts\python_direct.exe" -c "from manim import ThreeDScene; print(ThreeDScene.move_camera.__module__)"

# 5. 一次性校验版本 + 全部锚点（推荐）
& "D:\software\uv\envs\py314-cpu\Scripts\python_direct.exe" "<本技能目录>/scripts/check_manim_version.py"
```

### 读本机源码定位具体实现

```
Grep(pattern="def set_camera_orientation", path="D:\software\uv\envs\py314-cpu\Lib\site-packages\manim")
Read(file_path="D:\software\uv\envs\py314-cpu\Lib\site-packages\manim\scene\three_d_scene.py")
```

常用源码位置：

| 想查什么 | 去哪看 |
|---|---|
| 3D 相机、运镜 | `manim\scene\three_d_scene.py` |
| 3D 相机投影数学 | `manim\camera\three_d_camera.py` |
| 2D 相机基类 | `manim\camera\camera.py` |
| 颜色工具 | `manim\utils\color\core.py` |
| Text/MathTex | `manim\mobject\text\text_mobject.py`、`tex_mobject.py` |
| ValueTracker | `manim\mobject\value_tracker.py` |
| 命名空间导出清单 | `manim\__init__.py` |
| 版本与来源（METADATA） | `site-packages\manim-0.21.0.dist-info\METADATA` |

---

## 三、实战校验记录（0.21.0 实测，非文档摘抄）

以下每条都跑过验证，且由 `scripts/check_manim_version.py` **持续守护**
（它每次开工都会重跑这批断言，漂移即退出码 1）。**别再重复踩。**

### 3.1 `from manim import *` 到底导出了什么颜色常量

**实测结论**：`manim` 顶层命名空间有 150+ 个大写常量（`check_manim_version.py` 守的是**量级** `>=150`，
不是某个具体数字——常量总数会随版本增删漂移，守死数字只会制造假告警），其中：

| 存在 | 不存在 |
|---|---|
| `BLUE` `RED` `GREEN` `YELLOW` `ORANGE` `PURPLE` `TEAL` `PINK` `GOLD` `WHITE` `BLACK` `GREY` `GRAY` `MAROON` | **`CYAN`** **`MAGENTA`** |

同时存在 `PURE_CYAN`（`#00FFFF`）、`PURE_MAGENTA`（`#FF00FF`）、
以及全套 `_A`~`_E` 变体（`BLUE_A`…`TEAL_E`）。

> **做法**：想要精确的霓虹色（如 `#22D3EE`）**一律自己定义十六进制常量**，
> 不要赌 Manim 有没有这个名字——写错常量名是 `NameError`，不报错才奇怪。

### 3.2 `Scene` 的时间属性

| 论断 | 实测结果 |
|---|---|
| `Scene.time_since_start` | ❌ **不存在**，用了必报 `AttributeError` |
| `Scene.time` | ✅ **存在**，`float`，随 `play`/`wait` 推进 |

实测输出：`self.time` 初值 `0.0`，`self.wait(0.3)` 后为 `0.3`。

写法 A（推荐）：`ValueTracker`，时间轴完全可控、可从 0 重新开始

```python
head_u = ValueTracker(0.0)
self.play(head_u.animate.set_value(1.0), run_time=3.0)
```

写法 B：读 `self.time`，适合连续循环运动

```python
def follow(m, dt):
    m.move_to(curve[int((self.time * 0.35 % 1.0) * (N - 1))])
```

⚠️ `self.time` 是**场景累计时间、不会重置**。多幕复用同一逻辑时注意相位；
需要「从 0 开始的进度」时用写法 A。

> **纪律：写「某 API 不存在」这种断言前，必须先 `hasattr` 验一遍。**
> 本节两条结论都由 `scripts/check_manim_version.py` 持续守护。

### 3.3 3D 相关 API

```python
ThreeDScene.set_camera_orientation(phi=75*DEGREES, theta=30*DEGREES)
ThreeDScene.move_camera(phi=..., theta=..., zoom=..., frame_center=...)
ThreeDScene.add_fixed_in_frame_mobjects(text3d)   # 官方示例 FixedInFrameMobjectTest
ThreeDScene.remove_fixed_in_frame_mobjects(text3d)
ThreeDScene.begin_ambient_camera_rotation(rate=0.1)
ThreeDScene.stop_ambient_camera_rotation()
```

**相机投影的真实数学**（`manim\camera\three_d_camera.py`，反算 zoom 时要用）：

```python
points = points - frame_center                   # 先平移到 frame_center
points = points @ rotation_matrix.T              # 按 phi/theta 旋转
factor = focal_distance / (focal_distance - z)   # 透视除法
points[:, 0] *= factor * zoom
points[:, 1] *= factor * zoom
```

所以 `focal_distance` 越大越接近正交投影（本次用 30.0）。
**这就是为什么「把物体摆到原点 + 设 zoom」不能保证画面居中**——
必须用 `cam.project_points()` 反算，见 `scene-template-3d.md` 的 3D-2。

### 3.4 颜色工具

| 项 | 结论 |
|---|---|
| `interpolate_color(color1, color2, alpha)` | 返回 `ManimColor`；第三个参数是 `alpha`（**不是** `f`） |
| `ManimColor("#22D3EE")` | 构造接受十六进制字符串，直接返回 `ManimColor` |
| 与 `set_stroke()` 配合 | `interpolate_color` 的返回值可直接喂给 `set_stroke()` |

### 3.5 性能实测（本机 0.21.0 复现）

| 操作 | 单次耗时 | 备注 |
|---|---|---|
| `VMobject().set_points_smoothly(300 点)` | ≈ 4.7 ms | 优美好看，但贵 |
| `VMobject().set_points_smoothly(600 点)` | ≈ 9.3 ms | 点数翻倍，耗时翻倍 |
| `VMobject().set_points_as_corners(450 点)` | ≈ **0.08 ms** | 便宜两个数量级 |
| `Sphere(resolution=(6,6))` | ≈ 6.1 ms | 3D 小球别每帧新建 |

> **实践建议**：需要 updater 的对象**数量控制在 2～3 个**。
> 若要每帧更新大量点，优先用 `set_points_as_corners`（便宜 100 倍），
> 或把点云预处理好只更新少量顶点。

---

## 四、相关文件

- `SKILL.md` 硬约束 2 —— 版本与锚点守门（速查版）
- `scripts/check_manim_version.py` —— **版本 + API 锚点校验**，锚点漂移即退出码 1
- `references/scene-template.md` —— **二维**模板（最小可靠模板、卡片布局、参数扫描）
- `references/scene-template-3d.md` —— **真 3D 场景模板**（3D-1~3D-10，含 `fit_zoom` 反算实现）
- `references/pitfalls.md` —— 通用坑全集（配色 / 字体 / 动画机制 / 三维 / 构造类写法）
- `references/chart-generation.md` —— 图表路线的**做法与清单** + `charts_lib.py` 公共库
- `references/chart-pitfalls.md` —— 图表路线的**坑**
- `references/wechat-cover.md` / `wechat-cover-layouts.md` —— 公众号封面路线（尺寸、版式、字体授权）
- `references/incidents/mandelbulb-postmortem.md` —— 空转事故复盘
