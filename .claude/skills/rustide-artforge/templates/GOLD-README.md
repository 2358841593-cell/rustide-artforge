# 模板说明

| 文件 | 是什么 |
|---|---|
| `GOLD-v26-original.txt` | **实证配方，逐字保留，永不修改。** 产出 `角色成品/阿澈-浅蓝工作衫.png` 的原文 |
| `GOLD-from-scratch.txt` | 上面那份的参数化版本。**八段结构与原文逐字一致**，只把角色特定的值换成占位符 |

## 铁规矩

**改模板前，先 diff：**
```
diff <(grep -oE '^[A-Z][A-Z ]*[A-Z]:' templates/GOLD-v26-original.txt) \
     <(grep -oE '^[A-Z][A-Z ]*[A-Z]:' templates/GOLD-from-scratch.txt)
```
段序不一致就是改坏了。

## 曾经怎么改坏的

v26 之后我陆续加了 `PHOTO-LOCK` / `MOTIF` / `BIG SHAPE` / `FLAT FILL` 四个新段、
改了首句、把 `short stocky body` 换成 `{体型档位}`。**每一处单独看都有理由，合起来
把那份 245 词的配方改得只剩两段还认得出。** 之后再没出过认可的图。

> **新增段落之前先问：v26 那份没有这一段，照样出了认可的图。这一段真的必要吗？**
