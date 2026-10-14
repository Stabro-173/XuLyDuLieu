#!/bin/bash
# Waits for session 8 to end, then runs sessions 9 and 10 (35 min each), reporting + committing after each.
cd /d/THANHTUNG/HOC_KI_7/XLDL/cag-benchmark
PY=.venv/Scripts/python
until grep -q SESSION_END results/session8_q15.log; do sleep 5; done
commit() { git add -A && git -c user.email=phamthanhtung17032005@gmail.com -c user.name="Pham Thanh Tung" commit -q -m "$1

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" 2>/dev/null; }
$PY scripts/generate_report.py --results results/reduced_q15_fp16 > results/session8_report.log 2>&1
commit "Session 8: 1.5B fp16 reduced grid started; B3a dropped (VRAM spill on 4 GB)"
echo CHAIN_S8_COMMITTED
for s in 9 10; do
  echo "CHAIN_START_S$s"
  $PY -u scripts/run_benchmark.py --config configs/local_reduced_q15_fp16.yaml --out results/reduced_q15_fp16 --max-minutes 35 > results/session${s}_q15.log 2>&1
  echo SESSION_END >> results/session${s}_q15.log
  $PY scripts/generate_report.py --results results/reduced_q15_fp16 > results/session${s}_report.log 2>&1
  commit "Session $s: 1.5B fp16 reduced grid resumed"
  echo "CHAIN_DONE_S$s $(grep -E 'budget of|finished in' results/session${s}_q15.log | tail -1 | cut -c 25-)"
done
echo CHAIN_END
