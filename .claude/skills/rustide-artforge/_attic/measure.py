#!/usr/bin/env python3
"""出图体检 · 量出来，不靠勾选。
阈值不是拍的，是从 assets/refs-cel/ 的官方早期人设标定出来的。
用法:
  python3 checklists/measure.py <image.png>     体检一张图
  python3 checklists/measure.py --calibrate     重新标定阈值（打印参考图的实测区间）
"""
import sys, subprocess, tempfile, os, glob, colorsys, statistics as st
from collections import Counter

# 从官方早期人设 06-13 标定得来。改动前请先跑 --calibrate。
# 阈值来自 --calibrate 在 06-13 八张官方早期人设上的实测区间，不是拍脑袋。
# 阈值 = 八张官方早期人设的**实测区间**（--calibrate 得来），上下限都有。
# ⚠️ 早期版本全是"下限 + 无上限"，等于在说"越多越好"。
#    结果 v13→v24 跑了 12 版，把暖色推到 98%（参考上限 94.7）、暗部 84%（上限 76.7）、
#    线宽 18.6（中位 6.6）。**单边门禁会诱发最大化行为，这是过度迭代的根因。**
#    上限统一取 实测max + 约10% 余量。
TARGET = {
    "top_heavy":   (1.05, 2.75),   # 实测 1.07–2.49
    "quiet_pct":   (20, 36),       # 实测 20.0–31.7
    "line_rel":    (5.0, 12.0),    # 实测 5.4–7.0（所罗门37.8/丹尼尔21.8 是深色发块造成的测量假象，已排除）
    "shadow_pct":  (33, 80),       # 实测 33.6–76.7
    "chroma_pct":  (29, 70),       # 实测 29.4–64.3
    "mean_sat":    (0.53, 0.72),   # 实测 0.53–0.66
    "warm_pct":    (71, 95),       # 实测 71.2–94.7
    "curvature":   (1.00, 2.6),    # 实测 1.09–2.22。手绘抖动，出图偏直只有 0.82
}
REFS = "assets/refs-cel"

def load(src):
    from PIL import Image
    out = os.path.join(tempfile.mkdtemp(), "t.png")
    subprocess.run(["magick", src, "-background", "white", "-alpha", "remove", "-alpha", "off",
                    "-bordercolor", "white", "-border", "1", "-fuzz", "10%", "-trim", "+repage", out],
                   check=True, capture_output=True)
    return Image.open(out).convert("RGB")

