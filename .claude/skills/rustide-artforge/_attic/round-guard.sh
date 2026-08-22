#!/usr/bin/env bash
# 轮次守卫 · 强制版本上限
#
# 实测：STATUS.md 白纸黑字写"本轮最多 2 版"，实际跑了 8 版（v29→v36），
# 最后画风崩坏、全部作废。**版本上限只是文档里的一句话时，没有约束力。**
#
# 用法:
#   bash checklists/round-guard.sh <角色目录> start <已用到的最大版本号> <本轮最多版本数>
#
# ⚠️ 基线是**已用到的最大版本号**，不是"内容基准版"。
#    例：内容退回 v26，但版本号已用到 v36 → 基线填 36，下一版是 v37。
#    版本号只增不减，避免覆盖历史。
#   bash checklists/round-guard.sh <角色目录> check <打算出的版本号>
set -u
DIR="${1:?用法见文件头}"; OP="${2:?}"
R="$DIR/.round"

if [ "$OP" = "start" ]; then
  printf "base=%s\nmax=%s\nstarted=%s\n" "${3:?基线版本号}" "${4:?最多版本数}" "$(date +%F\ %T)" > "$R"
  echo "✅ 本轮开始：基线 v$3，最多 $4 版（即 v$(($3+1)) – v$(($3+$4))）"
  exit 0
fi

[ -f "$R" ] || { echo "⚠️  未登记轮次。先跑: round-guard.sh $DIR start <基线版本号> <最多版本数>"; exit 0; }
BASE=$(awk -F= '/^base=/{print $2}' "$R")
MAX=$(awk -F= '/^max=/{print $2}' "$R")
WANT="${3:?打算出的版本号}"
USED=$((WANT - BASE))

if [ "$USED" -le "$MAX" ]; then
  echo "✅ v$WANT 是本轮第 $USED 版（上限 $MAX）"
  exit 0
fi

cat <<EOF
❌ 超出本轮版本上限，停止出图。

   本轮基线 v$BASE，上限 $MAX 版（v$((BASE+1)) – v$((BASE+MAX))）
   你想出的是 v$WANT，已是第 $USED 版。

继续重抽只会越改越偏（实测 v29→v36 跑了 8 版，最后画风崩坏全部作废）。

正确做法二选一：
  1. 停下来，把当前最好的一版交给用户判断
  2. 若确实需要继续，先跑 compare.py 确认没有退化，再由**用户**决定开新一轮：
     bash checklists/round-guard.sh "$DIR" start $WANT <最多版本数>
EOF
exit 1
