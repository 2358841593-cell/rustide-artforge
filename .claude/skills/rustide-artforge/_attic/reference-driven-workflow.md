# 参考图驱动工作流（主路径）

> **纯文字提示词锁不住画风。** v1/v3 两次实测证明：规格写得再全，模型也只执行一部分。
> 正确做法是**让参考图承担风格，让提示词只承担差异**。
> 本文件是 R1 的**主路径**；`prompt-recipes.md` 的纯文字模式降为兜底。

---

## 0 · 为什么参考图赢过提示词

| | 文字提示词 | 参考图 |
|---|---|---|
| 线的颜色和粗细 | 说了也常不听 | **直接看到** |
| 头身比 | `five heads tall` 只能推一点 | **直接量到** |
| 平涂 vs 渐变 | 说了容易漂 | **直接看到** |
| 肤色明度 | 必须给 HEX 且防污染 | **直接看到** |
| 手绘线的抖动质感 | 几乎无法用词描述 | **只能靠图** |

> 结论：**风格归图，内容归词。** 提示词里凡是能被参考图看到的东西，都该删掉，把词数配额留给"这个角色和参考图哪里不一样"。

---

## 1 · 三阶段闭环

```
阶段 0 · 铸锚          官方参考图 + 极短提示词
   ↓                  → 生成一个「风格对、长相随机」的角色
   ↓                  → 人工确认 → 存进 assets/style-anchors/
   ↓
阶段 1 · 出角色        用【风格锚】(不是官方图) + 短提示词
   ↓                  → 提示词只写「和锚点不一样的地方」
   ↓
阶段 2 · 锚点晋升      认可的图存回 assets/style-anchors/
                      → 标注它锁定了什么 → 下次直接用
```

### 为什么用自己的产出当锚点，比用官方图更稳

官方图是 **300–600px 的低分辨率手绘扫描**，和生图模型的输出分布差得远，模型"学"它时要跨一个大 gap。
而**我们自己认可的成品**就在模型的输出分布里——它复现自己画过的东西，比模仿一张陌生扫描件容易得多。

> 所以：**官方图只在阶段 0 用一次**，之后全程用自己的锚点。

---

## 2 · 阶段 0 · 铸锚

**目标**：拿到第一张风格完全正确的图。长相随机，不管像不像谁。

### 参考图（两张，固定）
1. `assets/refs-cel/27-opening-cast-lineup.png` — 比例锚
2. `assets/refs-cel/06-john-early-portrait.png` — 上墨锚

> ❌ 永远不要用 `08-alva` 当比例锚（全组最瘦，会教反）。

### 提示词（~130 词，只有风格段 + LINE/DETAIL）

```
A 1990s hand-inked cel animation model sheet. Single character, full body, front view,
plain white background.

BUILD: big head, short body, five heads tall. A thick jacket with wide square
shoulders is the widest part. Very thin straight legs. Huge heavy square boots. Hands are

FACE: small graphic face, features low on the head. Eyes are two solid dark ovals. Mouth is
one short line. Two hard-edged oval blush patches. SKIN: pale pink-beige #F5E0BC with one
shadow #DCC29B.

LINE: brush-like line weight — very thick at the silhouette, thin and sometimes broken inside.
Torn jagged hems, collar flaring outward, big sharp pointed hair tufts, the coat flares out
well past the hips. At least fifteen small mismatched details — badges, tape, patches, torn
holes, buckles. Nothing is tidy or matched.

INK AND FILL: every outline is warm dark brown #2E241F, thick, rounded, hand-drawn, outer
silhouette thickest. Every colour is one flat matte fill with a single hard-edged shadow.
One strong brick-red #DD5233 accent. Single light from upper left.

Copy the proportions, outline weight and flat colour treatment of the references.
```

### 验收（不过就重铸，别往下走）
跑 `checklists/qc.md` A 组 + B 组前 5 条。**特别确认**：
- [ ] 描边是暖褐不是黑
- [ ] 零渐变
- [ ] 五个头高、腿细、靴子大
- [ ] **皮肤是浅粉米色 `#F5E0BC` 一带**（不是蜡黄）
- [ ] **身上细节 ≥15 个，且是杂的不是整齐的**
- [ ] 下摆锯齿、领子外翻、线宽有变化
- [ ] 有一块**高饱和**的强调色（不是一团灰）

### 存档
```
assets/style-anchors/A00-base.png
```
并在 `assets/style-anchors/MANIFEST.md` 记一行：它锁定了什么、什么时候铸的。

---

## 3 · 阶段 1 · 出角色

**参考图**：`style-anchors/A00-base.png`（+ 照片，如果是照片转译）

**提示词只写差异 + 参考图学不会的东西。**

实测教训：模型**不会**自动从参考图学到细节密度、线宽变化、锯齿下摆、外扩廓形——
这四样必须显式写。而线色、平涂、比例它学得还行。

