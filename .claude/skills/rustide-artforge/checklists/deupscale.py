#!/usr/bin/env python3
"""把「像素风的放大渲染图」还原成真正的像素点阵。

和 spritecut 是两件事，别混：
  spritecut  连续色调插画 → 面积平均 + 量化 → **重新决定**每个像素
  deupscale  已经是像素、只是被放大 → 测块边长 + 每块取代表色 → **不重新决定**

对已经是像素的图跑 spritecut 会再采样一次，出半像素错位和多余颜色，反而更糊。

块边长用边缘能量的自相关自动测（块边界处差异能量周期性地高），
相位用「哪个偏移下块边界的能量最大」定。每块取**中位色**而不是均值 ——
AI 渲染出来的块内有噪声和渐变，均值会把边界糊掉。

⚠️ --colors 默认关着，别随手开。在一张多格的连图上做 MEDIANCUT，调色板会被
面积大的颜色（肤色、发色、白）占满，**小面积的强调色直接被合并掉** ——
实测 8 连表情图量化到 24/48 色，绿眼睛和绿领带全变灰。要限色就单张单张地量。

⚠️ --tol 也别随手加大。底色泛洪会从**浅色的边缘**漏进角色内部：
实测 tol 从 12 提到 30，泛洪顺着裸露的肩膀钻进去，把肩线啃出洞。

用法:
  deupscale.py <输入> <输出目录> [--period N] [--colors N] [--split 行x列] [--tol N]
"""
import sys, os, argparse, statistics
sys.dont_write_bytecode = True
from collections import Counter, deque
from PIL import Image


def energy(px, W, H, axis, step=3):
    if axis == "x":
        return [sum(abs(px[x, y][k] - px[x - 1, y][k])
                    for y in range(0, H, step) for k in range(3))
                for x in range(1, W)]
    return [sum(abs(px[x, y][k] - px[x, y - 1][k])
                for x in range(0, W, step) for k in range(3))
            for y in range(1, H)]


def detect_period(e, lo=2, hi=40):
    """自相关取最强周期。谐波（2T、3T）分值也高，所以从小到大找第一个显著峰。"""
    m = statistics.mean(e)
    d = [v - m for v in e]
    scores = {T: sum(d[i] * d[i + T] for i in range(len(d) - T)) / (len(d) - T)
              for T in range(lo, hi + 1)}
    return max(scores, key=scores.get)


def detect_phase(px, W, H, T, axis, step=5):
    best = (-1, 0)
    for ph in range(T):
        s = 0
        rng = range(ph, W, T) if axis == "x" else range(ph, H, T)
        for i in rng:
            if i == 0:
                continue
            if axis == "x":
                s += sum(abs(px[i, y][k] - px[i - 1, y][k])
                         for y in range(0, H, step) for k in range(3))
            else:
                s += sum(abs(px[x, i][k] - px[x, i - 1][k])
                         for x in range(0, W, step) for k in range(3))
        if s > best[0]:
            best = (s, ph)
    return best[1]


def block_median(px, x0, y0, T, W, H):
    """块内中位色。均值会把块边界糊掉，中位对噪声和跨界像素都稳。"""
    ch = [[], [], []]
    for y in range(y0, min(y0 + T, H)):
        for x in range(x0, min(x0 + T, W)):
            c = px[x, y]
            for k in range(3):
                ch[k].append(c[k])
    return tuple(int(statistics.median(v)) for v in ch)


def snap(im, T, phx, phy):
    px = im.load(); W, H = im.size
    ow, oh = (W - phx) // T, (H - phy) // T
    out = Image.new("RGB", (ow, oh))
    op = out.load()
    for j in range(oh):
        for i in range(ow):
            op[i, j] = block_median(px, phx + i * T, phy + j * T, T, W, H)
    return out


