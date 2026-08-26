#!/usr/bin/env python3
"""从四张静态 sprite 程序化生成基础动作，并拼出总表 + 清单。

动作都是**整段位移**，和 walkgen 同一套路：靴子以上算躯干，躯干位移，
靴子留在地上。这样不需要重画，也不会出现 AI 逐帧重绘的抖动。

  待机 idle      2 帧  躯干抬 1px —— 呼吸
  互动 interact  3 帧  躯干后仰 1px 蓄力 → 前探 2px
  受击 hurt      2 帧  整体朝背面退 2px 并闪白 → 退 1px 复原

输出 spritesheet.png（11 列 × 4 行）和 anim.json，游戏端照 json 播即可。

用法: actiongen.py <sprite目录> <anim目录>
      sprite目录里要有 dir0..3.png
      anim 目录里要先有 walkgen 出的 walk_dir{0-3}_f{0-3}.png，动作和总表也写这里
"""
import sys, os, json, argparse
sys.dont_write_bytecode = True
from PIL import Image
from walkgen import body_box, boot_top

# 每个方向的「朝向」单位向量：前=下、后=上、左、右
FACING = {0: (0, 1), 1: (0, -1), 2: (-1, 0), 3: (1, 0)}
DIRNAMES = ["down", "up", "left", "right"]


def shift_torso(base, legs_top, dx, dy):
    """靴子以上整段位移，靴子留在原地。空出来的腰部用腿区顶行拉伸补上。"""
    W, H = base.size
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    torso = base.crop((0, 0, W, legs_top))
    out.paste(torso, (dx, dy), torso)
    if dy < 0:                       # 躯干抬起来，腰上留了缝
        strip = base.crop((0, legs_top, W, legs_top + 1))
        for i in range(-dy):
            out.paste(strip, (dx, legs_top + dy + i), strip)
    boots = base.crop((0, legs_top, W, H))
    out.paste(boots, (0, legs_top), boots)
    return out


def shift_all(base, dx, dy):
    W, H = base.size
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.paste(base, (dx, dy), base)
    return out


def flash(im, amt):
    """朝白色混合，受击的那一下。"""
    out = im.copy(); px = out.load(); W, H = out.size
    for y in range(H):
        for x in range(W):
            r, g, b, a = px[x, y]
            if a:
                px[x, y] = (round(r + (255 - r) * amt),
                            round(g + (255 - g) * amt),
                            round(b + (255 - b) * amt), a)
    return out


def build(base, d):
    """返回 {动作名: [帧,...]}"""
    legs_top, _ = boot_top(base)
    fx, fy = FACING[d]
    return {
        "idle": [base,
                 shift_torso(base, legs_top, 0, -1)],
        "interact": [base,
                     shift_torso(base, legs_top, -fx, -fy),          # 蓄力后仰
                     shift_torso(base, legs_top, fx * 2, fy * 2)],   # 前探
        "hurt": [flash(shift_all(base, -fx * 2, -fy * 2), 0.65),     # 退 2 + 闪白
                 shift_all(base, -fx, -fy)],                          # 退 1 复原
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spritedir"); ap.add_argument("animdir")
    a = ap.parse_args()

    bases = [Image.open(f"{a.spritedir}/dir{d}.png").convert("RGBA") for d in range(4)]
    FW, FH = bases[0].size
    walk = [[Image.open(f"{a.animdir}/walk_dir{d}_f{f}.png").convert("RGBA")
             for f in range(4)] for d in range(4)]
    acts = [build(bases[d], d) for d in range(4)]

    # 列顺序固定：walk 4 + idle 2 + interact 3 + hurt 2 = 11
    order = [("walk", 4), ("idle", 2), ("interact", 3), ("hurt", 2)]
    cols = sum(n for _, n in order)
    sheet = Image.new("RGBA", (FW * cols, FH * 4), (0, 0, 0, 0))
    clips, c0 = {}, 0
    for name, n in order:
        clips[name] = {"from": c0, "count": n}
        for d in range(4):
            frames = walk[d] if name == "walk" else acts[d][name]
            for i in range(n):
                sheet.alpha_composite(frames[i], ((c0 + i) * FW, d * FH))
        c0 += n

    clips["walk"].update(fps=8, loop=True, driver="distance", stepPx=4)
    clips["idle"].update(fps=1.4, loop=True)
    clips["interact"].update(fps=10, loop=False)
    clips["hurt"].update(fps=12, loop=False)

    os.makedirs(a.animdir, exist_ok=True)
    sheet.save(f"{a.animdir}/spritesheet.png")
    for d in range(4):
        for name, _ in order[1:]:
            for i, f in enumerate(acts[d][name]):
                f.save(f"{a.animdir}/{name}_dir{d}_f{i}.png")

    manifest = {"cell": [FW, FH],
                "rows": {n: i for i, n in enumerate(DIRNAMES)},
                "clips": clips}
    with open(f"{a.animdir}/anim.json", "w") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)

    # 门禁：位移过的帧也不能顶到画布边
    px = sheet.load(); bad = 0
    for cx in range(cols):
        for d in range(4):
            for yy in range(FH):
                for xx in range(FW):
                    if (xx in (0, FW - 1) or yy in (0, FH - 1)) and px[cx * FW + xx, d * FH + yy][3]:
                        bad += 1
    print(f"总表 {sheet.size[0]}×{sheet.size[1]}  {cols} 列 × 4 行  单帧 {FW}×{FH}")
    for name, spec in clips.items():
        print(f"  {name:<9} 列 {spec['from']}..{spec['from']+spec['count']-1}  "
              f"{spec['count']} 帧  fps {spec['fps']}  {'循环' if spec['loop'] else '单次'}")
    print(f"顶边像素 {bad} " + ("✓" if bad == 0 else "✗ 位移把角色推出画布了，收小位移或加大格子"))
    if bad:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
