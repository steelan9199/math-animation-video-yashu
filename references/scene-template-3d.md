# 三维场景模板（ThreeDScene / dark_tech 黑底）

以下每一段都来自一次真实交付（环面纽结，32.6 s / 720p / 30fps）的踩坑与修复，
不是伪代码，可直接复制使用。

> 二维模板（最小可靠模板、卡片布局、参数扫描、小结卡）在
> `references/scene-template.md`。**3D 不要套二维经验**——居中、运镜、配色插值
> 三件事在透视投影下规则完全不同。相关坑的速查表见 `references/pitfalls.md`「三维场景」。

## 3D-1 最小骨架与配色常量

```python
import numpy as np
import colorsys
from manim import *

# ⚠️ 版本锁定：Manim Community Edition 0.21.0，勿升级、勿混用 3b1b 版
# ⚠️ `from manim import *` **不导出** `CYAN` / `MAGENTA`，用了会 NameError。
#    但 `TEAL`/`PINK`/`GOLD`/`PURPLE`/`BLUE` 等**是**导出的。
#    结论：想要精确的霓虹色就自己定义十六进制常量，别赌名字是否存在。
BG        = "#000000"
C_CYAN    = "#22D3EE"   # 自定义霓虹青
C_MAG     = "#FF2E9A"   # 自定义霓虹品红
C_PUR     = "#8B5CF6"
C_YEL     = "#FFD60A"
C_WHT     = "#F4F7FB"
C_DIM     = "#8296B4"   # 页脚/次要文字，别调太暗，暗底上会看不清
FONT      = "Noto Sans SC"

FOCAL = 30.0   # 焦距越大越接近正交投影；透视感太强时调大
FILL  = 0.86   # 主体宽度占画面宽度的比例上限（fit_zoom 用）
SUB_Y = 3.15   # 固定字幕基线的 Y（top_text 用；别低于 -3.4，否则贴边）


class My3DScene(ThreeDScene):
    def construct(self):
        cam = self.camera
        cam.background_color = BG
        cam.set_focal_distance(FOCAL)
        cam.set_gamma(0.0)
        cam._frame_center.move_to(ORIGIN)   # 把主体摆在世界原点
```

## 3D-2 反算 zoom：让主体恒居中（3D 最大的坑）

`ThreeDScene` 用透视投影，**「包围盒中点」不等于画面中心**，
直接把物体摆到原点再设zoom，主体会明显偏出画面甚至斜着躺。

正确做法：用 `cam.project_points()` 拿到当前机位下的**真实投影范围**，再解 zoom。

```python
def fit_zoom(self, clouds, phi, th0, th1, half_h_cap, nsamp=21):
    """在 [th0, th1] 整段运镜区间内，取最坏情况反算 zoom。

    clouds: 要一起考虑的点列列表（形变动画要把中间态也塞进来）
    half_h_cap: 主体半高上限，用来给上下方字幕留白
    """
    cam = self.camera
    keep = (cam.get_phi(), cam.get_theta(), cam.get_gamma(), cam.get_zoom())
    cam.set_focal_distance(FOCAL)
    cam.set_gamma(0.0)
    cam.set_zoom(1.0)
    cam._frame_center.move_to(ORIGIN)

    ax = ay = 1e-9
    for th in np.linspace(th0, th1, nsamp):
        cam.set_phi(phi)
        cam.set_theta(float(th))
        for c in clouds:
            pr = cam.project_points(c.copy())
            ax = max(ax, float(np.abs(pr[:, 0]).max()))
            ay = max(ay, float(np.abs(pr[:, 1]).max()))

    cap_w = config.frame_width / 2 * FILL
    cap_h = min(config.frame_height / 2 * 0.95, half_h_cap)
    z = min(cap_w / ax, cap_h / ay)

    cam.set_phi(keep[0]); cam.set_theta(keep[1])
    cam.set_gamma(keep[2]); cam.set_zoom(keep[3])
    return z
```

**关键：拟合区间要按「这一幕实际会走到的机位」给，不要图省事拟合全角度。**
按全角度最坏情况拟合虽然不会出血，但主体会明显偏小（本次实测偏小约 25%）。

**形变动画要把中间态一起拟合**，否则形变过程中主体会冲出画面：

```python
fit4 = clouds + [lerp(clouds[0], clouds[1], 0.5),
                 lerp(clouds[1], clouds[2], 0.5),
                 lerp(clouds[0], clouds[2], 0.5)]
```

## 3D-3 运镜：机位与动画

