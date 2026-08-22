#!/usr/bin/env python3
"""唯一的检查工具。

出图前：  python3 checklists/check.py prompt.txt
出图后：  python3 checklists/check.py 出图.png     → 生成标尺图，人眼判头身比

只保留三条有实测证据、且单独就能挡住灾难的检查。其余都在 _attic/。
"""
import sys, os, re, subprocess, tempfile
sys.dont_write_bytecode = True

# ── 提示词检查（三条）────────────────────────────────────────────
BANNED = {
    "anime":     "会召唤 1:7 身材 + 亮晶大眼 + 细黑线的默认先验，碾压后文",
    "black":     "会让描边变成纯黑（哪怕写在 NEVER pure black 里也一样）",
    "chibi":     "同上，是负面词也会被当成待画清单",
    "realistic": "同上",
    "muted":     "参考图平均饱和 0.60，一点不muted；这个词让出图彩度掉到 7%",
    "dusty":     "同上",
    "desaturated": "同上",
}
ALLOW = r"\b(black|dark) (hair|fringe|beard|coat|boots|gloves|vest)\b"

def check_prompt(path):
    text = open(path).read()
    warn = []
    low = re.sub(r"\s+", " ", text.lower())
    scrub = re.sub(ALLOW, "", low).replace("cel animation", "")
    bad = []

    for w, why in BANNED.items():
        if re.search(rf"\b{w}\b", scrub):
            bad.append(f"禁用词 '{w}' —— {why}")

    negs = sorted(set(re.findall(r"\b(no|not|never|without|avoid)\b", low)))
    if negs:
        bad.append(f"否定词 {negs} —— GPT-Image/Codex 没有 negative 通道，"
                   "否定≈把这个概念念一遍。改成正面陈述")

    # PHOTO-LOCK 曾是硬门禁，已撤销为提醒。
    # 原因：它是为了消灭"照片里没有的红鼻头"而加的，但**用户认可的 ANCHOR-A 本身就有红鼻头**，
    # 而且产出那张的 v26 配方里根本没有 PHOTO-LOCK 段。这道门禁挡住了恢复已验证的配方。
    # —— 生成式硬保证 ——
    # 实测：编辑模式（拿上一张图当底改）连续用会累积漂移，8 次后头身比从 5 退到 7。
    # 而两张认可的成品都是**生成模式**出的。skill 必须是生成类。
    EDIT = r"(as the edit target|edit target|keep its (pose|exact)|retain the|change only|"\
           r"preserve its|same character in the reference|unchanged)"
    hits = sorted({m[0] if isinstance(m, tuple) else m for m in re.findall(EDIT, low)})
    if hits:
        bad.append(f"出现编辑模式措辞 {hits} —— **本 skill 必须是生成类**：从照片直出，"
                   "不拿上一张图当底改。编辑链会累积漂移（实测连改 8 次，头身比从 5 退到 7）")

    if re.search(r"\bphoto\b", low) and "PHOTO-LOCK" not in text.upper():
        warn.append("没有 PHOTO-LOCK 段（提醒，不阻断）—— 若不希望模型从参考图带走五官可以加，"
                    "但产出 ANCHOR-A 的 v26 配方并没有这一段")

    print(f"{os.path.basename(path)} · {len(text.split())} 词")
    for w in warn:
        print(f"  ⚠️  {w}")
    for b in bad:
        print(f"  ❌ {b}")
    if not bad:
        print("  ✅ 通过")
    return 1 if bad else 0

# ── 出图后：质感门禁 + 标尺图 ────────────────────────────────────
# 阈值取自 assets/refs-cel 四张官方早期人设，统一缩到 700px 高后实测。
# ⚠️ 阈值按**用户认可的两张成品**标定，不是按官方扫描件。
#    官方是 300–600px 扫描件（平涂 15–25%），生图模型达不到也不需要达到。
#    用户认可的 ANCHOR-A 是 4.1%/2715、ANCHOR-B 是 6.4%/2010 —— 那才是实际目标。
FLAT_MIN = 3.5    # 平涂率 %：认可成品 4.1–6.4；崩坏版曾低到 2.2
DENS_MAX = 3000   # 每万像素独立色数：认可成品 2010–2715；崩坏版曾高到 3528

def texture_gate(src):
    """量'油'：平涂率太低 + 色密度太高 = 渲染感，不是手绘平涂。"""
    from PIL import Image
    im = Image.open(_norm(src, 700)).convert("RGB")
    W, H = im.size; px = im.load()
    body = [(x, y) for y in range(H) for x in range(W) if sum(px[x, y]) < 735]
    n = len(body) or 1
    same = sum(1 for x, y in body if x + 1 < W and px[x, y] == px[x + 1, y])
    flat = same / n * 100
    dens = len({px[x, y] for x, y in body}) / n * 10000
    ok = True
    print(f"平涂率  {flat:5.1f}%   目标 4.1–6.4 ", end="   ")
    if flat < FLAT_MIN:
        print("❌ 偏低 = 渲染感/油"); ok = False
    else:
        print("✅")
    print(f"色密度  {dens:5.0f}    目标 2010–2715", end="   ")
    if dens > DENS_MAX:
        print("❌ 偏高 = 画得太精细"); ok = False
    else:
        print("✅")
    if not ok:
        print("  → 这两条**不是靠重抽能解决的**，要改提示词措辞：")
        print("     · 用 `cel-painted`、`flat colour fields`，**不要用 `cel-shaded`**")
        print("       （后者在 CG 语境里指三维卡通渲染，会把图往'油'里带）")
        print("     · 明写 `the whole figure uses about twenty flat colours;")
        print("       each area is one single colour, identical across the whole area`")
    return 0 if ok else 1

def _norm(src, H):
    import tempfile
    o = os.path.join(tempfile.mkdtemp(), "n.png")
    subprocess.run(["magick", src, "-background", "white", "-alpha", "remove", "-alpha", "off",
                    "-bordercolor", "white", "-border", "1", "-fuzz", "10%", "-trim", "+repage",
                    "-resize", f"x{H}", o], check=True, capture_output=True)
    return o

def make_ruler(src):
    out = os.path.join(os.path.dirname(os.path.abspath(src)), "_measure")
    os.makedirs(out, exist_ok=True)
    dst = os.path.join(out, os.path.splitext(os.path.basename(src))[0] + "-ruler.png")
    t = os.path.join(tempfile.mkdtemp(), "t.png")
    subprocess.run(["magick", src, "-background", "white", "-alpha", "remove", "-alpha", "off",
                    "-bordercolor", "white", "-border", "1", "-fuzz", "10%", "-trim", "+repage", t],
                   check=True, capture_output=True)
    W, H = map(int, subprocess.check_output(["magick", t, "-format", "%w %h", "info:"]).split())
    draws = []
    for i in range(1, 5):
        draws += ["-stroke", "red", "-draw", f"line 0,{H*i//5} {W},{H*i//5}"]
    subprocess.run(["magick", t, "-fill", "none", "-strokewidth", str(max(2, W // 250))]
                   + draws + ["-resize", "x800", dst], check=True, capture_output=True)
    print(f"标尺图 → _measure/{os.path.basename(dst)}")
    print("  红线把人物五等分。**下巴应落在第一条红线附近**（±8% 图高都算合格）。")
    print("  下巴明显在第一条线之上 = 比例跑了，这是唯一必须返工的情况。")
    return 0

if __name__ == "__main__":
    a = sys.argv[1]
    sys.exit((texture_gate(a) or make_ruler(a)) if a.lower().endswith((".png", ".jpg", ".jpeg")) else check_prompt(a))
