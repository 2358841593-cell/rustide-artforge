#!/usr/bin/env python3
"""从一张静态 sprite 程序化生成 4 帧行走循环。

v2 修掉了 v1 的三个硬伤：
  1. v1 先铺整张基底再把位移的腿盖上去 —— **原来的腿一直露在下面**，
     腿不是迈开，只是变宽 1px。所以看着像抖不像走。
     v2 把腿整块抠走，在透明画布上重新摆位，腿离开的地方就是背景。
  2. v1 只有 3 帧且第 2 帧 == 原图，注释写着"身体高 1px"但代码没做，
     四个方向里只有一个意外有起伏。v2 是标准 4 帧 接地/过渡/接地/过渡，
     过渡帧身体真的抬起来，并用一条拉伸带补住腰部接缝。
  3. v1 只横移腿。40px 尺度下横移 1px 看不出来，v2 抬腿（y 位移）为主。

两条腿在 40~48px 尺度下是连在一起的一整块，连通域分不开，
所以按**谷底列**（腿间空隙）劈开。

用法: walkgen.py <sprite.png> <输出目录> <前缀> [--legtop N] [--shift 1] [--lift 1] [--bob 1]
"""
import sys, os, argparse
sys.dont_write_bytecode = True
from PIL import Image


def body_box(im):
    px = im.load(); W, H = im.size
    ys = [y for y in range(H) for x in range(W) if px[x, y][3]]
    xs = [x for y in range(H) for x in range(W) if px[x, y][3]]
    return min(xs), min(ys), max(xs), max(ys)


def _runs(px, y, W, minlen=2):
    """这一行里连续不透明的段，短于 minlen 的当噪点丢掉。"""
    out, s = [], None
    for x in range(W + 1):
        on = x < W and px[x, y][3]
        if on and s is None:
            s = x
        elif not on and s is not None:
            if x - s >= minlen:
                out.append((s, x - 1))
            s = None
    return out


def boot_top(im):
    """自动找靴子区顶行：从底往上，只要这一行还**分得出两条腿**就继续。

    早先用「宽度不超过底部两行均宽的 1.35 倍」判断，是脆的 —— 换一张
    设计稿，大衣衣摆那行宽度刚好卡在阈值上就被当成靴子，横移时又把
    衣摆劈成两半（新版 5 姿势稿实测就踩中了：y38 衣摆宽 16，阈值 16.2）。
    腿分不分得开是这件事的本质，按这个判断跟画风无关。"""
    px = im.load(); W, H = im.size
    rows = [y for y in range(H) if any(px[x, y][3] for x in range(W))]
    bot = max(rows)
    y = bot
    while y - 1 >= 0 and len(_runs(px, y - 1, W)) >= 2:
        y -= 1
    if y == bot:                      # 一条腿都分不开（长袍之类），退回底部四行
        y = max(rows[0], bot - 3)
    return y, bot


def valley_column(im, legs_top):
    """腿区里不透明像素最少的那一列 —— 两腿之间的空隙。
    只在中间三分之一里找，免得劈到身体外沿。"""
    px = im.load(); W, H = im.size
    x0, _, x1, _ = body_box(im)
    lo, hi = x0 + (x1 - x0) // 3, x1 - (x1 - x0) // 3
    best, bestn = (x0 + x1) // 2, 10 ** 9
    for x in range(lo, hi + 1):
        n = sum(1 for y in range(legs_top, H) if px[x, y][3])
        if n < bestn:
            best, bestn = x, n
    return best


def compose(base, legs_top, moves, bob):
    """moves: [(x起, x止, dx, dy), ...] 每块腿各自位移。
    躯干整体上抬 bob，腰部空出的 bob 行用腿区顶行拉伸补上，避免断腰。"""
    W, H = base.size
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    torso = base.crop((0, 0, W, legs_top))
    out.paste(torso, (0, -bob), torso)

    if bob:
        strip = base.crop((0, legs_top, W, legs_top + 1))
        for i in range(bob):
            out.paste(strip, (0, legs_top - bob + i), strip)

    for xa, xb, dx, dy in moves:
        piece = base.crop((xa, legs_top, xb, H))
        out.paste(piece, (xa + dx, legs_top + dy), piece)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sprite"); ap.add_argument("outdir"); ap.add_argument("prefix")
    ap.add_argument("--legtop", type=int, default=-1,
                    help="腿区顶行，-1 = 自动识别靴子")
    ap.add_argument("--shift", type=int, default=1, help="迈步横向位移")
    ap.add_argument("--lift", type=int, default=1, help="抬腿高度")
    ap.add_argument("--bob", type=int, default=1, help="过渡帧身体抬高")
    a = ap.parse_args()

    base = Image.open(a.sprite).convert("RGBA")
    if not any(base.load()[x, y][3] == 0
               for y in range(base.size[1]) for x in range(base.size[0])):
        raise SystemExit("✗ 输入 sprite 没有透明像素 —— 先过 spritecut.py")

    W, H = base.size
    auto_top, bot = boot_top(base)
    legs_top = auto_top if a.legtop < 0 else a.legtop
    vx = valley_column(base, legs_top)
    s, L, b = a.shift, a.lift, a.bob
    print(f"{a.prefix}: 靴区 y{legs_top}..{bot}，谷底列 x={vx}")

    Lg = (0, vx, 0, 0)          # 左腿块占位模板
    Rg = (vx, W, 0, 0)
    def legs(ldx, ldy, rdx, rdy):
        return [(Lg[0], Lg[1], ldx, ldy), (Rg[0], Rg[1], rdx, rdy)]

    # 抬起的那条腿**向内收**，另一条踩住不动。
    # 早先是一帧把两腿并拢 (+s,-s)、一帧把两腿撇开 (-s,+s)，一个循环里
    # 间隙摆动 6px，走起来是罗圈腿。腿真正迈步时是往身体下方收的，
    # 不是向外撇 —— 现在间隙只会变窄，不会变宽。
    frames = [
        compose(base, legs_top, legs(+s, -L, 0,  0), b),  # f0 抬左腿内收，身体起
        compose(base, legs_top, legs(0,   0, 0,  0), 0),  # f1 双脚着地
        compose(base, legs_top, legs(0,   0, -s, -L), b), # f2 抬右腿内收，身体起
        compose(base, legs_top, legs(0,   0, 0,  0), 0),  # f3 双脚着地
    ]
    os.makedirs(a.outdir, exist_ok=True)
    prev = None
    for i, f in enumerate(frames):
        f.save(f"{a.outdir}/{a.prefix}_f{i}.png")
        if prev is not None:
            d = sum(1 for y in range(H) for x in range(W)
                    if f.load()[x, y] != prev.load()[x, y])
            print(f"   f{i-1}→f{i} 差异 {d}/{W*H} ({d/(W*H):.1%})")
        prev = f
    print(f"{a.prefix}: 4 帧已生成")


if __name__ == "__main__":
    main()
