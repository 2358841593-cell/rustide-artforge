# 出图提示词配方 v2

> ⚠️ **v1 实测失败，已整体重写。** 失败原因见 §0——那不是"忘了写什么"，是**写法本身**不对。
> 本文件按**图像模型的脾气**写，不按规格文档的脾气写。

---

## 0 · v1 为什么失败（必读，否则会重蹈覆辙）

v1 生成的提示词把所有规格都写全了——`1:5 ratio`、`WARM DARK BROWN #2E241F, NEVER pure black`、
`exactly ONE hard-edged cel shadow`、`no gradients`——**模型一条都没执行**。六个原因：

| # | 错误 | 后果 | 修法 |
|---|---|---|---|
| 1 | **提示词 ~900 词** | 图像模型前 ~100 token 权重最高，风格指令被稀释到失效 | **上限 280 词，且风格段须占 ≥45%** |
| 2 | **首句含 `anime`** | "anime character design sheet" 先验极强 = 1:7 身材 + 亮晶大眼 + 细黑线，坐在最高权重位碾压后文 | **禁用 `anime` 一词**，改 `1990s hand-inked cel animation model sheet` |
| 3 | **大量否定式**（`NEVER pure black` / `no gradients` / 末尾 100 词 `Avoid...`） | 多数现代生图模型**没有 negative 通道**；否定词在正面提示词里≈把该概念念了一遍。`NEVER pure black` 反而画出黑线 | **全部改成正面陈述**，见 §3 转换表 |
| 4 | **比例写成数字** `1:5 head-to-body ratio` | 模型不算比例，等于没说 | 用描述词：`big head, short body, five heads tall` |
| 5 | **参考图选了 `08-alva`** | 阿尔瓦是全组最瘦、最接近普通日漫比例的一个，拿它当比例锚 = 教反了 | 比例锚固定用 `27-cast-lineup` + `06-john` |
| 6 | **照片被授予 `build` / `posture` 所有权** | 模型照真人解剖画 = 写实比例，直接打赢 1:5 | 照片**只拥有**发型的形、遮挡物、1–2 个夸张五官；**身体一律来自参考图** |

> **一句话教训：图像提示词不是规格文档。规格文档追求完备，图像提示词追求前置、简短、正面。**

---

## 1 · 七段式主模板（≤280 词，风格段 ≥45%）

顺序不可改。**风格和比例必须在角色之前**——这是 v1 最致命的错误。

```
S1  风格锚      ← 最高权重位，定画种
S2  比例锚 + LINE ← 第二权重位，定形体和线质（用描述词）
S3a PHOTO-LOCK ← 锁死生理域：只放大照片里已有的五官/脸型/胖瘦，不得新增
S3b 肤色        ← 单独成段，必带 HEX，叫 pale pink-beige
S4  角色一句话
S5  脸 + 夸张点
S6  服装（照片改造版）+ DETAIL 细节密度
S7  上墨与填色 + 配色  ← 全正面陈述，暖色主导、不写降饱和词
```

### 英文主模板（复制即用）

```
A 1990s hand-inked cel animation model sheet. Single character, full body, front view,
plain white background, empty field.

BUILD: big head, short body, five heads tall. A thick padded jacket with wide square shoulders
is the widest part. Very thin simple straight legs. Huge heavy square
boots. Brush-like line weight, very thick at the silhouette
and thin inside; torn jagged hems; the jacket flares out well past the hips.

PHOTO-LOCK: from the photo the face and body keep only these traits, amplified —
{体型档位}, {脸型}, {眼型}, {眉}, {鼻}, {肤色档位}. The face and body carry these traits and
these alone. Costume, props and hair styling stay free to exaggerate.

SKIN: pale pink-beige #{skin_hex} with one shadow #{skin_shadow_hex}. The skin stays pale.

WHO: {一句话：年龄 + 职业 + 出身 + 性格}.

FACE: small simplified graphic face, features grouped low on the head. Eyes are two solid dark
oval shapes. Mouth is one short line. Two small hard-edged oval blush patches. Thick short
eyebrows. {遮挡物：heavy fringe covering the eyes / round glasses / a full beard / goggles}.
{夸张点 1}. {夸张点 2}.

CLOTHES (a scavenged version of what the photo wears): {内层}, {中层}, {外层}.

DETAIL: at least fifteen small mismatched details — round badges and pins of different sizes in
clashing colours, tape strips, patches of different shapes, visible stitching, torn holes,
hanging cloth strips, buckles. Nothing is tidy or matched. Printed "{n}" on the chest. {道具}.

INK AND FILL: every outline is warm dark brown {line_hex}. Outlines are thick, rounded and
hand-drawn, and the outer silhouette line is the thickest. Every colour is one flat matte fill
with a single hard-edged shadow shape in a slightly cooler tone. The clothing colours are
warm and sun-bleached, saturated but worn: {accent_hex} jacket, {neutral_a_hex} and
{neutral_b_hex} for most of the figure, a small {surprise_hex} accent. Warm colours dominate.
Light from upper left.
```

