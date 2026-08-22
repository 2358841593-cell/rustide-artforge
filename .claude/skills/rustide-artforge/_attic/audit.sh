#!/usr/bin/env bash
# 一致性审计 · 把文档里所有内嵌提示词抽出来跑一遍 lint
# 用法: bash checklists/audit.sh
cd "$(dirname "$0")/.." || exit 1
fail=0
python3 - <<'PY' > /tmp/_blocks.txt
import re, os, glob
pats = glob.glob('references/*.md') + glob.glob('examples/*.md') + glob.glob('../../../outputs/r1/*/prompt-v*.txt')
for f in pats:
    if '_archive' in f: continue
    t = open(f).read()
    for i, m in enumerate(re.finditer(r'```(?:text)?\n(.*?)```', t, re.S)):
        b = m.group(1)
        # 只挑看起来是英文出图提示词的块
        if re.search(r'(A 1990s hand-inked|Same drawing style)', b):
            os.makedirs('/tmp/_b', exist_ok=True)
            p = f'/tmp/_b/{f.replace("/","_")}_{i}.txt'
            open(p, 'w').write(b)
            print(p, f)
PY
while read -r path src; do
  out=$(python3 checklists/prompt-lint.py "$path" 2>&1); rc=$?
  if [ $rc -ne 0 ]; then
    echo "❌ $src"
    echo "$out" | sed 's/^/     /'
    fail=1
  else
    echo "✅ $src  ($(echo "$out" | head -1))"
  fi
done < /tmp/_blocks.txt
rm -rf /tmp/_b /tmp/_blocks.txt
exit $fail
