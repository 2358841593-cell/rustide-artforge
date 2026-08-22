#!/usr/bin/env bash
# 变异测试 · 验证 regress.sh 真的有牙
# 故意把已修好的 bug 改回去，确认回归套件能抓到。全部 ✅ 才说明套件有效。
# 用法: bash checklists/mutate.sh
cd "$(dirname "$0")/.." || exit 1
cp checklists/prompt-lint.py /tmp/lint.bak
run(){
  local desc="$1" old="$2" new="$3" expect="$4"
  OLD="$old" NEW="$new" python3 -c '
import os,sys
p="checklists/prompt-lint.py"; t=open(p).read()
if os.environ["OLD"] not in t: sys.exit(1)
open(p,"w").write(t.replace(os.environ["OLD"],os.environ["NEW"],1))' || { echo "  ⚠️  变异点未找到: $desc"; return; }
  if bash checklists/regress.sh 2>&1 | grep -qF "❌ $expect"; then echo "  ✅ 抓到: $desc"
  else echo "  ❌ 漏掉: $desc"; fi
  cp /tmp/lint.bak checklists/prompt-lint.py
}
run "删掉 LINE 段检查" 'if "LINE:" not in text and not edit_mode:' 'if False:' "v4: 缺 LINE 段"
run "删掉 DETAIL 段检查" 'if "DETAIL" not in text.upper() and not edit_mode:' 'if False:' "v4: 缺 DETAIL 段"
run "还原 black 白名单 bug" 'scrubbed = re.sub(r"\bblack (hair|fringe|hat|coat|beard|boots|gloves)\b", "", low)' 'scrubbed = "" if "black hair" in low else low' "v1: 禁用词 black"
run "删掉 SKIN 检查" 'if not re.search(r"\bskin:", low):' 'if False:' "v3: 缺 SKIN 段"
run "删掉降饱和词门禁" 'if re.search(r"\b(dusty|muted|desaturated|washed[- ]out|greyish|grayish)\b", low):' 'if False:' "v3: 出现降饱和词"
run "还原模式检测 re.match" 're.search(r"same drawing style", "\n\n".join(text.strip().split("\n\n")[:3]), re.I)' 're.match(r"same drawing style", text.strip(), re.I)' "模式识别"
run "删掉服装来源检查"      'if not re.search(r"scavenged version of what the photo wears|from the photo", low):' 'if False:' "v4: 未声明服装来自照片"
diff -q /tmp/lint.bak checklists/prompt-lint.py >/dev/null && echo "✅ lint 已还原"
