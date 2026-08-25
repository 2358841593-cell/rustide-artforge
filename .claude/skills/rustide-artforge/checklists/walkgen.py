#!/usr/bin/env python3
"""从一张静态 sprite 程序化生成行走帧。
在 40px 尺度下腿只有 4-6 像素，位移法比重画可靠得多，且**零抖动**。
用法: walkgen.py <静态sprite.png> <输出目录> <前缀>
"""
import sys, os
sys.dont_write_bytecode = True
from PIL import Image

BG = (255, 255, 255)

def load(p):
    return Image.open(p).convert("RGB")

def body_rows(im):
    """找出角色占据的行范围"""
    px = im.load(); W, H = im.size
    rows = [y for y in range(H) if any(sum(px[x, y]) < 720 for x in range(W))]
    return (min(rows), max(rows)) if rows else (0, H-1)

def make_frame(base, leg_frac, dx, bob):
    """leg_frac: 腿部区域占身高的比例（从底部往上）
       dx: 左腿右移 dx，右腿左移 dx（正数=迈开）
       bob: 整体上移像素"""
    W, H = base.size
    top, bot = body_rows(base)
    legs_top = bot - int((bot - top) * leg_frac)
    # 先整张铺基底，位移的腿叠在上面 —— 这样错位处不会露出背景
    out = base.copy()

    if bob:
        out = Image.new("RGB", (W, H), BG)
        out.paste(base, (0, -bob))

    legs = out.crop((0, legs_top, W, H))
    lw = legs.size[0] // 2
    left  = legs.crop((0, 0, lw, legs.size[1]))
    right = legs.crop((lw, 0, legs.size[0], legs.size[1]))
    # 叠在原腿之上，露出来的那一列仍是基底内容，不会变白
    out.paste(left,  (dx, legs_top))
    out.paste(right, (lw - dx, legs_top))
    return out

def main():
    base = load(sys.argv[1]); out = sys.argv[2]; pre = sys.argv[3]
    os.makedirs(out, exist_ok=True)
    # 三帧：左脚出 / 并脚(基底) / 右脚出
    frames = [make_frame(base, 0.28, 1, 0),   # 左脚出
              base,                            # 并脚，身体高 1px
              make_frame(base, 0.28, -1, 0)]  # 右脚出
    for i, f in enumerate(frames):
        f.save(f"{out}/{pre}_f{i}.png")
    print(f"{pre}: 3 帧已生成")

main()
