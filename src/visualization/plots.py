"""Publication figures (PNG + PDF) from the summary table. Only completed runs are plotted."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

# Validated reference categorical palette, fixed slot order -> fixed baseline (never re-ranked).
ORDER = ["B0_stale", "B1_full_recompute", "B2_append_correction", "B3_document_cache",
         "B3a_document_cache_approx", "B4_layered", "B5_prefix_invalidation"]
COLORS = dict(zip(ORDER, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6250d6", "#e34948"]))
MARKERS = dict(zip(ORDER, ["o", "s", "^", "D", "v", "P", "X"]))
LABELS = {"B0_stale": "B0 Stale", "B1_full_recompute": "B1 Full Recompute",
          "B2_append_correction": "B2 Append Correction", "B3_document_cache": "B3 Doc Cache (exact)",
          "B3a_document_cache_approx": "B3a Doc Cache (APPROX)", "B4_layered": "B4 Layered CAG",
          "B5_prefix_invalidation": "B5 Prefix Invalidation"}
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({
    "font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
    "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
    "figure.dpi": 150, "savefig.bbox": "tight", "lines.linewidth": 2, "axes.axisbelow": True,
})


def _save(fig, out: Path, name: str) -> list[str]:
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext in ("png", "pdf"):
        p = out / f"{name}.{ext}"
        fig.savefig(p)
        paths.append(str(p))
    plt.close(fig)
    return paths


def _present(df: pd.DataFrame) -> list[str]:
    return [b for b in ORDER if b in set(df["baseline"])]


def _bar(df, col, ylabel, title, out, name, err_col=None, pct=False, exclude=()):
    bs = [b for b in _present(df) if b not in exclude]
    g = df[df["baseline"].isin(bs)].groupby("baseline")[col]
    means = g.mean().reindex(bs)
    errs = (df[df["baseline"].isin(bs)].groupby("baseline")[err_col].mean().reindex(bs) if err_col
            else g.std(ddof=1).reindex(bs).fillna(0) if g.count().min() > 1 else None)
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    x = np.arange(len(bs))
    vals = means.values * (100 if pct else 1)
    ax.bar(x, vals, color=[COLORS[b] for b in bs], width=0.68, edgecolor="white", linewidth=2,
           yerr=None if errs is None else errs.values * (100 if pct else 1), capsize=3,
           error_kw={"ecolor": MUTED, "elinewidth": 1})
    for xi, v in zip(x, vals):
        if not np.isnan(v):
            ax.annotate(f"{v:.1f}" if pct else f"{v:.3g}", (xi, v), xytext=(0, 3), textcoords="offset points",
                        ha="center", fontsize=7.5, color=INK)
    ax.set_xticks(x, [LABELS[b] for b in bs], rotation=25, ha="right")
    ax.set_ylabel(ylabel + (" (%)" if pct else ""))
    ax.set_title(title, loc="left", color=INK)
    ax.grid(axis="x", visible=False)
    return _save(fig, out, name)


def make_all(summary: pd.DataFrame, cost: pd.DataFrame, out_dir: str | Path) -> dict:
    out = Path(out_dir)
    figs = {}
    s = summary.copy()
    main = s[s["experiments"].str.contains("update_types")]
    if main.empty:
        main = s
    n_cond = main["condition_id"].nunique()
    sub = f" ({n_cond} conditions; error bars = std across conditions)"

    # 1. Update latency vs answer accuracy
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    agg = main.groupby("baseline").agg(lat=("update_latency_s_mean", "mean"), acc=("updated_fact_accuracy", "mean"),
                                       lat_sd=("update_latency_s_mean", "std"), acc_sd=("updated_fact_accuracy", "std"))
    for b in _present(main):
        r = agg.loc[b]
        ax.errorbar(r["lat"] * 1000, r["acc"] * 100, xerr=(r["lat_sd"] or 0) * 1000, yerr=(r["acc_sd"] or 0) * 100,
                    fmt=MARKERS[b], color=COLORS[b], ms=8, mec="white", mew=1.5, ecolor=GRID, capsize=0, label=LABELS[b])
        ax.annotate(LABELS[b], (r["lat"] * 1000, r["acc"] * 100), xytext=(6, 4), textcoords="offset points",
                    fontsize=7.5, color=INK)
    ax.set_xscale("symlog", linthresh=1)
    ax.set_xlabel("Update latency per condition (ms, symlog)")
    ax.set_ylabel("Updated-fact accuracy (%)")
    ax.set_title("Update latency vs updated-fact accuracy" + sub, loc="left", fontsize=8.5)
    ax.legend(fontsize=7, loc="lower right")
    figs["latency_vs_accuracy"] = _save(fig, out, "01_latency_vs_accuracy")

    figs["update_latency"] = _bar(main, "update_latency_s_mean", "Update latency (s)",
                                  "Update latency by baseline" + sub, out, "02_update_latency",
                                  exclude=("B0_stale",))
    figs["reuse"] = _bar(main, "cache_reuse_ratio", "Valid cache reuse ratio", "Cache reuse ratio by baseline"
                         " (B0 excluded: stale reuse is not valid; B3a: approximate chunks not counted)",
                         out, "03_cache_reuse", pct=True, exclude=("B0_stale",))

    # 4. Update position vs latency
    pos = s[s["experiments"].str.contains("position")]
    if not pos.empty:
        fig, ax = plt.subplots(figsize=(6.4, 3.6))
        for b in [x for x in _present(pos) if x != "B0_stale"]:
            g = pos[pos["baseline"] == b].groupby("update_position").agg(
                x=("edit_pos_norm_dynamic", "mean"), y=("update_latency_s_mean", "mean"),
                e=("update_latency_s_mean", "std")).sort_values("x")
            ax.errorbar(g["x"], g["y"] * 1000, yerr=g["e"].fillna(0) * 1000, marker=MARKERS[b], color=COLORS[b],
                        ms=7, mec="white", label=LABELS[b], capsize=2)
        ax.set_xlabel("Normalised edit position within dynamic suffix (0 = start, 1 = end)")
        ax.set_ylabel("Update latency (ms)")
        ax.set_title(f"Edit position vs update latency ({pos['condition_id'].nunique()} conditions)", loc="left")
        ax.legend(fontsize=7, ncol=2)
        figs["position"] = _save(fig, out, "04_position_vs_latency")

    # 5. Stable ratio vs speed-up over B1
    rat = s[s["experiments"].str.contains("stable_ratio")]
    if not rat.empty:
        fig, ax = plt.subplots(figsize=(6.4, 3.6))
        ref = rat[rat["baseline"] == "B1_full_recompute"].set_index("condition_id")["update_latency_s_mean"]
        for b in [x for x in _present(rat) if x not in ("B0_stale", "B1_full_recompute")]:
            g = rat[rat["baseline"] == b].copy()
            g["speedup"] = g["condition_id"].map(ref) / g["update_latency_s_mean"]
            g = g.groupby("stable_ratio_actual")["speedup"].mean().sort_index()
            ax.plot(g.index * 100, g.values, marker=MARKERS[b], color=COLORS[b], ms=7, mec="white", label=LABELS[b])
        ax.axhline(1, color=MUTED, lw=1, ls="--")
        ax.set_xlabel("Actual stable-prefix ratio (% of knowledge tokens)")
        ax.set_ylabel("Update speed-up vs B1 (×)")
        ax.set_title("Stable prefix ratio vs update speed-up", loc="left")
        ax.legend(fontsize=7)
        figs["stable_ratio"] = _save(fig, out, "05_stable_ratio_vs_speedup")

    figs["updated_acc"] = _bar(main, "updated_fact_accuracy", "Updated-fact accuracy",
                               "Updated-fact accuracy by baseline" + sub, out, "06_updated_fact_accuracy", pct=True)
    figs["unchanged_acc"] = _bar(main, "unchanged_fact_accuracy", "Unchanged-fact accuracy",
                                 "Unchanged-fact accuracy by baseline" + sub, out, "07_unchanged_fact_accuracy", pct=True)
    figs["stale"] = _bar(main, "stale_answer_rate", "Stale answer rate",
                         "Stale answer rate (obsolete value returned)" + sub, out, "08_stale_answer_rate", pct=True)

    # 9. End-to-end cost vs queries per update
    if cost is not None and not cost.empty:
        c = cost[cost["condition_id"].isin(main["condition_id"])]
        fig, ax = plt.subplots(figsize=(6.4, 3.6))
        qs = np.array([1, 2, 5, 10, 20, 50])
        comp = c.groupby("baseline").agg(u=("update_s", "mean"), q=("query_s", "mean"))
        for b in [x for x in _present(main) if x != "B0_stale"]:
            r = comp.loc[b]
            ax.plot(qs, r["u"] + qs * r["q"], marker=MARKERS[b], color=COLORS[b], ms=6, mec="white", label=LABELS[b])
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("Questions answered per update")
        ax.set_ylabel("Cost of one update cycle (s)")
        ax.set_title("Update + query cost per cycle (from measured means)", loc="left")
        ax.legend(fontsize=7)
        figs["cost"] = _save(fig, out, "09_cost_vs_queries")

    figs["memory"] = _bar(main, "peak_gpu_allocated_mb", "Peak GPU allocated during update (MB)",
                          "Peak GPU memory by baseline (weights included)" + sub, out, "10_peak_gpu_memory")
    return figs