### 两条硬指标（填完必须实测）

| 指标 | 阈值 | 为什么 |
|---|---|---|
| **总词数** | ≤ 280 | 再长风格指令就被稀释。LINE / DETAIL 成为必需段后，250 撑不住 |
| **风格段占比** `(S1+S2+S7) / 总词数` | **≥ 45%** | 真正起作用的机制不是绝对词数，是**风格词压过内容词**。S1/S2/S6 是风格段 |

超标时**只砍 S4 / S6 的形容词**，S1、S2、S3、S7 一个字都不能动。

> 💡 S6 里不要重复写颜色名（`deep-teal work shirt`）——S6 已经给了 HEX。
> 双重指定会打架，而且白白吃掉词数配额。

---

## 2 · 参考图（比文字更重要）

**必须附两张，角色固定，不要临时挑。**

| 槽位 | 用哪张 | 教什么 |
|---|---|---|
| **比例锚** | `27-opening-cast-lineup.png` | 上重下轻、大头细腿大靴、全组比例语言 |
| **上墨锚** | `06-john-early-portrait.png` | 暖褐色线、平涂、单层硬影、磨损画法 |

按角色类型可替换**上墨锚**（比例锚永远不换）：

| 角色 | 上墨锚换成 |
|---|---|
| 儿童 | `07-sam-early-portrait.png` |
| 老人 / 市井 | `13-hoffman-early-portrait.png` |
| 机械 / 非人 | `11-daniel-early-portrait.png` |
| 挂满装备的工作者 | `12-william-early-portrait.png` |

> ❌ **不要用 `08-alva`（阿尔瓦）当比例锚。** 他是全组最瘦、最接近普通日漫比例的一个，v1 就栽在这里。

### 参考图指令（正面写，短）

```
Copy the body proportions, outline weight and flat colour treatment of the reference sheets.
Same drawing system, different person.
```

> ❌ **绝对不要写长串 `Do not copy Image 2's identity / face / hair / costume / pose...`**
> v1 就是这么写的，结果模型什么都没拿。**一句 `Same drawing system, different person.` 足够了。**

---

## 3 · 否定 → 正面 转换表（核心修复）

**除非模型有真正的 negative 通道（SD / Flux / MJ 的 `--no`），否则一个否定词都不要写。**

| ❌ 否定式（v1，会反噬） | ✅ 正面式（v2） |
|---|---|
| `NEVER pure black outlines` | `every outline is warm dark brown #2E241F` |
| `no gradients, no soft shading` | `every colour is one flat matte fill` |
| `no airbrush, no texture, no grain` | `clean paper-like flat colour` |
| `not chibi, not realistic` | `five heads tall` |
| `no glossy anime eyes` | `eyes are two solid dark oval shapes` |
| `no detailed nose` | `minimal nose, one small mark` |
| `no background scenery` | `plain white background` |
| `no drop shadow` | `figure sits directly on white` |
| `no separate fingers` | `hands are simple mitten shapes`（**可选**，官方仅 3–4/8 这么画，别当硬要求） |
| `no individual hair strands` | `hair is a few solid pointed lobes` |
| `dusty / muted / desaturated` | `warm and sun-bleached, saturated but worn`（实测参考图平均饱和 0.60） |
| `no modern tech` | *（不写。技术水位靠 S5 正面列举实际穿戴来保证）* |

---

## 4 · 各模型的负面提示词策略

| 模型 | 有 negative 通道？ | 怎么做 |
|---|---|---|
| **GPT-Image / Codex 生图 / Nano Banana** | ❌ 无 | **一个否定词都不写**。全用 §3 正面式 |
| **Midjourney** | ✅ `--no` | 主提示词全正面；否定项放 `--no` 参数 |
| **Stable Diffusion / Flux / ComfyUI** | ✅ 独立 negative 字段 | 主提示词全正面；否定项放 negative 字段 |

### 仅供有 negative 通道的模型使用

```
black outline, gradient, soft shading, airbrush, glossy eyes, realistic proportions,
long legs, thin body, detailed face, 3d render, painterly, texture, grain, halftone,
glow, bloom, background, drop shadow, watermark, text
```

> 保持**短**。v1 那种 100 词负面清单即使在支持的模型上也会互相稀释。

---

## 5 · 照片的所有权边界（v1 的第 6 个错误）

明确写死，且**只给三样**：

```
From the photo take ONLY: the shape of the hair, {遮挡物}, and {1-2 个夸张五官}.
Everything else — body proportions, height, build, pose, clothing — comes from the model sheets.
```