def metrics(im):
    W, H = im.size
    px = im.load()
    ink = lambda x, y: sum(px[x, y]) < 700

    # 行宽剖面
    prof = []
    for y in range(H):
        xs = [x for x in range(W) if ink(x, y)]
        prof.append((max(xs) - min(xs) + 1) if xs else 0)

    # 上重下轻：全身最宽 / 小腿处(72%~85%)最宽
    widest = max(prof)
    calf = max(prof[int(H * 0.72):int(H * 0.85)] or [1])
    top_heavy = widest / calf if calf else 0

    # 平涂率：与右邻像素完全同色的比例（渐变/纹理会拉低）
    same = tot = 0
    for y in range(0, H, 2):
        for x in range(0, W - 1, 2):
            if px[x, y] == (255, 255, 255):
                continue
            tot += 1
            if px[x, y] == px[x + 1, y]:
                same += 1
    flat_pct = same / tot * 100 if tot else 0

    # 负空间：6x10 网格，唯一色数 ≤ 中位数一半的格子算"安静"
    gx, gy, cells = 6, 10, []
    for j in range(gy):
        for i in range(gx):
            x0, x1, y0, y1 = i*W//gx, (i+1)*W//gx, j*H//gy, (j+1)*H//gy
            cells.append(len({px[x, y] for y in range(y0, y1, 3) for x in range(x0, x1, 3)}))
    med = st.median(cells)
    quiet_pct = sum(1 for c in cells if c <= med * 0.5) / len(cells) * 100

    # 相对线宽：每条扫描线从左侧进入人物时，第一段深色的长度
    isdark = lambda c: sum(c) < 330
    runs = []
    for y in range(int(H*0.15), int(H*0.90), 3):
        x = 0
        while x < W and sum(px[x, y]) > 700: x += 1
        if x >= W: continue
        n = 0
        while x + n < W and isdark(px[x + n, y]): n += 1
        if 0 < n < W * 0.15: runs.append(n)
    line_rel = (sorted(runs)[len(runs)//2] / H * 1000) if runs else 0

    # 暗部占比：量化后按色相分族，同色相里有明暗两级时，较暗那些算阴影
    q = im.quantize(colors=24, method=1).convert("RGB")
    qp = q.load()
    cnt = Counter(qp[x, y] for y in range(0, H, 2) for x in range(0, W, 2)
                  if sum(px[x, y]) < 730)
    tot = sum(cnt.values())
    fam = {}
    for c, n in cnt.items():
        hh, ll, ss = colorsys.rgb_to_hls(*[v/255 for v in c])
        if ss < 0.12: continue
        fam.setdefault(round(hh*12), []).append((ll, n))
    sh = 0
    for v in fam.values():
        v.sort()
        if len(v) >= 2 and v[-1][0] - v[0][0] > 0.08:
            sh += sum(n for l, n in v[:-1])
    shadow_pct = sh / tot * 100 if tot else 0

    # 轮廓曲率：手绘感的量化形态。参考图轮廓不断改变方向，出图偏直偏光滑
    sc = im.resize((max(1, W * 900 // H), 900)); sp = sc.load(); SW, SH = sc.size
    Lb, Rb = [], []
    for y in range(SH):
        xs = [x for x in range(SW) if sum(sp[x, y]) < 700]
        if xs: Lb.append(min(xs)); Rb.append(max(xs))
    def curv(b):
        if len(b) < 30: return 0
        d = [b[i+1] - b[i] for i in range(len(b)-1)]
        k = [abs(d[i+1] - d[i]) for i in range(len(d)-1)]
        return sum(k) / len(k) if k else 0
    curvature = (curv(Lb) + curv(Rb)) / 2

    # 色彩三项：彩度占比 / 平均饱和 / 暖色占比
    ctot = cchrom = cwarm = 0; sats = []
    for y in range(0, H, 2):
        for x in range(0, W, 2):
            c = px[x, y]
            if sum(c) > 730: continue
            ctot += 1
            hh, ll, ss = colorsys.rgb_to_hls(*[v/255 for v in c])
            if ss > 0.20 and 0.15 < ll < 0.90:
                cchrom += 1; sats.append(ss)
                if hh < 0.13 or hh > 0.92: cwarm += 1
    chroma_pct = cchrom / ctot * 100 if ctot else 0
    mean_sat = sum(sats) / len(sats) if sats else 0
    warm_pct = cwarm / cchrom * 100 if cchrom else 0

    # 描边主色
    dark = [px[x, y] for y in range(0, H, 3) for x in range(0, W, 3) if sum(px[x, y]) < 230]
    line = Counter(dark).most_common(1)[0][0] if dark else (0, 0, 0)

    return dict(size=(W, H), prof=prof, top_heavy=top_heavy, curvature=curvature,
                line_rel=line_rel, shadow_pct=shadow_pct,
                chroma_pct=chroma_pct, mean_sat=mean_sat, warm_pct=warm_pct,
                flat_pct=flat_pct, quiet_pct=quiet_pct, line=line)

def calibrate():
    """只读：不生成任何文件。"""
    files = sorted(glob.glob(f"{REFS}/0[6-9]-*.png") + glob.glob(f"{REFS}/1[0-3]-*.png"))
    acc = {k: [] for k in ("top_heavy", "quiet_pct", "line_rel", "shadow_pct",
                           "chroma_pct", "mean_sat", "warm_pct", "curvature")}
    for f in files:
        m = metrics(load(f))
        for k in acc:
            acc[k].append(m[k])
        print(f"  {os.path.basename(f):30} 线宽{m['line_rel']:5.1f} 暗部{m['shadow_pct']:5.1f}% "
              f"彩度{m['chroma_pct']:5.1f}% 饱和{m['mean_sat']:5.2f} 暖色{m['warm_pct']:5.1f}% 曲率{m['curvature']:5.2f}")
    print("\n官方参考实测区间（建议阈值取此区间）:")
    for k, v in acc.items():
        print(f"  {k:11} min {min(v):6.2f}  中位 {st.median(v):6.2f}  max {max(v):6.2f}")

def check(src):
    m = metrics(load(src))
    print(f"人物尺寸 {m['size'][0]}x{m['size'][1]}")
    rows = [("上重下轻", "top_heavy", "{:.2f}"), ("相对线宽", "line_rel", "{:.1f}"),
            ("暗部占比", "shadow_pct", "{:.1f}%"), ("负空间", "quiet_pct", "{:.0f}%"),
            ("彩色占比", "chroma_pct", "{:.1f}%"), ("平均饱和", "mean_sat", "{:.2f}"),
            ("暖色占比", "warm_pct", "{:.1f}%"), ("轮廓曲率", "curvature", "{:.2f}")]
    bad = 0
    for label, key, fmt in rows:
        lo, hi = TARGET[key]
        v = m[key]
        ok = lo <= v <= hi
        bad += not ok
        mark = "✅" if ok else ("❌偏低" if v < lo else "❌超出(过犹不及)")
        print(f"{label:8} {fmt.format(v):>10}   参考区间 {lo}–{hi}   {mark}")
    print(f"{'平涂率':8} {m['flat_pct']:9.1f}%   仅供同分辨率横向比（官方扫描件 12–28%）")
    r, g, b = m["line"]
    warm = r >= b and r > 28
    bad += not warm
    print(f"{'描边主色':8} {'#%02X%02X%02X' % (r, g, b):>10}   要暖褐 R≥B 且 R>28        {'✅' if warm else '❌'}")
    # 头身比：生成标尺图，人眼判
    base = os.path.basename(os.path.splitext(src)[0])
    if base.endswith("-ruler"):
        print("\n（输入本身是标尺图，跳过标尺生成）")
        return bad
    rdir = os.path.join(os.path.dirname(os.path.abspath(src)), "_measure")
    os.makedirs(rdir, exist_ok=True)
    ruler = os.path.join(rdir, base + "-ruler.png")
    W, H = m["size"]
    draws = []
    for n, col in ((5, "red"), (7, "blue")):
        for i in range(1, n):
            draws += ["-stroke", col, "-draw", f"line 0,{H*i//n} {W},{H*i//n}"]
    subprocess.run(["magick", src, "-background", "white", "-alpha", "remove", "-alpha", "off",
                    "-bordercolor", "white", "-border", "1", "-fuzz", "10%", "-trim", "+repage",
                    "-fill", "none", "-strokewidth", str(max(2, W // 250))] + draws +
                   ["-resize", "520x", ruler], capture_output=True)
    print(f"\n头身比   → 看标尺图 _measure/{os.path.basename(ruler)}")
    print("         红线=5头身分割，蓝线=7头身分割。**下巴应落在第一条红线上或略高**。")
    print("         下巴若在第一条蓝线之上 = 超过7头身 = 不合格。")
    return bad

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--calibrate":
        calibrate()
    else:
        sys.exit(1 if check(sys.argv[1]) else 0)
