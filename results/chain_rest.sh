#!/bin/bash
# Runs 35-minute sessions (11, 12, ...) on the 1.5B reduced grid until every run is done.
cd /d/THANHTUNG/HOC_KI_7/XLDL/cag-benchmark
PY=.venv/Scripts/python
commit() { git add -A && git -c user.email=phamthanhtung17032005@gmail.com -c user.name="Pham Thanh Tung" commit -q -m "$1

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" 2>/dev/null; }
s=11
while [ $s -le 16 ]; do
  echo "CHAIN_START_S$s"
  $PY -u scripts/run_benchmark.py --config configs/local_reduced_q15_fp16.yaml --out results/reduced_q15_fp16 --max-minutes 35 > results/session${s}_q15.log 2>&1
  rc=$?
  echo SESSION_END >> results/session${s}_q15.log
  $PY scripts/generate_report.py --results results/reduced_q15_fp16 > results/session${s}_report.log 2>&1
  commit "Session $s: 1.5B fp16 reduced grid resumed"
  echo "CHAIN_DONE_S$s rc=$rc $(grep -E 'budget of|finished in' results/session${s}_q15.log | tail -1 | cut -c 25-)"
  if [ $rc -ne 0 ] || grep -q "finished in" results/session${s}_q15.log; then break; fi
  s=$((s+1))
done
echo CHAIN_END
