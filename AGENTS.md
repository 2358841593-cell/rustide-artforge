# 给 Codex / 任意生图 agent

《锈汛 RUSTIDE》角色美术生成 skill。**产物是提示词，不是图。**

## 跑一次

**只读这两个文件**（约 6400 tokens）：
1. `.claude/skills/rustide-artforge/RUN.md` —— 步骤 · 上墨锚表 · 14 个职业 · 五个菜单
2. `.claude/skills/rustide-artforge/templates/GOLD-from-scratch.txt` —— 模板

**不要读 `references/`**，那是出问题时按症状查的（对照表见 `SKILL.md`）。

## 两条命令

```bash
python3 .claude/skills/rustide-artforge/checklists/check.py prompt.txt   # 出图前
python3 .claude/skills/rustide-artforge/checklists/check.py 出图.png      # 出图后
```

## 三条最容易犯的错

1. `short stocky body` / `five heads tall` 是画法常量，任何角色都要写。改成 `slim` 必出 7 头身。
2. 禁用 `anime` / `black` / `chibi` / `realistic` / `muted` / `dusty`，**哪怕在否定句里**；**零否定词**。
3. **必须生成模式**。`edit target` / `retain the` / `change only` 会被拦下。

## 产物

成品放 `角色成品/`，**提示词同名 `.txt` 一起存**，登记进 `references/world/cast.md`。
中间废版本当场删，不要建 `outputs/` `_archive/`。
