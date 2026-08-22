#!/usr/bin/env bash
# 编辑链守卫 · 禁止"改了又改"
#
# 编辑模式（"以上一张图为编辑目标，其余保持不变"）能把单张图调好，但：
#   · 不产生可复用的东西 —— 换一张照片全部作废
#   · 会累积漂移 —— 实测连续编辑 8 次(v29→v36)，头身比从 5 退回 7，画风崩坏
#   · **等于手动修图，不是 skill**
#
# 规则：编辑模式只允许**单次单点**微调。
#       若编辑目标本身也是编辑模式产物 → 拦下，要求回到生成模式。
#
# 用法: bash checklists/edit-chain-guard.sh <角色目录> <本次提示词> <编辑目标图>
set -u
DIR="${1:?}"; P="${2:?}"; TARGET="${3:-}"

is_edit(){ head -3 "$1" 2>/dev/null | grep -qi "edit target"; }

if ! is_edit "$P"; then
  echo "✅ 生成模式（从照片直出）—— 这是默认且推荐的模式"
  exit 0
fi

[ -n "$TARGET" ] || { echo "⚠️  编辑模式但没给编辑目标，无法检查链长"; exit 0; }

# 编辑目标 character-vN.png → 找它对应的 prompt-vN.txt
N=$(basename "$TARGET" | sed -n 's/.*v\([0-9][0-9]*\).*/\1/p')
SRC=$(find "$DIR" -name "prompt-v$N.txt" 2>/dev/null | head -1)

if [ -z "$SRC" ]; then
  echo "✅ 编辑模式，单次。编辑目标 v$N 没有对应提示词（或是外部图），视为链长 1"
  exit 0
fi

if is_edit "$SRC"; then
  cat <<EOF
❌ 编辑链过长，停止。

   本次是编辑模式，编辑目标 v$N **本身也是编辑产物**（$(basename "$SRC")）。
   这已经是「改了又改」，会累积漂移。

   实测：v29→v36 连续编辑 8 次，头身比从 5 退回 7，画风崩坏，全部作废。

正确做法：
   把这两轮想改的东西**合并写进一份生成模式提示词**，从照片重新直出。
   模板见 templates/GOLD-from-scratch.txt
EOF
  exit 1
fi

echo "✅ 编辑模式，链长 1（目标 v$N 是生成模式产物）—— 允许，但这是最后一次编辑"
exit 0
