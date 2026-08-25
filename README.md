# poetic-collage-grid-jl-paper

`poetic-collage-grid-jl-paper-latest` 是一个将单张照片转换为 3:4 竖版诗意双联画的图像处理 Skill。

它使用真实的原图像素、程序化电影调色、纸张纹理、打字机油墨与纤维撕边算法，生成一张具有当代编辑感和实体印刷触感的完整 PNG。

> Gather Edition · Deterministic Image Post-processing

## 效果参考

| Rawr | Quiet |
| :---: | :---: |
| <img width="1536" height="2048" alt="Codex 图像 2026年8月25日 18_41_45" src="https://github.com/user-attachments/assets/959b3e12-6777-4c1a-b0c9-047c62dc2cfb" />|<img width="1536" height="2048" alt="Codex 图像 2026年8月24日 18_57_12" src="https://github.com/user-attachments/assets/6a441804-bd27-4f4a-99af-0119ebb85d2b" />|

## 效果结构

最终作品采用固定的上下二宫格：

- 画布比例：`3:4`
- 默认尺寸：`1536 × 2048 px`
- 上宫格：低饱和 Morandi 纸张、英文诗句与原图碎片
- 下宫格：等比例铺满的原始照片
- 上下比例：严格 `50% / 50%`
- 输出格式：单张 PNG

下宫格不会被拉伸。原图将通过 `cover` 方式进行等比例裁切并铺满整个区域。

## 核心特性

### 真实原图碎片

诗句中的图片片段直接提取自处理后的下宫格照片，不重绘、不扩图，也不生成虚构内容。

### 一一对应的白色缺口

每个上方碎片都对应下方照片中的一个白色缺口：

- 位置来源一致
- 显示尺寸一致
- 长宽比例一致
- 撕纸蒙版一致

### 程序化电影后期

下宫格会经过克制的电影感处理：

- 轻微降低饱和度
- 柔和高光肩部
- 保留暗部细节
- 轻微冷阴影与暖高光
- 柔和边缘渐晕
- 细微单色胶片颗粒

这是像素级后处理，不依赖生成式图像模型重新绘制照片。

### Morandi 纸张背景

上宫格颜色根据原图自动提取，并转换为明亮、低饱和的 Morandi 色。

纸张表面包含：

- 轻微明度颗粒
- 稀疏纤维
- 克制的实体纸张触感
- 不泛黄、不做旧、不添加复古污渍

### 真实打字机墨迹模拟

英文诗句采用机械打字机字体骨架，并逐字符加入：

- 墨色压力差异
- 轻微基线偏移
- 水平套印偏差
- 墨水扩散
- 少量漏墨点
- 字符边缘积墨

字体保持清晰，不会变成夸张的破损字体或拼贴字体。

### 纤维撕纸边缘

图片碎片、白色缺口和上下分界线使用同一套程序化撕纸逻辑：

- 低频撕裂轮廓
- 微小不规则缺口
- 半透明纤维边缘
- 确定性的随机种子

整体仍接近矩形，不使用夸张、厚重或装饰性的撕纸效果。

## 工作流程

```text
输入照片
   ↓
等比例 Cover 裁切
   ↓
电影感像素后期
   ↓
提取原图片段
   ↓
生成匹配的撕纸蒙版和白色缺口
   ↓
生成 Morandi 纸张背景
   ↓
排版英文诗句与图片片段
   ↓
渲染打字机油墨
   ↓
合成并输出单张 PNG
```

每次渲染都会生成一张完整作品，不需要分别生成上下宫格再手工拼接。

## 环境要求

- Python 3.10 或更高版本
- Pillow

安装依赖：

```bash
python3 -m pip install Pillow
```

## 快速开始

```bash
python3 scripts/render_diptych.py \
  --image /absolute/path/to/source.png \
  --spec /absolute/path/to/spec.json \
  --output /absolute/path/to/final.png
```

## 配置示例

