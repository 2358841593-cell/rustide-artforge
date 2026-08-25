---
name: rustide-artforge
description: 把一张真人照片转成《锈汛 RUSTIDE》世界里的角色——风来之国式赛璐璐平涂人设立绘。产物是一份可直接交给 Codex / 任意生图 agent 的英文出图提示词。当用户发来照片说"做成角色/立绘/人设"，或提到 风来之国 / Eastward 画风 / 赛璐璐 / 锈汛 / RUSTIDE / 角色设定 / 出图提示词 时使用。
---

# RUSTIDE ARTFORGE

把真人照片锻成《锈汛》世界的居民。**产物是提示词，不是图。**

## 跑一次 → 只读 [`RUN.md`](RUN.md)

那一个文件里有全部需要的东西：步骤 · 上墨锚表 · 14 个职业 · 五个菜单 · 三条易错点。
**约 2900 tokens。跑的时候不要读 `references/`。**

```bash
python3 checklists/check.py prompt.txt   # 出图前
python3 checklists/check.py 出图.png      # 出图后（生成标尺图判头身比）
```

## 出问题了 → 按症状查

| 症状 | 查这个 |
|---|---|
| 比例跑了 / 发油 / 线太细 / 太精细 | `references/art-visual.md` |
| 不够夸张 / 五官一个样 / 女性出不来 / 杂物同质化 | `references/art-design-direction.md` |
| 颜色发灰 / 肤色发黄 / 撞色 | `references/palette.md` |
| 不像本人 / 衣服和照片无关 | `references/photo-to-character.md` |
| 像通用蒸汽朋克 / 没有世界观味道 | `references/world/00-core.md` |
| 想给角色写小传 | `references/world/daily-life.md` |
| 做游戏用的像素小人 | `references/pixel-sprite.md` |
| 指标数值对不上 | `references/metrics.md` |

## 目录

```
RUN.md                    ← 跑一次只读这个
templates/
  GOLD-from-scratch.txt   主模板（参数化）
  GOLD-v26-original.txt   实证配方原文，永不修改
checklists/check.py       唯一的工具
references/               查证用，跑的时候不读
  art-visual.md           线 / 色 / 光 / 质感 + 全部实测数据
  art-design-direction.md 比例 / 脸 / 服装 / 女性 / 杂物
  palette.md              调色板（色值实采自官图）
  photo-to-character.md   照片 → 角色 · 三层法
  metrics.md              八项指标的官图实测区间
  world/                  设定集（00-core / professions / daily-life / cast）
examples/worked-example.md 填空示范
assets/refs-cel/          官方参考图 16 张
_attic/                   已退役的 9 个工具与 27 条铁律
```

## 三层法

| 层 | 来源 | 决定什么 | 出问题时改哪 |
|---|---|---|---|
| **① 画法层** | 固定常量 | 五头身、`short stocky`、暖褐线、平涂 | 比例 / 发油 / 线 |
| **② 照片层** | 照片 | 五官、发型、四肢粗细、服装款式 | 不像本人 |
| **③ 故事层** | 职业档案 + 小传 | 随身物、杂物类、母题、道具 | 同质化 / 没世界观味 |

**三层互不覆盖。** 混在一起就会为了「像本人」把比例改坏——实测踩过。
