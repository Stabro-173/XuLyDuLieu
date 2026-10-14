"""Aggregate raw results into CSV summaries, figures and auto-generated markdown tables.

Usage: python scripts/generate_report.py --results results/pilot [--publish-summary]
Writes <results>/benchmark_summary.csv, cycle_cost.csv, failed_runs.csv, figures/*.png|pdf and
reports/<profile>_tables.md. --publish-summary also copies the summary to results/benchmark_summary.csv.
"""
import argparse
import shutil

import _bootstrap  # noqa: F401
import numpy as np
import pandas as pd

from src.evaluation.performance_metrics import cycle_cost, load_raw, summarize
from src.utils import PROJECT_ROOT, read_json
from src.visualization.plots import LABELS, ORDER, make_all


def md_table(df: pd.DataFrame, floatfmt: str = ".3f") -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, (float, np.floating)):
                cells.append("—" if np.isnan(v) else format(v, floatfmt))
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def by_baseline(df: pd.DataFrame, cols: dict, pct: set = frozenset()) -> pd.DataFrame:
    g = df.groupby("baseline")
    t = pd.DataFrame({name: g[c].mean() * (100 if name in pct else 1) for name, c in cols.items()})
    t = t.reindex([b for b in ORDER if b in t.index])
    t.insert(0, "Method", [LABELS[b] for b in t.index])
    return t.reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--publish-summary", action="store_true")
    a = ap.parse_args()
    rdir = PROJECT_ROOT / a.results
    profile = rdir.name
    summ, extra = summarize(rdir)
    summ.to_csv(rdir / "benchmark_summary.csv", index=False)
    cost = cycle_cost(summ)
    cost.to_csv(rdir / "cycle_cost.csv", index=False)
    extra["failed_runs"].to_csv(rdir / "failed_runs.csv", index=False)
    if a.publish_summary:
        shutil.copy(rdir / "benchmark_summary.csv", PROJECT_ROOT / "results" / "benchmark_summary.csv")
    figs = make_all(summ, cost, rdir / "figures")

    raw = load_raw(rdir)
    ans = raw["answers"]
    env = read_json(rdir / "environment.json") if (rdir / "environment.json").exists() else {}
    parts = [f"# Auto-generated tables — profile `{profile}`\n",
             f"Engine: `{env.get('engine', {})}`\n",
             f"Conditions: {summ['condition_id'].nunique()}; completed method runs: {len(summ)}; "
             f"failed runs: {len(extra['failed_runs'])}; answered questions (rep 0): "
             f"{int((ans['rep'] == 0).sum()) if len(ans) else 0}\n"]

    main_df = summ[summ["experiments"].str.contains("update_types")]
    if main_df.empty:
        main_df = summ
    parts.append(f"\n## Main comparison ({main_df['condition_id'].nunique()} conditions, mean over conditions)\n")
    parts.append(md_table(by_baseline(main_df, {
        "upd lat (ms)": "update_latency_s_mean", "upd prefill (ms)": "update_prefill_s_mean",
        "init prefill (ms)": "initial_prefill_s_mean", "TTFT (ms)": "query_ttft_s_mean",
        "answer (ms)": "query_latency_s_mean", "reuse %": "cache_reuse_ratio",
        "ctx final": "context_tokens_final", "peak alloc MB": "peak_gpu_allocated_mb"}, {"reuse %"}).assign(
        **{"upd lat (ms)": lambda d: d["upd lat (ms)"] * 1000, "upd prefill (ms)": lambda d: d["upd prefill (ms)"] * 1000,
           "init prefill (ms)": lambda d: d["init prefill (ms)"] * 1000, "TTFT (ms)": lambda d: d["TTFT (ms)"] * 1000,
           "answer (ms)": lambda d: d["answer (ms)"] * 1000}), ".1f"))
    parts.append("\n\n### Accuracy (%)\n")
    acc_cols = {"A updated": "updated_fact_accuracy", "A stale": "stale_answer_rate", "A mixed": "mixed_answer_rate",
                "B unchanged": "unchanged_fact_accuracy", "C probes": "old_value_probe_accuracy",
                "D cross-doc": "cross_document_accuracy", "E unanswerable": "unanswerable_accuracy",
                "overall": "overall_accuracy", "agree w/ B1 tokens": "b1_token_agreement"}
    parts.append(md_table(by_baseline(main_df, acc_cols, set(acc_cols)), ".1f"))

    # pooled question-level accuracy over every condition
    if len(ans):
        a0 = ans[ans["rep"] == 0]
        piv = (a0.assign(c=a0["outcome"] == "correct").groupby(["baseline", "group"])["c"].agg(["mean", "count"]))
        t = piv["mean"].unstack() * 100
        n = piv["count"].unstack()
        t = t.reindex([b for b in ORDER if b in t.index])
        t.columns = [f"{c} (n={int(n[c].iloc[0])})" for c in t.columns]
        t.insert(0, "Method", [LABELS[b] for b in t.index])
        parts.append("\n\n## Pooled question-level accuracy over all conditions (%)\n")
        parts.append(md_table(t.reset_index(drop=True), ".1f"))
        st = a0[a0["group"] == "A"].groupby("baseline")["outcome"].value_counts(normalize=True).unstack().fillna(0) * 100
        st = st.reindex([b for b in ORDER if b in st.index])
        st.insert(0, "Method", [LABELS[b] for b in st.index])
        parts.append("\n\n### Group A outcome breakdown (%)\n")
        parts.append(md_table(st.reset_index(drop=True), ".1f"))

    for exp, keys in [("position", ["update_position"]), ("stable_ratio", ["stable_ratio_target"]),
                      ("context_length", ["budget"]), ("sequential", ["n_sequential"]), ("repeated", ["n_sequential"])]:
        d = summ[summ["experiments"].str.contains(exp)]
        if d.empty:
            continue
        cols = ["update_latency_s_mean", "update_latency_s_std", "recomputed_tokens", "cache_reuse_ratio",
                "context_tokens_final", "updated_fact_accuracy", "stale_answer_rate", "unchanged_fact_accuracy",
                "query_latency_s_mean"]
        extra_keys = {"position": ["edit_pos_norm_dynamic"], "stable_ratio": ["stable_ratio_actual"]}.get(exp, [])
        t = d.groupby(keys + ["baseline"])[extra_keys + cols].mean().reset_index()
        t["update_latency_ms"] = t.pop("update_latency_s_mean") * 1000
        t["update_latency_std_ms"] = t.pop("update_latency_s_std") * 1000
        t["query_latency_ms"] = t.pop("query_latency_s_mean") * 1000
        t["baseline"] = t["baseline"].map(LABELS)
        parts.append(f"\n\n## Ablation: {exp} ({d['condition_id'].nunique()} conditions)\n")
        parts.append(md_table(t, ".3f"))

    if len(extra["failed_runs"]):
        parts.append("\n\n## Failed runs\n")
        parts.append(md_table(extra["failed_runs"].assign(error=lambda d: d["error"].str.slice(0, 120))))
    parts.append("\n\n## Figures\n" + "\n".join(f"- {k}: `{v[0]}`" for k, v in figs.items()))
    out = PROJECT_ROOT / "reports" / f"{profile}_tables.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")
    print(f"wrote {rdir / 'benchmark_summary.csv'} ({len(summ)} rows), {out}, {len(figs)} figures")


if __name__ == "__main__":
    main()
