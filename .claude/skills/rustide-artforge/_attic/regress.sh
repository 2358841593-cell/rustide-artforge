#!/usr/bin/env bash
# 回归套件 · 把每一个踩过的坑锁住
# 用法: bash checklists/regress.sh
cd "$(dirname "$0")/.." || exit 1
pass=0; fail=0
OUT=../../../outputs/r1/2026-08-21-wirewright-che

ok(){ printf "  ✅ %s\n" "$1"; pass=$((pass+1)); }
no(){ printf "  ❌ %s\n     %s\n" "$1" "$2"; fail=$((fail+1)); }

# 断言：某提示词必须被 lint 判为不合格，且理由里含某关键词
must_fail(){ # $1=文件 $2=期望关键词 $3=说明
  [ -f "$1" ] || { no "$3" "文件不存在: $1"; return; }
  out=$(python3 checklists/prompt-lint.py "$1" 2>&1); rc=$?
  if [ $rc -ne 0 ] && echo "$out" | grep -q "$2"; then ok "$3"
  else no "$3" "期望含「$2」的失败，实得: $(echo "$out" | tr '\n' ' ' | cut -c1-150)"; fi
}
must_pass(){ # $1=文件 $2=说明
  [ -f "$1" ] || { no "$2" "文件不存在: $1"; return; }
  out=$(python3 checklists/prompt-lint.py "$1" 2>&1); rc=$?
  if [ $rc -eq 0 ]; then ok "$2"
  else no "$2" "$(echo "$out" | grep '❌' | tr '\n' ' ')"; fi
}
mode_is(){ # $1=文件 $2=期望模式
  out=$(python3 checklists/prompt-lint.py "$1" 2>&1 | head -1)
  echo "$out" | grep -q "$2" && ok "模式识别: $(basename "$1") → $2" \
    || no "模式识别: $(basename "$1")" "期望 $2，实得 $out"
}

echo "── 1. 历史失败提示词必须仍被拦下 ──"
must_fail "$OUT/_archive/prompt.md"              "anime"        "v1: 禁用词 anime"
must_fail "$OUT/_archive/prompt.md"              "black"        "v1: 禁用词 black（曾被 'black hair' 白名单误掩盖）"
must_fail "$OUT/_archive/prompt.md"              "否定词"        "v1: 大量否定式"
must_fail "$OUT/_archive/prompt.md"              "do-not-copy"  "v1: do-not-copy 长串"
must_fail "$OUT/_archive/prompt-v3.md"           "SKIN"         "v3: 缺 SKIN 段（黄脸主因之一）"
must_fail "$OUT/_archive/prompt-v3.md"           "降饱和词"      "v3: 出现降饱和词"
must_fail "$OUT/_archive/prompt-v4-photo2-run.txt" "缺 LINE 段"   "v4: 缺 LINE 段"
must_fail "$OUT/_archive/prompt-v4-photo2-run.txt" "缺 DETAIL 段" "v4: 缺 DETAIL 段"
must_fail "$OUT/_archive/prompt-v4-photo2-run.txt" "服装"        "v4: 未声明服装来自照片"
must_fail "$OUT/_archive/prompt-v4-photo2-run.txt" "cream"      "v4: 肤色叫 warm cream"

echo "── 2. 当前提示词必须通过 ──"
# 动态取版本号最大的提示词，避免硬编码某一版（v6 被取代后曾导致误报）
CUR=$(ls "$OUT"/prompt-v*.txt 2>/dev/null | sed 's/.*prompt-v\([0-9]*\)\.txt/\1 &/' | sort -rn | head -1 | cut -d' ' -f2)
must_pass "$CUR" "当前提示词通过 lint: $(basename "${CUR:-无}")"

echo "── 3. 模式识别（曾退化过：比例段前置后认不出参考图模式）──"
mode_is "$CUR" "参考图"
mode_is "$OUT/_archive/prompt.md" "纯文字模式"

echo "── 4. 文档内嵌提示词一致性 ──"
if bash checklists/audit.sh >/dev/null 2>&1; then ok "audit.sh 全绿（模板/范例/铸锚提示词）"
else no "audit.sh" "$(bash checklists/audit.sh 2>&1 | grep -A3 '❌' | head -6)"; fi

