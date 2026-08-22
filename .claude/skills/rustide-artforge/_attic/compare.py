#!/usr/bin/env python3
"""版本对比 · 判断新版是不是真的更好，防止"越改越偏"。
用法: python3 checklists/compare.py 旧版.png 新版.png
"""
import sys, os, subprocess, tempfile
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from measure import metrics, load, TARGET

LABEL = {"top_heavy":"上重下轻","line_rel":"相对线宽","shadow_pct":"暗部占比",
         "quiet_pct":"负空间","chroma_pct":"彩色占比","mean_sat":"平均饱和",
         "warm_pct":"暖色占比","curvature":"轮廓曲率"}

def dist(v, lo, hi):
    """离区间的距离，区间内为 0"""
    return 0.0 if lo <= v <= hi else (lo - v if v < lo else v - hi)

def norm(k, d):
    lo, hi = TARGET[k]
    span = (hi - lo) or 1
    return d / span

def ruler_pair(a, b):
    """左右并排的标尺对照图 —— 头身比只能人眼判，工具必须把图摆到人面前。"""
    out = os.path.join(os.path.dirname(os.path.abspath(b)), "_measure")
    os.makedirs(out, exist_ok=True)
    tmps = []
    for src in (a, b):
        f = os.path.join(tempfile.mkdtemp(), "r.png")
        im = load(src); W, H = im.size
        draws = []
        for n, col in ((5, "red"), (7, "blue")):
            for i in range(1, n):
                draws += ["-stroke", col, "-draw", f"line 0,{H*i//n} {W},{H*i//n}"]
        subprocess.run(["magick", src, "-background", "white", "-alpha", "remove", "-alpha", "off",
                        "-bordercolor", "white", "-border", "1", "-fuzz", "10%", "-trim", "+repage",
                        "-fill", "none", "-strokewidth", str(max(2, W//250))] + draws +
                       ["-resize", "x760", f], capture_output=True)
        tmps.append(f)
    dst = os.path.join(out, f"COMPARE-{os.path.basename(a)[:-4]}-vs-{os.path.basename(b)[:-4]}.png")
    subprocess.run(["magick"] + tmps + ["+append", "-background", "white", "-alpha", "remove", dst],
                   capture_output=True)
    return dst

def main(a, b):
    ma, mb = metrics(load(a)), metrics(load(b))
    print(f"{'指标':10} {os.path.basename(a)[:16]:>16} {os.path.basename(b)[:16]:>16}   变化")
    better = worse = same = 0
    for k, label in LABEL.items():
        lo, hi = TARGET[k]
        va, vb = ma[k], mb[k]
        da, db = norm(k, dist(va, lo, hi)), norm(k, dist(vb, lo, hi))
        fmt = "{:.2f}" if k in ("top_heavy", "mean_sat", "curvature") else "{:.1f}"
        if abs(da - db) < 0.02:
            tag, s = "持平", 0; same += 1
        elif db < da:
            tag, s = "✅ 更近", 1; better += 1
        else:
            tag, s = "❌ 更远", -1; worse += 1
        ina = "✓" if da == 0 else " "
        inb = "✓" if db == 0 else " "
        print(f"{label:10} {fmt.format(va):>15}{ina} {fmt.format(vb):>15}{inb}   {tag}")

    print(f"\n落在区间内: {os.path.basename(a)} {sum(1 for k in LABEL if dist(ma[k],*TARGET[k])==0)}/8"
          f"   {os.path.basename(b)} {sum(1 for k in LABEL if dist(mb[k],*TARGET[k])==0)}/8")
    print(f"更近 {better} 项 · 更远 {worse} 项 · 持平 {same} 项")
    print()
    rp = ruler_pair(a, b)
    print("━" * 62)
    print("⚠️ **头身比不在以上任何指标里** —— 它只能靠标尺图人眼判。")
    print(f"   已生成左右对照：_measure/{os.path.basename(rp)}")
    print("   左=旧版 右=新版，红线为 5 头身分割。**先看下巴位置，再看下面的判决。**")
    print()
    print("   实测教训：v36 在指标上 5/8 达标、优于 v26 的 3/8，compare 判了'可以采用'，")
    print("   但它的头身比已退回约 7 头身、画风崩坏。**指标全绿救不了比例崩坏。**")
    print("━" * 62)
    print()
    if worse > better:
        print("判决：**新版整体更差，建议回退到旧版。**")
        print("      这就是「越改越偏」。修一个指标打坏另一个时，退回去比继续改更省。")
        return 1
    if better > worse:
        print("判决：新版更接近参考区间。")
    else:
        print("判决：互有胜负。")
    print()
    print("⚠️ **指标是门槛，不是目标。最终由人眼选片。**")
    print("   实测反例：v26 只有 3/8 落在区间内，v28 有 5/8，")
    print("   但用户认为 **v26 更好看**。指标全过不等于画得好，")
    print("   指标略差也不构成返工理由。**不要为了刷指标反复重抽。**")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