```python
CAM_PHI = 68 * DEGREES        # 俯角，别用默认视角
THETA = {                     # 每一幕的方位角区间（真 3D 环绕）
    "a1": (-96 * DEGREES, -26 * DEGREES),
    "a2": (-26 * DEGREES,  16 * DEGREES),
}

def place(self, phi, th, fit_range, cap, clouds):
    """瞬时摆位，不产生动画。"""
    z = self.fit_zoom(clouds, phi, fit_range[0], fit_range[1], cap)
    self.camera.set_phi(phi); self.camera.set_theta(th); self.camera.set_zoom(z)
    return z

def dolly(self, phi, th_end, fit_range, cap, clouds, run_time=2.0):
    """运镜到新机位（带动画）。th_end 从 THETA[幕名][1] 取。"""
    z = self.fit_zoom(clouds, phi, fit_range[0], fit_range[1], cap)
    self.play(
        self.camera.phi_tracker.animate.set_value(phi),
        self.camera.theta_tracker.animate.set_value(th_end),
        self.camera.zoom_tracker.animate.set_value(z),
        run_time=run_time, rate_func=smooth,
    )
    return z
```

**两条全局tracker 在 `construct` 开头建一次**，3D-5 / 3D-7 / 3D-8 都要用：

```python
def construct(self):
    ...
    self.head_u = ValueTracker(0.0)   # 色带生长进度 0~1
    self.morph = ValueTracker(0.0)    # 形变进度 0~(len(clouds)-1)
```

3D-5 里的 `THETA_END` = `THETA["a1"][1]`，即这一幕运镜的终点方位角。

直接改 `cam.phi_tracker` / `theta_tracker` / `zoom_tracker` 的值来做动画，
比反复调`set_camera_orientation()` 更好控制。

## 3D-4 固定字幕：不跟相机翻转

3D 场景里所有文字**必须** `add_fixed_in_frame_mobjects()`，
否则会随相机倾斜变形、甚至翻到背面去。

```python
def top_text(self, text, color=C_WHT, size=30):
    t = Text(text, font=FONT, font_size=size, color=color)
    t.move_to(ORIGIN + UP * SUB_Y)
    self.add_fixed_in_frame_mobjects(t)
    return t
```

用完记得 `remove_fixed_in_frame_mobjects()`，否则该mobject 会永远被钉在画面里。

- 字幕放**画面中下方居中**，字号 ≤ 28；横排太长会贴到右边缘被裁掉。
- 上下都留白：主体半高上限设成 2.6 左右，字幕基线在 ±3.4。
- 同一时刻画面上只留一行字。新标题要先`FadeOut` 旧标题再 `FadeIn` 新字幕，
  否则两行字会叠在一起（本次踩过）。

## 3D-5 色带渐变 + 双层辉光

一条曲线拆成若干「色带」，每段是独立的 `VMobject`。
色带同时承担渐变、生长动画、形变三件事，比反复替换整条曲线省事得多。

```python
N_PTS = 240# 采样点数
N_BAND = 12         # 色带数
CORE_W = 2.4# 亮线宽
GLOW_LAYERS = ((15.0, 0.10), (7.0, 0.30))   # 辉光：(线宽, 透明度)

@staticmethod
def band_slices(n_band=N_BAND, n_pts=N_PTS):
    """把闭合曲线切成首尾相接的索引区间（末段绕回起点闭合）。"""
    edges = np.linspace(0, n_pts, n_band + 1).astype(int)
    edges[-1] = n_pts - 1          # ⚠️ 不加这行，最后一段会越界IndexError
    out = []
    for i in range(n_band):
        if i < n_band - 1:
            out.append(np.arange(edges[i], edges[i + 1] + 1))
        else:
            out.append(np.concatenate([np.arange(edges[i], n_pts), [0]]))
    return out
```

生长动画**必须让辉光层和亮线层同步**。
用两个独立 `LaggedStart` 分别控制两层，节奏对不上，轨迹会画成**虚线**：

```python
nlay = len(GLOW_LAYERS)
grow = []
for i in range(N_BAND):
    for li in range(nlay):
        grow.append(FadeIn(glows[i * nlay + li]))
    grow.append(Create(cores[i]))
self.play(
    LaggedStart(*grow, lag_ratio=(1.0 / N_BAND) * 0.55),
    self.head_u.animate.set_value(1.0),
    cam.theta_tracker.animate.set_value(THETA_END),
    run_time=3.8, rate_func=linear,
)
```

## 3D-6 配色插值：用色相旋转，千万别用 RGB 线性插值

两套配色之间过渡时，**RGB 线性插值走到中途必然掉进灰**。
实测：RGB 插值彩度最低掉到 **0.083**（肉眼就是一条灰带），
改成 HSV 旋转色相后全程稳定在 **0.82** 以上。

```python
def _hex2hsv(h):
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return colorsys.rgb_to_hsv(r, g, b)

def _hsv2manim(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, min(max(s, 0.0), 1.0),
                                min(max(v, 0.0), 1.0))
    return ManimColor((r, g, b, 1.0))

PAL_A = ("#22D3EE", "#FF2E9A")   # 沿曲线的渐变端点色
HUE_SHIFT = 60                   # 形变终点相对起点的色相偏移（度）

def band_color(frac, g):
    """frac: 沿曲线的位置 0~1；g: 形变进度 0~1。"""
    a, b = _hex2hsv(PAL_A[0]), _hex2hsv(PAL_A[1])
    h = a[0] + (b[0] - a[0]) * frac + (HUE_SHIFT / 360.0) * g
    s = a[1] + (b[1] - a[1]) * frac
    v = a[2] + (b[2] - a[2]) * frac
    return _hsv2manim(h, s, v)
```