echo "── 5. 文档零残留矛盾 ──"
stale=$(grep -rn "≤180\|≤200\|≤250\|六段顺序\|六段式" --include='*.md' --include='*.py' . 2>/dev/null | grep -v _archive)
[ -z "$stale" ] && ok "无过期阈值/段数残留" || no "残留过期表述" "$stale"
bad=$(for f in $(grep -rhoE '`(references|templates|checklists|examples|assets)/[a-zA-Z0-9._/-]+`' --include='*.md' . | tr -d '`' | sort -u); do [ -e "$f" ] || echo "$f"; done)
[ -z "$bad" ] && ok "引用的文件全部存在" || no "引用了不存在的文件" "$bad"

echo "── 6. 测量工具在官方参考图上必须自洽 ──"
cal=$(python3 checklists/measure.py --calibrate 2>&1)
if echo "$cal" | grep -q "top_heavy"; then
  lo=$(echo "$cal" | awk '/top_heavy/{print $3}')
  awk -v v="$lo" 'BEGIN{exit !(v>=1.0)}' && ok "参考图 top_heavy 下限 $lo ≥ 1.0（阈值取自实测，非拍脑袋）" \
    || no "标定异常" "top_heavy 下限 $lo"
else no "measure.py --calibrate" "$cal"; fi
for r in assets/refs-cel/06-john-early-portrait.png assets/refs-cel/13-hoffman-early-portrait.png; do
  python3 checklists/measure.py "$r" >/dev/null 2>&1
  [ $? -le 1 ] && ok "measure.py 能跑通 $(basename "$r")" || no "measure.py 崩溃" "$r"
done

echo "── 6b. 本轮新门禁 ──"
must_fail "$OUT/_archive/prompt-v3.md" "PHOTO-LOCK" "缺 PHOTO-LOCK 被拦下"
# 编辑模式不该强要求 LINE/SKIN-HEX/warm-dark-brown（否则是过度约束）
printf 'Use the first image as the edit target. Keep everything.\n\nSame drawing style as the reference sheets. A different person.\n\nPHOTO-LOCK: keep only the slim build and narrow eyes from the photo, amplified.\n\nCURVE: every edge is a slightly uneven curve.\n' > /tmp/_edit.txt
must_pass /tmp/_edit.txt "编辑模式不被过度约束"

echo "── 6c. 轮次守卫 ──"
TD=$(mktemp -d)
bash checklists/round-guard.sh "$TD" start 10 2 >/dev/null
bash checklists/round-guard.sh "$TD" check 12 >/dev/null 2>&1 && ok "轮次内放行(v12/上限2)" || no "轮次守卫" "第2版被误拦"
bash checklists/round-guard.sh "$TD" check 13 >/dev/null 2>&1 && no "轮次守卫" "第3版超限却放行" || ok "超限被拦下(v13/上限2)"
rm -rf "$TD"

echo "── 6d. 编辑链守卫 ──"
A="$OUT/_archive/v13-v24-overshoot"
bash checklists/edit-chain-guard.sh "$OUT" "$A/prompt-v23.txt" "$A/character-v22.png" >/dev/null 2>&1 \
  && no "编辑链守卫" "连续编辑(v23←v22←编辑)却放行" || ok "连续编辑被拦下"
bash checklists/edit-chain-guard.sh "$OUT" "$CUR" >/dev/null 2>&1 \
  && ok "生成模式放行: $(basename "$CUR")" || no "编辑链守卫" "生成模式被误拦"
must_pass templates/GOLD-from-scratch.txt "黄金模板通过 lint"

echo "── 7. 无游离产物（cwd 重置导致文件写错目录）──"
stray=$(ls prompt-*.txt character-*.png qc-*.md STATUS.md 2>/dev/null; ls -d checklists/__pycache__ 2>/dev/null)
[ -z "$stray" ] && ok "skill 根目录无游离产物" || no "skill 根目录有游离产物" "$stray —— 应在 outputs/r1/<角色>/ 下。写文件请用绝对路径"

echo "── 8. 夹具（真实样本覆盖不到的修复）──"
for f in checklists/fixtures/pass-*.txt; do
  must_pass "$f" "过度约束哨兵: $(basename "$f")"
done

# 断言总数固定，防止 glob 意外扩张（曾因 measure.py 污染源目录导致计数暴涨）
EXPECT=28
[ $((pass+fail)) -eq $EXPECT ] || { printf "  ❌ 断言总数 %d ≠ 预期 %d —— 有测试被漏跑或 glob 意外扩张\n" $((pass+fail)) $EXPECT; fail=$((fail+1)); }

echo
printf "通过 %d · 失败 %d\n" "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
