"""Run a benchmark profile on real hardware and write raw JSONL results (resumable).

Usage: python scripts/run_benchmark.py --config configs/pilot.yaml [--out results/pilot] [--limit N]
CPU runs require --device cpu --allow-cpu and are labelled as such in every row.
"""
import argparse
import logging
import time

import _bootstrap  # noqa: F401
from common import environment, make_engine
from src.benchmark.experiment_manager import build_conditions, load_config
from src.benchmark.runner import Runner, TimeBudgetReached, warmup
from src.utils import PROJECT_ROOT, set_seed, write_json

log = logging.getLogger("cag.run")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--device", default="auto")
    ap.add_argument("--allow-cpu", action="store_true")
    ap.add_argument("--limit", type=int, default=None, help="only the first N conditions")
    ap.add_argument("--only", default=None, help="comma-separated experiment names")
    ap.add_argument("--max-minutes", type=float, default=None,
                    help="stop cleanly (between method runs) after this many minutes; rerun to resume")
    a = ap.parse_args()
    cfg = load_config(a.config)
    out = PROJECT_ROOT / (a.out or f"results/{cfg['profile']}")
    set_seed(0)
    eng = make_engine(cfg["model"], a.device, a.allow_cpu)
    tag = cfg["profile"] + ("_CPU_SMOKE" if eng.info.device == "cpu" else "")
    log.info("engine: %s", eng.info)
    write_json(out / "environment.json", {**environment(eng), "config": cfg, "run_tag": tag})
    conds, failures = build_conditions(cfg, eng.tok, eng.template)
    if failures:
        write_json(out / "not_constructible.json", failures)
    if a.only:
        keep = set(a.only.split(","))
        conds = [c for c in conds if keep & set(c.meta["experiments"])]
    conds = conds[: a.limit] if a.limit else conds
    log.info("%d conditions, %d not constructible", len(conds), len(failures))
    t0 = time.perf_counter()
    deadline = t0 + a.max_minutes * 60 if a.max_minutes else None
    warmup(eng)
    runner = Runner(eng, out, cfg["baselines"], cfg.get("reps", 1), cfg.get("query_latency_subset", 3), tag,
                    deadline=deadline)
    total = len(conds) * len(cfg["baselines"]) * cfg.get("reps", 1)
    try:
        for i, c in enumerate(conds):
            log.info("[%d/%d] %s (%d events, %d questions)", i + 1, len(conds), c.condition_id, len(c.events),
                     len(c.questions))
            runner.run_condition(c)
    except TimeBudgetReached:
        log.info("time budget of %.0f min reached: %d/%d method runs done (%.0f%%). Rerun the same command "
                 "to resume.", a.max_minutes, len(runner.done), total, 100 * len(runner.done) / total)
        return
    log.info("finished in %.1f min: %d/%d method runs done", (time.perf_counter() - t0) / 60,
             len(runner.done), total)


if __name__ == "__main__":
    main()
