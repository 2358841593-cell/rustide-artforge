# 项目说明（给 Codex / 任意生图 agent）

《锈汛 RUSTIDE》美术资产生成系统。

## 用法

读 `.claude/skills/rustide-artforge/SKILL.md`（53 行），照着做。**不需要别的指令。**

最短路径：
1. 抄 `templates/GOLD-from-scratch.txt`，填占位符，**结构不改**
2. `python3 .claude/skills/rustide-artforge/checklists/check.py prompt.txt` —— 红的必须修
3. 出图，附 `assets/refs-cel/27-opening-cast-lineup.png` + `06-john-early-portrait.png`
4. `python3 .claude/skills/rustide-artforge/checklists/check.py 出图.png` —— 看标尺图判头身比

## 三条硬检查

- 禁用 `anime` / `black` / `chibi` / `realistic` / `muted` / `dusty`，**哪怕在否定句里**
- **零否定词**（生图模型没有 negative 通道）
- **PHOTO-LOCK 段**：参考图只提供画法，不提供五官

## 三条容易犯的错

- **生成模式是默认**。编辑模式只允许单次单点，绝不连续
- **生理域**（五官/脸型/胖瘦）只能放大照片里已有的；装扮域随便夸张
- **一次只动一个旋钮**，单轮最多 3 版，人眼选片

## 产物纪律

成品放 `角色成品/`，一个角色一张，中文命名。
**中间版本、提示词、QC 报告当场删。不要建 `outputs/` `_archive/` `_measure/`。**
曾积累到 168 个文件 / 52MB，全是废版本。

已认可的成品可当参考图用，比官方扫描件更贴近模型自身分布。

## 当前范围

✅ R1 角色立绘 · 🔒 R2 像素小人 / R3 海报 / R4 场景 —— 见 `ROADMAP.md`
