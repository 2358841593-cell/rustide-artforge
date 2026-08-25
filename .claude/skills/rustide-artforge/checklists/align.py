#!/usr/bin/env python3
"""把网格切出来的帧按「脚底贴地 + 水平居中」对齐到统一画布。
游戏 sprite 的标准锚点。用法: align.py <网格图> <列> <行> <输出目录> <目标高px>
"""
import sys, os, subprocess, tempfile
sys.dont_write_bytecode = True
from PIL import Image

def bbox(im):
    px = im.convert("RGB").load(); W, H = im.size
    xs, ys = [], []
    for y in range(H):
        for x in range(W):
            if sum(px[x, y]) < 720:
                xs.append(x); ys.append(y)
    return (min(xs), min(ys), max(xs)+1, max(ys)+1) if xs else None

def main():
    src, cols, rows, out, target = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], int(sys.argv[5])
    os.makedirs(out, exist_ok=True)
    im = Image.open(src).convert("RGB"); W, H = im.size
    cw, ch = W // cols, H // rows

    cells = {}
    for r in range(rows):
        for c in range(cols):
            cell = im.crop((c*cw, r*ch, (c+1)*cw, (r+1)*ch))
            b = bbox(cell)
            if b: cells[(r, c)] = cell.crop(b)

    # 统一尺度：以所有帧里最高的那个定缩放比，保证角色等大
    maxh = max(v.size[1] for v in cells.values())
    scale = target / maxh
    canvas_w = int(max(v.size[0] for v in cells.values()) * scale) + 4
    canvas_h = target + 2

    for (r, c), sp in cells.items():
        w2, h2 = max(1, round(sp.size[0]*scale)), max(1, round(sp.size[1]*scale))
        sp = sp.resize((w2, h2), Image.NEAREST)
        canv = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))
        # 锚点：水平居中 + 脚底贴画布底部（留 1px）
        canv.paste(sp, ((canvas_w - w2)//2, canvas_h - h2 - 1))
        canv = canv.quantize(colors=10, dither=Image.NONE).convert("RGB")
        canv.save(f"{out}/r{r}c{c}.png")
    print(f"{len(cells)} 帧 → {canvas_w}x{canvas_h}，统一缩放 {scale:.3f}")

main()
