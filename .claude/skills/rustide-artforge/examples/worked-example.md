# 填空示范

> 这份是 `templates/GOLD-from-scratch.txt` **填好占位符之后**的样子。
> **段落结构与模板逐字一致** —— 范例的权重压过规则，结构一旦漂移就会污染后续生成（实测踩过两次）。

## 假想输入

一张照片：三十上下的男性，短寸头，黑框圆眼镜，络腮胡不长但明显，眼小眉浓，体型敦实，肤色偏白，
穿灰色连帽卫衣 + 牛仔裤，左手戴一块旧机械表。

## 七步怎么填

| 步骤 | 结论 |
|---|---|
| A 桶硬锚点 | 短寸头 · **圆眼镜 + 络腮胡（双重遮挡）** · 敦实 · 瓷肤 · 连帽衫+牛仔裤 |
| B 桶夸张（≤2） | **眉极浓** → 两条几乎连成一条的粗色块；**眼小** → 镜片后两个小豆点 |
| 世界观四问 | 釜谷出身 · 接线人 · 汛期照常出门修东西 · 左手小指是自接的黄铜义指（伤疤） |
| 服装改造 | 灰卫衣 → 骨白旧毛线连帽衫（帽绳换成旧世电线）；牛仔裤 → 灰卡其工装裤塞进大靴 |
| 压倒性元素 | **外扩过胯的灼橙油布围裙外套**（选照片里独有的廓形，不选头发） |
| 细节配方 | 接线人 = 线缆卷 / 插头 / 绝缘带 / 小工具，**不是通用徽章**；成人工匠档 15–20 个 |
| 配色 1+2+1 | 灼橙 `#EA9056` ＋ 灰卡其 `#9F946B`、骨白 `#F1DEA9` ＋ 汽笛蓝 `#02758F` |

## 填好的提示词

```text
A 1990s hand-inked animation model sheet, cel-painted on acetate. Single full-body character,
front view, plain white background.

Same drawing style and proportions as the reference sheets. A different person.

BUILD: big head, stocky body, five heads tall. Wide padded shoulders are widest. Head as
tall as boots; thin legs only two heads long; boots huge and square. A patient Kettle
prosthetics-fitter, soldering iron in one hand.

CURVE: every edge is a slightly uneven curve. Sleeves bow, hems wave, trouser sides splay, the
jaw rounds.

LINE: moderate warm dark brown #2E241F brush lines, silhouette twice the interior weight.

SKIN: pale pink-beige #F5E0BC with one shadow #DCC29B. The skin stays pale.

PHOTO-LOCK: from the photo the face keeps only these traits, amplified — a round face, small narrow eyes, extremely thick brows, a broad plain nose, pale skin.
Limb thickness follows the photo: thick forearms.
The face and body carry these traits and these alone. The style reference sheets supply
drawing technique only.

FACE: ink-dark cropped hair in solid lobes; round-framed glasses and a short full beard cover
most of it. Two extremely thick brows almost meet and press on the glasses rim. Behind the
lenses the eyes are two tiny dots. Mouth a short line, hard blush ovals, one lens frosted over.

CLOTHES (a scavenged version of what the photo wears): a teal high-neck, a bone-white knit
hooded shirt with an old-world wire for a drawstring, a long ember-orange oilcloth apron-coat,
wide ash-khaki trousers tucked into huge boots.

BIG SHAPE: the apron-coat is as wide at the hem as he is tall from waist to floor.
Two more things are pushed past sense: the brows are as thick as his fingers, and the goggles
on his forehead are as wide as his whole face.

DETAIL: at least eighteen small mismatched details clustered at the chest and one cuff, leaving
the rest of the cloth plain. This character is a wire-fitter, so the clutter is cable coils,
plugs, insulating tape, small tools and connector caps rather than generic badges.
Printed "K-07". A brass pocket-watch on the apron clasp.

MOTIF: this is the RUSTIDE world, so he carries pale uneven wax sealing the hems and pocket
edges, and goggles pushed up on the forehead with a dust scarf hanging loose at the neck, worn
but idle.

PHOTO: hair, eyes and clothes come from the photo. Body and pose proportions follow references.

FLAT FILL: the whole figure uses about twenty flat colour fields. Each area is one single
colour, identical across the whole area — poster ink on paper, hand-painted onto a cel. Shadows
are separate hard-edged colour fields, one per material, covering about half the figure.

INK AND FILL: Ember-orange #EA9056 apron-coat, ash-khaki #9F946B trousers, bone-white
#F1DEA9 hooded shirt, whistle-blue #02758F high-neck. Warm hues lead. Clothing colours are
sun-bleached, saturated but worn. Light from upper left.
```

## 这个例子想说明的

照片里那件**灰色连帽卫衣**变成了骨白旧毛线连帽衫，**款式保留了、材质和颜色换了**——
这就是「服装从照片来」的意思，不是套一件预设工装。

而**油布围裙、黄铜怀表、`K-07` 铭牌**是世界观长出来的，照片里一个都没有。

「像」来自**圆眼镜 + 络腮胡 + 寸头 + 敦实 + 浓眉小眼 + 白皮肤**，不来自衣服。