def kill_checker(im, tol=12):
    """棋盘格底 = 两种相近的浅灰交替。从四边泛洪，两种都吃。

    只泛洪、不全图删 —— 角色内部同色的地方（眼白、白衬衫）要留住。"""
    im = im.convert("RGBA"); W, H = im.size; px = im.load()
    corners = [px[0, 0][:3], px[W - 1, 0][:3], px[0, H - 1][:3], px[W - 1, H - 1][:3]]
    bg = list({c for c in corners})
    # 角上可能只采到棋盘格的一种，补上另一种：找和它相近但不同的边缘色
    edge = Counter(px[x, y][:3] for x in range(W) for y in (0, H - 1))
    edge.update(px[x, y][:3] for y in range(H) for x in (0, W - 1))
    for c, _ in edge.most_common(4):
        if all(sum(abs(a - b) for a, b in zip(c, g)) > tol for g in bg) and len(bg) < 2:
            if sum(c) > 600:
                bg.append(c)

    def is_bg(c):
        return any(all(abs(c[k] - g[k]) <= tol for k in range(3)) for g in bg)

    seen = [[False] * H for _ in range(W)]
    q = deque([(x, y) for x in range(W) for y in (0, H - 1)] +
              [(x, y) for y in range(H) for x in (0, W - 1)])
    n = 0
    while q:
        x, y = q.popleft()
        if not (0 <= x < W and 0 <= y < H) or seen[x][y]:
            continue
        if not is_bg(px[x, y][:3]):
            continue
        seen[x][y] = True
        px[x, y] = (0, 0, 0, 0); n += 1
        q.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])
    return im, bg, n


def quantize(im, n):
    """只量化不透明像素。dither 关掉 —— 抖动会毁掉平涂。"""
    rgb = im.convert("RGB")
    q = rgb.quantize(colors=n, method=Image.MEDIANCUT, dither=Image.Dither.NONE)
    out = q.convert("RGBA")
    op, ip = out.load(), im.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            if ip[x, y][3] == 0:
                op[x, y] = (0, 0, 0, 0)
    return out


def bands(empty, n, min_gap):
    spans, s = [], None
    for i in range(n):
        if not empty[i] and s is None:
            s = i
        elif empty[i] and s is not None:
            if all(empty[j] for j in range(i, min(i + min_gap, n))):
                spans.append((s, i - 1)); s = None
    if s is not None:
        spans.append((s, n - 1))
    return spans


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src"); ap.add_argument("outdir")
    ap.add_argument("--period", type=int, default=0, help="块边长，0=自动测")
    ap.add_argument("--colors", type=int, default=0, help="量化色数，0=不量化")
    ap.add_argument("--split", default="", help="切成几行几列，例 2x4")
    ap.add_argument("--tol", type=int, default=12, help="底色容差")
    a = ap.parse_args()

    im = Image.open(a.src).convert("RGB")
    W, H = im.size; px = im.load()
    print(f"原图 {W}×{H}，{len(set(px[x, y] for y in range(0, H, 2) for x in range(0, W, 2)))} 色")

    T = a.period or min(detect_period(energy(px, W, H, "x")),
                        detect_period(energy(px, W, H, "y")))
    phx = detect_phase(px, W, H, T, "x")
    phy = detect_phase(px, W, H, T, "y")
    print(f"块边长 {T}，相位 x={phx} y={phy}")

    grid = snap(im, T, phx, phy)
    print(f"点阵 {grid.size[0]}×{grid.size[1]}"
          f"，{len(set(grid.getdata()))} 色")

    rgba, bg, ncut = kill_checker(grid, a.tol)
    print(f"底色 {bg} —— 泛洪透明 {ncut} 像素")

    if a.colors:
        rgba = quantize(rgba, a.colors)
        opaque = {c[:3] for c in rgba.getdata() if c[3]}
        print(f"量化到 {a.colors} 色，实际 {len(opaque)} 色")

    os.makedirs(a.outdir, exist_ok=True)
    rgba.save(os.path.join(a.outdir, "点阵.png"))

    if a.split:
        r, c = (int(v) for v in a.split.lower().split("x"))
        p = rgba.load(); GW, GH = rgba.size
        rempty = [all(p[x, y][3] == 0 for x in range(GW)) for y in range(GH)]
        rows = bands(rempty, GH, 3)
        cells = []
        for y0, y1 in rows:
            cempty = [all(p[x, y][3] == 0 for y in range(y0, y1 + 1)) for x in range(GW)]
            for x0, x1 in bands(cempty, GW, 3):
                cells.append((x0, y0, x1, y1))
        print(f"切格：期望 {r}×{c}={r*c}，实际找到 {len(cells)}")
        for i, (x0, y0, x1, y1) in enumerate(cells):
            sub = rgba.crop((x0, y0, x1 + 1, y1 + 1))
            sub.save(os.path.join(a.outdir, f"{i:02d}.png"))
            print(f"   {i:02d}.png  {sub.size[0]}×{sub.size[1]}  @({x0},{y0})")


if __name__ == "__main__":
    main()
