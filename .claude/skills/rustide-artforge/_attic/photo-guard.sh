#!/usr/bin/env bash
# 照片守卫 · 防止「换了照片却复用旧提示词」
#
# prompt-v{N}.txt 里的 CLOTHES / FACE 段是从某一张照片推导出来的，写死在文本里。
# 换照片后若直接复用旧提示词，新照片的服装和五官**永远进不去**（实测发生过）。
#
# 用法: bash checklists/photo-guard.sh <prompt-vN.txt> <当前照片>
#   首次会创建 sidecar  <prompt-vN.photo>  记录来源照片的 SHA256。
#   之后每次比对；不一致就拦下，要求回 STEP 1 重新推导，出 prompt-v{N+1}.txt。
set -u
P="${1:?用法: photo-guard.sh <prompt.txt> <photo>}"
PH="${2:?用法: photo-guard.sh <prompt.txt> <photo>}"
SIDE="${P%.txt}.photo"
NOW=$(shasum -a 256 "$PH" | awk '{print $1}')

if [ ! -f "$SIDE" ]; then
  printf "%s  %s\n" "$NOW" "$(basename "$PH")" > "$SIDE"
  echo "✅ 已登记来源照片: $(basename "$PH")  ${NOW:0:16}"
  exit 0
fi

WAS=$(awk '{print $1}' "$SIDE"); WASF=$(awk '{print $2}' "$SIDE")
if [ "$NOW" = "$WAS" ]; then
  echo "✅ 照片未变（$WASF ${WAS:0:16}），可复用 $(basename "$P")"
  exit 0
fi

cat <<EOF
❌ 照片变了，不能复用这份提示词。

   提示词依据: $WASF  ${WAS:0:16}
   当前照片  : $(basename "$PH")  ${NOW:0:16}

$(basename "$P") 里的 CLOTHES / FACE 段是从旧照片推导后**写死在文本里**的。
直接跑它，新照片的服装和五官进不去。

正确做法：回 photo-to-character.md STEP 1 重新提取，产出 prompt-v\$((N+1)).txt。
EOF
exit 1
