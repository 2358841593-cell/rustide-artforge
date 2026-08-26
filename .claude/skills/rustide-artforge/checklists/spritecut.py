#!/usr/bin/env python3
"""把 sprite 设计稿切成带透明底、留边距的像素帧。

和旧管线的两处关键区别：
  1. 抠图在**全分辨率**做完再降采样 —— 那时角色四周还有大片背景，
     边界泛洪能一次刷干净，不需要任何亮度阈值（骨白衣物再也不会被吃）。
  2. 角色是**装进**格子而不是裁进格子 —— 等比缩放到内框，底部居中贴进
     透明画布，四周留出边距。旧管线 -resize x40 后直接裁 24 宽，
     头发和肩膀顶死在画布壁上，泛洪进不去，白洞永远刷不掉。

用法: spritecut.py <设计稿.png> <输出目录> [--cell 32x48] [--colors 16]
"""
import sys, os, argparse
sys.dont_write_bytecode = True
from collections import deque
from PIL import Image

PAD_X = 2          # 左右各留的最小边距
PAD_TOP = 2        # 头顶留白
PAD_BOT = 2        # 脚下留白（落地基线在 CH-PAD_BOT-1）


def background_mask(im):
    """全分辨率边界泛洪，返回 True=背景 的位图。"""
    W, H = im.size
    px = im.load()
    mask = bytearray(W * H)
    def is_bg(c):
        return c[0] > 238 and c[1] > 238 and c[2] > 235
    dq = deque([(x, y) for x in range(W) for y in (0, H - 1)] +
               [(x, y) for y in range(H) for x in (0, W - 1)])
    while dq:
        x, y = dq.popleft()
        if not (0 <= x < W and 0 <= y < H) or mask[y * W + x]:
            continue
        if not is_bg(px[x, y]):
            continue
        mask[y * W + x] = 1
        dq.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    return mask


def split_columns(im, mask, min_gap=15):
    """按空白列带把并排的几个角色分开。"""
    W, H = im.size
    empty = [all(mask[y * W + x] for y in range(H)) for x in range(W)]
    spans, start = [], None
    for x in range(W):
        if not empty[x] and start is None:
            start = x
        elif empty[x] and start is not None:
            if all(empty[i] for i in range(x, min(x + min_gap, W))):
                spans.append((start, x - 1)); start = None
    if start is not None:
        spans.append((start, W - 1))
    return spans


def bbox(mask, W, x0, x1, H):
    xs, ys = [], []
    for y in range(H):
        row = y * W
        for x in range(x0, x1 + 1):
            if not mask[row + x]:
                xs.append(x); ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


def cut(im, mask, box, scale, cell):
    """裁出角色 → 面积平均降采样 → alpha 二值化 → 底部居中贴进透明画布。"""
    CW, CH = cell
    x0, y0, x1, y1 = box
    W, _ = im.size
    sub = im.crop((x0, y0, x1 + 1, y1 + 1)).convert("RGBA")
    sp = sub.load()
    for yy in range(sub.size[1]):
        for xx in range(sub.size[0]):
            if mask[(y0 + yy) * W + (x0 + xx)]:
                sp[xx, yy] = (0, 0, 0, 0)

    tw = max(1, round((x1 - x0 + 1) * scale))
    th = max(1, round((y1 - y0 + 1) * scale))
    # 面积平均比最近邻保形好得多（最近邻 10 倍降采样会整只眼睛丢掉），
    # 抗锯齿随后被调色板量化削掉，仍是硬边真像素。
    small = sub.resize((tw, th), Image.BOX)
    px = small.load()
    for yy in range(th):
        for xx in range(tw):
            r, g, b, a = px[xx, yy]
            px[xx, yy] = (r, g, b, 255 if a >= 128 else 0)

    canvas = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    canvas.paste(small, ((CW - tw) // 2, CH - PAD_BOT - th), small)
    return canvas


def quantize(im, n):
    """只对不透明像素做调色板量化，透明区不参与。"""
    rgb = im.convert("RGB")
    q = rgb.quantize(colors=n, method=Image.MEDIANCUT, dither=Image.Dither.NONE)
    out = q.convert("RGBA")
    op, ip = out.load(), im.load()
    W, H = im.size
    for y in range(H):
        for x in range(W):
            if ip[x, y][3] == 0:
                op[x, y] = (0, 0, 0, 0)
    return out


def verify(im, name):
    """门禁：最外圈 1px 必须全透明，否则角色被画布切了。"""
    W, H = im.size
    px = im.load()
    bad = [(x, y) for y in range(H) for x in range(W)
           if (x in (0, W - 1) or y in (0, H - 1)) and px[x, y][3]]
    if bad:
        raise SystemExit(f"✗ {name}: {len(bad)} 个不透明像素顶在画布边上，"
                         f"角色被切了 —— 调大 --cell 或边距后重跑")
    xs = [x for y in range(H) for x in range(W) if px[x, y][3]]
    ys = [y for y in range(H) for x in range(W) if px[x, y][3]]
    return (min(xs), min(ys), max(xs), max(ys))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet"); ap.add_argument("outdir")
    ap.add_argument("--cell", default="32x48")
    ap.add_argument("--colors", type=int, default=16)
    ap.add_argument("--names", default="dir0,dir1,dir2,dir3")
    a = ap.parse_args()

    CW, CH = (int(v) for v in a.cell.lower().split("x"))
    cell = (CW, CH)
    names = a.names.split(",")

    im = Image.open(a.sheet).convert("RGB")
    W, H = im.size
    mask = background_mask(im)
    spans = split_columns(im, mask)
    if len(spans) != len(names):
        raise SystemExit(f"✗ 设计稿里找到 {len(spans)} 个角色，但给了 {len(names)} 个名字：{spans}")

    boxes = [bbox(mask, W, x0, x1, H) for x0, x1 in spans]
    # 四个方向必须共用同一个缩放比，否则朝向一换人就变大变小
    inner_w, inner_h = CW - PAD_X * 2, CH - PAD_TOP - PAD_BOT
    scale = min(min(inner_w / (b[2] - b[0] + 1), inner_h / (b[3] - b[1] + 1)) for b in boxes)

    os.makedirs(a.outdir, exist_ok=True)
    print(f"格子 {CW}×{CH}，内框 {inner_w}×{inner_h}，统一缩放 {scale:.4f}")
    for name, box in zip(names, boxes):
        f = quantize(cut(im, mask, box, scale, cell), a.colors)
        bb = verify(f, name)
        f.save(os.path.join(a.outdir, f"{name}.png"))
        solid = sum(1 for y in range(CH) for x in range(CW) if f.load()[x, y][3])
        print(f"  {name}.png  剪影 x[{bb[0]}..{bb[2]}] y[{bb[1]}..{bb[3]}] "
              f"({bb[2]-bb[0]+1}×{bb[3]-bb[1]+1})  不透明 {solid}/{CW*CH}  ✓边距合格")


main()