## 3D-7 形变：在多组曲线之间插值

```python
def lerp(a, b, f):
    return a * (1.0 - f) + b * f

def attach_morph(self, cores, glows, slices, clouds, tracker):
    """tracker 范围 0~(len(clouds)-1)，整数部分切组、小数部分组内插值。"""
    n = len(clouds)
    denom = max(n - 1, 1)
    last = max(len(slices) - 1, 1)

    def make(sl, frac, mob, width, opacity):
        def upd(m, dt):
            s = float(tracker.get_value())
            k = int(np.clip(s, 0, n - 2))
            f = float(np.clip(s - k, 0.0, 1.0))
            g = float(np.clip(s / denom, 0.0, 1.0))
            a, b = clouds[k], clouds[k + 1]
            m.set_points_smoothly(lerp(a[sl], b[sl], f))
            m.set_stroke(band_color(frac, g), width=width, opacity=opacity)
        return upd

    for i, mob in enumerate(cores):
        mob.add_updater(make(slices[i], i / last, mob, CORE_W, 1.0))
    for i in range(len(slices)):
        for li, (w, o) in enumerate(GLOW_LAYERS):
            glows[i * len(GLOW_LAYERS) + li].add_updater(
                make(slices[i], i / last, glows[i * len(GLOW_LAYERS) + li], w, o))
```

形变结束要收尾：`for m in cores + glows: m.clear_updaters()` 再 `self.remove(...)`，
否则 updater 会继续在已移除对象上跑。

## 3D-8 光点跟随

```python
def follow(m, dt):
    u = float(np.clip(self.head_u.get_value(), 0.0, 0.99999))
    s = float(np.clip(self.morph.get_value(), 0.0, len(clouds) - 1.0001))
    k = int(s); f = s - k
    j = int(u * (len(clouds[0]) - 1))
    m.move_to(lerp(clouds[k][j], clouds[k + 1][j], f))

head = Sphere(radius=0.085, resolution=(10, 10))
head.set_fill(C_CYAN, opacity=1.0).set_stroke(C_WHT, width=1.2)
halo = Dot3D(radius=0.34, color=C_CYAN)
halo.set_fill(opacity=0.14).set_stroke(C_CYAN, width=1.0, opacity=0.45)
head.add_updater(follow); halo.add_updater(follow)
```

⚠️ **不要用 `self.time_since_start`**——`Scene` 没有这个属性，写了必崩（已实测 `AttributeError`）。
两种正确写法（`ValueTracker` 优先 / 读 `self.time` 做连续运动）、
以及「写『某 API 不存在』前必须先 `hasattr` 验一遍」这条纪律，见
`references/manim-api-troubleshooting.md` §3.2 `Scene` 的时间属性。

## 3D-9 收尾：白闪穿越

```python
flash = Rectangle(width=config.frame_width + 1,
                  height=config.frame_height + 1)
flash.set_fill(C_WHT, opacity=0.0).set_stroke(width=0)
self.add_fixed_in_frame_mobjects(flash)
self.play(cam.zoom_tracker.animate.set_value(z * 5.4),
          run_time=1.5, rate_func=rate_functions.ease_in_cubic)
self.play(flash.animate.set_fill(opacity=1.0), run_time=0.35)
self.remove(flash)
self.remove_fixed_in_frame_mobjects(flash)
```

## 3D-10 写3D 场景前，先渲染一个标定场景

**这一步不要省。** 「包围盒中点≠ 画面中心」这件事靠推理判断不了严重程度，
必须用一次 20 秒的廉价渲染把算法验证掉。

标定场景：把一条 3D 曲线摆正，用3D-2 的 `fit_zoom` 配好 zoom，
在画面正中放一个 `add_fixed_in_frame_mobjects` 的十字。
渲染后看十字是否被曲线稳稳穿过——穿过= 算法正确，后面才敢往下写。

```python
cross = VGroup(Line(LEFT * 0.35, RIGHT * 0.35, stroke_width=2),
               Line(UP * 0.35, DOWN * 0.35, stroke_width=2)).set_color(C_WHT)
self.add_fixed_in_frame_mobjects(cross)
```

## 3D 性能参考（Manim 0.21，本机）

单次操作耗时实测表见 `references/manim-api-troubleshooting.md` §3.5 性能实测。

- 每帧的 `always_redraw` / `add_updater` 对象控制在 2～3 个。
- 需要 updater 的色带**放在场景顶层**（不要塞进 `VGroup` 里当子对象），
  否则 `self.remove(g)` 和 `clear_updaters()` 容易漏。
- 实测 32.6 s / 720p / 30fps 的 3D 场景，480p 预览 ~25 s，成片 ~41 s（**倍率约 ×1.6**）。

