#!/usr/bin/env python3
"""从四张静态 sprite 程序化生成基础动作，并拼出总表 + 清单。

动作都是**整段位移**，和 walkgen 同一套路：靴子以上算躯干，躯干位移，
靴子留在地上。这样不需要重画，也不会出现 AI 逐帧重绘的抖动。

  待机 idle      2 帧  躯干抬 1px —— 呼吸
  互动 interact  3 帧  躯干后仰 1px 蓄力 → 前探 2px
  受击 hurt      2 帧  整体朝背面退 2px 并闪白 → 退 1px 复原
  打招呼 wave    4 帧  设计稿里真画出来的举手姿势，小臂左右摆

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


def skin_color(im):
    """肤色 = 调色板里最亮的暖色（R 明显大于 B）。"""
    px = im.load(); W, H = im.size
    cand = [px[x, y][:3] for y in range(H) for x in range(W)
            if px[x, y][3] and px[x, y][0] > px[x, y][2] + 20]
    return max(cand, key=sum) if cand else None


def find_hand(base):
    """脸以下的肤色**连通簇**里，挑最外侧的那个小簇 = 手。

    不能对所有肤色点取总包围盒 —— 下巴和手会被圈成一大块，
    整个胸口都会被当成手搬走（第一版就是这么坏的）。"""
    from collections import deque
    px = base.load(); W, H = base.size
    sk = skin_color(base)
    if sk is None:
        return None
    bx0, by0, bx1, by1 = body_box(base)
    # 实测四个方向：手一律落在 y35~37，下巴/脖子的肤色簇在 y27~31。
    # 阈值 0.55 会把下巴放进来（侧视图就是这么把脸当成手搬走的），收到 0.72。
    ymin = by0 + int((by1 - by0) * 0.72)
    seen = set(); clusters = []
    for y in range(ymin, H):
        for x in range(W):
            if px[x, y][3] and px[x, y][:3] == sk and (x, y) not in seen:
                q = deque([(x, y)]); seen.add((x, y)); c = []
                while q:
                    a, b = q.popleft(); c.append((a, b))
                    for na, nb in ((a+1,b),(a-1,b),(a,b+1),(a,b-1),
                                   (a+1,b+1),(a-1,b-1),(a+1,b-1),(a-1,b+1)):
                        if (ymin <= nb < H and 0 <= na < W and px[na,nb][3]
                                and px[na,nb][:3] == sk and (na,nb) not in seen):
                            seen.add((na,nb)); q.append((na,nb))
                clusters.append(c)
    cx = (bx0 + bx1) / 2
    # 手是小簇（脸的下半部分会连成大簇），且离中线远
    hands = [c for c in clusters if len(c) <= 12]
    if not hands:
        return None
    best = max(hands, key=lambda c: abs(sum(p[0] for p in c)/len(c) - cx))
    xs = [p[0] for p in best]; ys = [p[1] for p in best]
    return min(xs), max(xs), min(ys), max(ys)


def sleeve_color(base, hand):
    """手正上方那两行的主色 —— 用来把手原来的位置补掉。"""
    from collections import Counter
    px = base.load()
    x0, x1, y0, _ = hand
    c = Counter(px[x, y][:3] for y in range(max(0, y0 - 3), y0)
                for x in range(x0, x1 + 1) if px[x, y][3])
    return c.most_common(1)[0][0] if c else None


# ⚠️ 抬手不能靠程序化位移凑 —— 两条路都试过并且都失败了：
#   1. 位移「手 + 一截袖子」往上 → 出来是**耸肩**，袖子整块上移手还在下面。
#   2. 按袖色/肤色/描边色现画一条 2px 小臂 → 出来是一根**悬空的黑棍**，
#      那个高度身体外沿是头发，胳膊落在空隙里接不上肩。
# 根因：位移只能搬运已有像素，抬手必须让胳膊伸到剪影**外面**去。
# 通用判据：凡是要改变剪影的动作，都只能回设计稿加姿势。
# 所以 wave 是设计稿里真画出来的第五个姿势，这里只负责让它摆动。


def wave_arm(front, wave):
    """举起的胳膊 = 「wave 有、正面姿势没有」的那块像素里最大的连通簇。

    两张图是分开画的，整体有 ~46% 的重绘噪声，但**新增的不透明像素**
    能干净地圈出胳膊（实测 x4..7 y17..26，其余是零星噪点）。"""
    from collections import deque
    pf, pw = front.load(), wave.load()
    W, H = wave.size
    new = {(x, y) for y in range(H) for x in range(W)
           if pw[x, y][3] and not pf[x, y][3]}
    seen = set(); best = []
    for s in new:
        if s in seen:
            continue
        q = deque([s]); seen.add(s); c = []
        while q:
            x, y = q.popleft(); c.append((x, y))
            for n in ((x+1,y),(x-1,y),(x,y+1),(x,y-1),
                      (x+1,y+1),(x-1,y-1),(x+1,y-1),(x-1,y+1)):
                if n in new and n not in seen:
                    seen.add(n); q.append(n)
        if len(c) > len(best):
            best = c
    if not best:
        return None
    xs = [p[0] for p in best]; ys = [p[1] for p in best]
    return min(xs), max(xs), min(ys), max(ys)


def tilt_arm(wave, arm, dx):
    """把小臂上半截横移 dx —— 肘部不动，读出来是挥手。"""
    if arm is None or dx == 0:
        return wave
    x0, x1, y0, y1 = arm
    W, H = wave.size
    cut = y0 + int((y1 - y0) * 0.6)          # 肘部：这一行以下不动
    out = wave.copy(); px = out.load(); bp = wave.load()
    block = [(x, y, bp[x, y]) for y in range(y0, cut + 1)
             for x in range(max(0, x0 - 1), min(W, x1 + 2)) if bp[x, y][3]]
    for x, y, _ in block:
        px[x, y] = (0, 0, 0, 0)
    for x, y, c in block:
        if 1 <= x + dx < W - 1:
            px[x + dx, y] = c
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

    # 打招呼用设计稿里那张正面举手姿势 —— 四个朝向共用一张：
    # 角色跟你打招呼时会转过来面对你，这是常见做法。
    wave_png = os.path.join(a.spritedir, "wave.png")
    if not os.path.exists(wave_png):
        raise SystemExit("✗ 缺 wave.png —— spritecut 时要带 --names dir0,dir1,dir2,dir3,wave")
    wv = Image.open(wave_png).convert("RGBA")
    arm = wave_arm(bases[0], wv)
    if arm is None:
        raise SystemExit("✗ 在 wave.png 里找不到举起的胳膊（和正面姿势没有新增像素）")
    print(f"举手的小臂 x[{arm[0]}..{arm[1]}] y[{arm[2]}..{arm[3]}]")
    wave_frames = [wv, tilt_arm(wv, arm, -1), wv, tilt_arm(wv, arm, 1)]
    for d in range(4):
        acts[d]["wave"] = wave_frames

    # 列顺序固定：walk 4 + idle 2 + interact 3 + hurt 2 + wave 4 = 15
    order = [("walk", 4), ("idle", 2), ("interact", 3), ("hurt", 2), ("wave", 4)]
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
    clips["wave"].update(fps=7, loop=False)

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