> ❌ v1 写的 `Image 1 owns identity, age presentation, posture, build` —— 把 `build` 和 `posture` 给了真人照片，
> 模型就按真人解剖画，1:5 直接输掉。**身体的所有权永远属于参考图。**

---

## 6 · 中文核对模板

```
90 年代手绘赛璐璐动画设定稿。单人全身，正面，纯白底，空场。

体型：大头、短身、**五个头高**。厚外套的宽方肩是全身最宽处。腿又细又直。靴子巨大方正。手是没有手指分节的连指块。

角色：{一句话}

脸：小而简化的图形脸，五官集中在下半部。眼睛是两个纯深色椭圆。嘴是一条短线。两块硬边扁圆腮红。粗短眉。{遮挡物}。{夸张点1}。{夸张点2}。

服装：{内层}、{中层}、{外层}。布补丁、胶带条、明缝线、毛边下摆。胸口一个印刷数字「{n}」。{道具}。

上墨与填色：所有描边都是暖深褐 {线色HEX}，粗、圆头、手绘感，外轮廓最粗。每个颜色都是一块平涂哑光色 + 一块偏冷的硬边阴影。颜色暖、晒褪、有磨损但仍然饱和：{主强调HEX} 外套，{中性AHEX} 和 {中性BHEX} 占大部分，一小块 {意外色HEX}。单一左上光。

参考图：照抄参考图的身体比例、线宽和平涂方式。同一套画法，换一个人。
照片只拿三样：发型的形、{遮挡物}、{夸张五官}。身体比例、身高、体格、姿势、服装全部来自参考图。
```

---

## 7 · 调试阶梯（出图不对时，一次只动一个旋钮）

按顺序试，**不要一次改多处**——改多了不知道是哪个起的作用。

| 症状 | 第一个要动的旋钮 |
|---|---|
| **腿太长 / 身材写实** | 把 S2 提到 S1 前面；`five heads tall` 改成 `five heads tall,  and short-legged`；确认比例锚是 `27-cast-lineup` |
| **黑色细线** | 检查提示词里还有没有 `black` 这个词（哪怕在否定句里）——全删；`warm dark brown` 重复两次 |
| **有渐变 / 柔影** | S6 提到最前面；加 `poster-flat colour, like printed paper` |
| **脸是标准日漫脸** | 检查有没有 `anime`——删掉；`eyes are two solid dark oval shapes` 单独成句放 S1 之后 |
| **不像本人** | 照片里的 A 桶锚点没写进 S4，或遮挡物漏了 |
| **像参考图里的角色** | 加一句 `Same drawing system, different person.`（不要写长串 do-not-copy） |
| **太花太吵** | S5 砍掉一半形容词；确认中性色 HEX 有两个 |
| **全都不对** | 走 §8 两阶段法 |

---

## 8 · 两阶段法（顽固情况的兜底）

一次到位失败时，拆成两步，成功率高得多：

**阶段一 · 只出风格**
不给照片，只给两张参考图 + S1/S2/S6 三段（约 90 词），生成一个**风格正确但长相随机**的角色。
先确认比例、线色、平涂都对了。

**阶段二 · 换特征**
把阶段一的成品作为**唯一参考图**，指令：
```
Keep this exact drawing style, proportions, outline colour and flat shading.
Change only: the hair to {发型的形}, add {遮挡物}, make {夸张五官}.
```

> 风格一旦锁定在一张图里，后续改特征几乎不会漂。这也是做**角色多视图**和**群像**的正确方法。

---

## 9 · 多视图扩展

固定 `payload.json` 不变，**并把第一次的成品图作为参考图附上**，只换 S1：

| 需要 | S1 替换为 |
|---|---|
| 三视图 | `A 1990s hand-inked cel animation model sheet: the same character in three views — front, three-quarter, back — standing on one horizontal line, plain white background.` |
| 表情表 | `A 1990s hand-inked cel animation expression sheet: six heads of the same character — neutral, smiling, angry, surprised, tired, laughing. Plain white background.` |
| 动作表 | `A 1990s hand-inked cel animation pose sheet: four full-body poses of the same character. Plain white background.` |
| 半身像 | `A 1990s hand-inked cel animation model sheet. Single character, chest up, front view, plain white background.` |

---

## 10 · 拼装约定

1. 按 §1 七段顺序填字段，**实测总词数 ≤280 且风格段 ≥45%，超标只砍 S4/S6**
2. 按 §2 附两张参考图 + 那一句参考图指令
3. 按 §5 写死照片所有权边界
4. 按 §4 决定负面提示词策略——**无 negative 通道的模型一个否定词都不写**
5. **不要让 agent 自由补充描述**。每多一句自由发挥，风格就漂一点
6. 出图后对 `checklists/qc.md`；不对就按 §7 调试阶梯**一次动一个旋钮**
