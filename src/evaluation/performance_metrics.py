"""Aggregate raw JSONL measurements into per-(condition, baseline) summary rows."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.utils import read_json, read_jsonl

VALIDATION_LABEL = {
    "B0_stale": "n/a (stale by design)",
    "B1_full_recompute": "reference",
    "B2_append_correction": "n/a (append-only, not exact)",
    "B3a_document_cache_approx": "APPROXIMATE",
}


def dist(x) -> dict:
    x = np.asarray([v for v in x if v is not None and not (isinstance(v, float) and np.isnan(v))], dtype=float)
    if len(x) == 0:
        return {"mean": np.nan, "median": np.nan, "std": np.nan, "p95": np.nan, "n": 0}
    return {"mean": x.mean(), "median": np.median(x), "std": x.std(ddof=1) if len(x) > 1 else 0.0,
            "p95": np.percentile(x, 95) if len(x) >= 5 else np.nan, "n": len(x)}


def load_raw(results_dir: str | Path) -> dict:
    d = Path(results_dir)
    return {k: pd.DataFrame(read_jsonl(d / f"{k}.jsonl")) for k in ("updates", "answers", "runs", "conditions")}


def validation_status(results_dir: Path) -> dict:
    p = Path(results_dir) / "cache_validation.json"
    if not p.exists():
        p = Path(results_dir).parent / "cache_validation.json"
    out = dict(VALIDATION_LABEL)
    if p.exists():
        v = read_json(p)
        per = {}
        for case in v["cases"].values():
            for m, r in case["methods"].items():
                per.setdefault(m, []).append(r["status"] == "PASS")
        for m, ok in per.items():
            if m not in out:
                out[m] = f"{'PASS' if all(ok) else 'FAIL'} ({sum(ok)}/{len(ok)})"
    return out


def per_question_agreement(ans: pd.DataFrame) -> pd.DataFrame:
    """Generated-token agreement of each method with B1 on the same question (rep 0)."""
    a = ans[ans["rep"] == 0]
    ref = a[a["baseline"] == "B1_full_recompute"].set_index(["condition_id", "question_id"])["generated_ids"]
    def agree(r):
        k = (r["condition_id"], r["question_id"])
        return float(ref.get(k) == r["generated_ids"]) if k in ref.index else np.nan
    a = a.copy()
    a["agree_b1_tokens"] = a.apply(agree, axis=1)
    return a


def summarize(results_dir: str | Path) -> tuple[pd.DataFrame, dict]:
    raw = load_raw(results_dir)
    upd, ans, runs, conds = raw["updates"], raw["answers"], raw["runs"], raw["conditions"]
    if "run_status" in upd:  # only fully valid runs enter the summary
        upd = upd[upd["run_status"] == "ok"]
    if "run_status" in ans:
        ans = ans[ans["run_status"] == "ok"]
    vstat = validation_status(Path(results_dir))
    ans_a = per_question_agreement(ans) if len(ans) else ans
    rows = []
    ok_runs = runs[runs["status"] == "ok"]
    for (cid, b), g in ok_runs.groupby(["condition_id", "baseline"]):
        u = upd[(upd["condition_id"] == cid) & (upd["baseline"] == b)]
        per_rep = u.groupby("rep").agg(total=("update_total_s", "sum"), prefill=("prefill_s", "sum"),
                                       mgmt=("cache_management_s", "sum"), ser=("serialization_s", "sum"),
                                       tokz=("tokenization_s", "sum"))
        lat = dist(per_rep["total"])
        u0 = u[u["rep"] == 0]
        q = ans_a[(ans_a["condition_id"] == cid) & (ans_a["baseline"] == b)] if len(ans_a) else ans_a
        q0 = q[q["rep"] == 0]
        def acc(grp, outcome="correct"):
            s = q0[q0["group"] == grp]
            return (s["outcome"] == outcome).mean() if len(s) else np.nan
        init_prefill = [r["prefill_s"] for r in g["initialize"] if r]
        c = conds[conds["condition_id"] == cid].iloc[0]
        first = g.iloc[0]
        rows.append({
            "condition_id": cid, "baseline": b, "model": first["model"], "device_name": first["device_name"],
            "dtype": first["dtype"], "experiments": ",".join(c["meta"].get("experiments", [])),
            "dataset_config": f"budget={c['budget']},seed={c['seed']},docs={c['meta']['n_selected_docs']}",
            "budget": c["budget"], "seed": c["seed"], "scenario": c["scenario"], "update_type": c["scenario"],
            "update_position": c["position"], "n_sequential": c["n_sequential"], "n_events": c["n_events"],
            "context_tokens_v0": c["knowledge_tokens_v0"],
            "context_tokens_final": int(u0["total_knowledge_tokens"].iloc[-1]) if len(u0) else np.nan,
            "stable_ratio_target": c["stable_ratio_target"], "stable_ratio_actual": c["stable_ratio_actual"],
            "edit_pos_norm_full": c["edit_pos_norm_full"], "edit_pos_norm_dynamic": c["edit_pos_norm_dynamic"],
            "reps": len(per_rep),
            "update_latency_s_mean": lat["mean"], "update_latency_s_median": lat["median"],
            "update_latency_s_std": lat["std"], "update_latency_s_p95": lat["p95"],
            "update_prefill_s_mean": per_rep["prefill"].mean(), "update_cache_mgmt_s_mean": per_rep["mgmt"].mean(),
            "update_serialization_s_mean": per_rep["ser"].mean(), "update_tokenization_s_mean": per_rep["tokz"].mean(),
            "initial_prefill_s_mean": float(np.mean(init_prefill)) if init_prefill else np.nan,
            "query_ttft_s_mean": q["ttft_s"].mean() if len(q) else np.nan,
            "query_latency_s_mean": q["generation_s"].mean() if len(q) else np.nan,
            "query_tokens_per_s_mean": q["decode_tokens_per_s"].mean() if len(q) else np.nan,
            "n_questions": len(q0),
            "updated_fact_accuracy": acc("A"), "stale_answer_rate": acc("A", "stale"),
            "mixed_answer_rate": acc("A", "mixed"),
            "unchanged_fact_accuracy": acc("B"), "old_value_probe_accuracy": acc("C"),
            "cross_document_accuracy": acc("D"), "unanswerable_accuracy": acc("E"),
            "overall_accuracy": (q0["outcome"] == "correct").mean() if len(q0) else np.nan,
            "b1_token_agreement": q0["agree_b1_tokens"].mean() if len(q0) else np.nan,
            "reused_tokens": u0["reused_tokens"].sum() if len(u0) else np.nan,
            "recomputed_tokens": u0["recomputed_tokens"].sum() if len(u0) else np.nan,
            "cache_reuse_ratio": (u0["reused_tokens"].sum() / u0["total_knowledge_tokens"].sum())
            if len(u0) and b != "B0_stale" else np.nan,
            "peak_gpu_allocated_mb": u["gpu_peak_allocated_mb"].max() if "gpu_peak_allocated_mb" in u else np.nan,
            "peak_gpu_reserved_mb": u["gpu_peak_reserved_mb"].max() if "gpu_peak_reserved_mb" in u else np.nan,
            "answer_peak_gpu_allocated_mb": max((r.get("answer_gpu_peak_allocated_mb") or np.nan) for r in g["final_cache"]),
            "kv_cache_mb_final": u0["kv_cache_mb"].iloc[-1] if len(u0) else np.nan,
            "validation_status": vstat.get(b, "not validated"),
        })
    df = pd.DataFrame(rows)
    failed = runs[runs["status"] != "ok"][["condition_id", "baseline", "rep", "status", "error"]] if len(runs) else runs
    return df, {"failed_runs": failed}


def cycle_cost(df: pd.DataFrame, qs=(1, 5, 20)) -> pd.DataFrame:
    """Cost of one update followed by q questions, composed from measured mean components."""
    out = []
    for _, r in df.iterrows():
        per_upd = r["update_latency_s_mean"] / max(1, r["n_events"])
        for q in qs:
            out.append({"condition_id": r["condition_id"], "baseline": r["baseline"], "q": q,
                        "update_s": per_upd, "query_s": r["query_latency_s_mean"],
                        "cycle_cost_s": per_upd + q * r["query_latency_s_mean"]})
    return pd.DataFrame(out)