```
Same drawing style and proportions as the reference sheets: warm dark brown #2E241F
outlines, every colour one flat matte fill with one hard-edged shadow; big head, five heads
tall, thin legs, huge square boots. A different person.

LINE: brush-like line weight — very thick at the silhouette, thin and sometimes broken
inside. Torn jagged hems, collar flaring outward, big sharp pointed hair tufts, the outer
coat flares out well past the hips.

PHOTO-LOCK: from the photo the face and body keep only these traits, amplified —
{体型档位}, {脸型}, {眼型}, {眉}, {鼻}, {肤色档位}. The face and body carry these traits and
these alone. Costume, props and hair styling stay free to exaggerate.

SKIN: pale pink-beige #{skin_hex} with one shadow #{skin_shadow_hex}. The skin stays pale.

WHO: {一句话}.

FACE: {遮挡物}. {夸张五官 1}. {夸张五官 2}. Eyes are two solid dark ovals, mouth one short
line, two hard-edged oval blush patches, thick short eyebrows.

CLOTHES (a scavenged version of what the photo wears): {照片款式的改造版，三层}.

DETAIL: he is covered in at least fifteen small mismatched details — round badges and pins of
different sizes and clashing colours, strips of tape, patches of different shapes, visible
stitching, torn holes, hanging cloth strips, buckles, a hanging tool. Nothing is tidy or
matched. Printed "{n}" on the chest.

CLOTHING COLOURS: {accent_hex} {哪件}, {neutral_a_hex} and {neutral_b_hex} elsewhere, a small
{surprise_hex} accent. The clothing colours are warm and sun-bleached, saturated but worn.
```

约 **230–260 词**。比纯文字模式的 900 词短得多，但比最初设想的 140 词长——
因为实测发现 LINE 和 DETAIL 两段**不能省**，参考图教不会。

### 四条硬规则（每条都是实测踩出来的）

1. **SKIN 单独成段，在 CLOTHES 之前，且叫 `pale pink-beige` 不叫 `warm cream`。**
   实测：给 `#FCE8A4` 出图变成 `#EFCD86`，蓝通道掉 46，发蜡黄。`cream`/`warm` 会被往黄拉。
2. **`dusty / muted` 必须限定作用域到衣服。**
   写 `The clothing colours are warm and sun-bleached, saturated but worn.`，**不要**写 `The clothing colours are warm and sun-bleached.`
3. **CLOTHES 必须标注是照片服装的改造版。**
   写 `a scavenged version of what the photo wears`。
   旧版把服装划给参考图 + 硬塞自编工装，出图和照片毫无关系。
4. **DETAIL 段不可省，且要点明"杂、不成套"。**
   参考图身上有 16–20 个小细节，我们第一轮只有 4–5 个。模型不会自己数。

---

## 4 · 阶段 2 · 锚点晋升

出图**你认可**之后（不是"差不多"，是真的对），存进锚点库：

```
assets/style-anchors/A0N-{描述}.png
```

并在 `MANIFEST.md` 记一行，**写清楚它锁定了什么**——因为不同锚点擅长的东西不同：

| 锚点类型 | 锁定什么 | 下次什么时候用 |
|---|---|---|
| 基础锚 `A00-base` | 线、平涂、比例、肤色 | 默认起手 |
| 儿童锚 | 1:3.5 比例、大头 | 做小孩时 |
| 老人锚 | 1:4 矮宽比例 | 做长辈时 |
| 机械锚 | 非人比例、金属画法 | 做机器人时 |
| 群像锚 | 多人同框的一致性 | 做排队图时 |

> 锚点库会**越用越准**。这是这套流程真正的复利所在。

---

## 5 · 什么时候回退到纯文字模式

只有两种情况：
1. **阶段 0 铸锚本身**（那时还没有锚点）
2. 生图工具**不支持传参考图**

其余一律走参考图驱动。纯文字模式见 `prompt-recipes.md`。

---

## 6 · 失败时的分诊

| 症状 | 是谁的问题 | 修哪 |
|---|---|---|
| 线、平涂、比例不对 | **锚点不合格** | 回阶段 0 重铸，别在阶段 1 硬调 |
| 风格对但不像本人 | 提示词的 CHANGE 段太弱 | 加强 A 桶锚点描述 |
| 皮肤发黄发暗 | SKIN 段缺失或被 muted 波及 | §3 两条防污染规则 |
| 整体灰成一团 | 强调色饱和度不够 / 占比不足 | 换一个高饱和主强调色，见 `palette.md` §2 |
| 像锚点里那个人 | 缺 `A different person.` | 补上这一句（**不要**写长串 do-not-copy） |
| 越改越漂 | 一次改了多处 | 一次只动一个旋钮 |