```json
{
  "canvas": [1536, 2048],
  "split": 0.5,
  "fit": "cover",
  "focus": [0.5, 0.5],
  "film_look": {
    "enabled": true,
    "strength": 0.54,
    "grain": 0.018,
    "seed": 311
  },
  "paper_texture": {
    "enabled": true,
    "strength": 0.12,
    "fiber": 0.08,
    "seed": 83
  },
  "print_style": {
    "enabled": true,
    "ink_variation": 0.18,
    "registration_shift": 0.55,
    "baseline_jitter": 0.65,
    "ink_spread": 0.14,
    "seed": 97
  },
  "torn_edges": {
    "enabled": true,
    "roughness": 0.18,
    "split_roughness": 0.14,
    "fiber": 0.22,
    "seed": 109
  },
  "poem": [
    {"text": "On her knees, "},
    {"crop": "page"},
    {"text": " holds another gaze; "},
    {"crop": "earbud"},
    {"text": " listens as "},
    {"crop": "cable"},
    {"text": " gathers one small "},
    {"crop": "shore"},
    {"text": " from the shore."}
  ],
  "crops": [
    {"id": "page", "box": [0.425, 0.300, 0.075, 0.060]},
    {"id": "earbud", "box": [0.240, 0.785, 0.065, 0.075]},
    {"id": "cable", "box": [0.330, 0.535, 0.070, 0.100]},
    {"id": "shore", "box": [0.795, 0.325, 0.040, 0.055]}
  ]
}
```

所有裁片坐标均使用原图归一化坐标：

```text
[x, y, width, height]
```

数值范围为 `0–1`。

## 主要参数

| 参数 | 说明 | 建议范围 |
|---|---|---:|
| `focus` | 下宫格裁切中心 | `0–1` |
| `film_look.strength` | 电影调色强度 | `0.45–0.88` |
| `film_look.grain` | 单色胶片颗粒 | `0.02–0.04` |
| `paper_texture.strength` | 纸张明度纹理 | `0.08–0.18` |
| `paper_texture.fiber` | 纸面纤维密度 | `0.04–0.12` |
| `ink_variation` | 打字机墨色变化 | `0–0.40` |
| `registration_shift` | 字符套印偏移 | `0–1.5 px` |
| `baseline_jitter` | 字符基线变化 | `0–1.5 px` |
| `ink_spread` | 墨水扩散程度 | `0–0.35` |
| `roughness` | 碎片撕边强度 | `0–0.60` |
| `split_roughness` | 中间分界撕边强度 | `0–0.50` |
| `torn_edges.fiber` | 撕边纤维强度 | `0–0.60` |

## 诗句规范

默认输出一条英文诗句：

- 建议长度：12–24 个单词
- 排版行数：1–3 行
- 默认字体大小：36 px
- 整体水平、垂直居中
- 图片片段作为诗句中的视觉名词
- 不使用标题、署名、日期或励志口号

诗句应来自照片中真实存在的动作、材质、时间和空间关系，而不是套用通用文案。

## 可复现性

电影颗粒、纸张纹理、打字机墨迹和撕纸边缘都支持独立的随机种子。

在以下内容保持不变时，可以稳定复现相同结果：

- 输入照片
- JSON 参数
- 裁片坐标
- 字体文件
- Pillow 版本
- 随机种子

## 隐私与图像完整性

- 不上传或替换原图内容
- 不进行面部美化
- 不重绘人物或环境
- 不使用生成模型补充画面
- 不复制参考图片中的专有字体
- 处理可在本地完成

## 项目结构

```text
poetic-collage-grid-jl-paper/
├── README.md
├── SKILL.md
├── scripts/
│   └── render_diptych.py
└── references/
    ├── poetry-and-crops.md
    ├── film-look.md
    ├── paper-print-direction.md
    └── render-spec.md
```

## 已知限制

- 横图和竖图都需要经过固定 `3:2` 下宫格视口裁切。
- 裁片必须位于最终可见区域内。
- 当前纸张、胶片和油墨均为算法模拟，并非真实材料扫描。
- 英文打字机排版效果最佳。
- 自动生成的诗句和取样坐标仍建议经过一次视觉检查。

## License

发布前请根据项目用途选择并补充许可证，同时确认示例图片、字体及相关素材拥有合法使用权限。
