"""Phase 4: exact-cache equivalence of B3/B4/B5 (and the approximate B3a) vs one-shot Full Recompute
on the real model, for the ten mandated update scenarios.

Usage: python scripts/validate_cache.py --config configs/smoke.yaml --budget 2048 --out results/cache_validation.json
"""
import argparse
import time

import _bootstrap  # noqa: F401
from common import environment, make_engine
from src.benchmark.experiment_manager import load_config, load_documents, load_partition_config
from src.benchmark.experiments import select_documents
from src.cache.cache_validation import validate_case, validation_cases
from src.cache.engine import free_cuda
from src.data.knowledge import KnowledgeSnapshot
from src.data.partitioner import partition
from src.utils import write_json

METHODS = ["B3_document_cache", "B4_layered", "B5_prefix_invalidation", "B3a_document_cache_approx"]


def _fmt(x: dict) -> str:
    kv = "n/a" if x["kv_rel_max"] is None else f"{x['kv_rel_max']:.1e}"
    return (f"{x['status']}(kv_rel={kv},logit={x['logits_max_abs']:.2e},"
            f"tok={x['generated_token_agreement']:.2f},reuse={x['reused_tokens']})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/smoke.yaml")
    ap.add_argument("--budget", type=int, default=2048)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="results/cache_validation.json")
    ap.add_argument("--device", default="auto")
    ap.add_argument("--allow-cpu", action="store_true")
    a = ap.parse_args()
    cfg = load_config(a.config)
    eng = make_engine(cfg["model"], a.device, a.allow_cpu)
    docs, corpus = load_documents()
    sel, held = select_documents(docs, eng.tok, eng.template, a.budget, a.seed)
    ordered, _ = partition(sel, load_partition_config())
    snap = KnowledgeSnapshot(0, ordered)
    res = {"budget": a.budget, "seed": a.seed, "engine": eng.info.__dict__, "cases": {}}
    for name, ev in validation_cases(snap, held[0], a.seed, corpus):
        t0 = time.perf_counter()
        r = validate_case(eng, snap, ev, METHODS)
        r["seconds"] = time.perf_counter() - t0
        res["cases"][name] = r
        free_cuda()
        line = "  ".join(f"{m.split('_')[0]}:{_fmt(x)}" for m, x in r["methods"].items())
        print(f"{name:28s} ref_tokens={r['ref_tokens']}  {line}", flush=True)
    summ = {}
    for m in METHODS:
        st = [c["methods"][m]["status"] for c in res["cases"].values()]
        summ[m] = {"pass": st.count("PASS"), "total": len(st)}
    res["summary"] = summ
    res["environment"] = environment(eng)
    write_json(a.out, res)
    print("summary:", summ)


if __name__ == "__main__":
    main()
