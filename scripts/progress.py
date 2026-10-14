"""Show completion % and an ETA (from measured wall time per method run) for every work item.

Usage: python scripts/progress.py
"""
import _bootstrap  # noqa: F401
from transformers import AutoTokenizer

from src.benchmark.experiment_manager import build_conditions, load_config
from src.data.knowledge import PromptTemplate
from src.utils import PROJECT_ROOT, read_json, read_jsonl, resolve_model_path

ITEMS = [  # (label, config, results dir)
    ("pilot 0.5B fp32", "configs/local_pilot_q05_fp32.yaml", "results/pilot_q05_fp32"),
    ("reduced 1.5B fp16", "configs/local_reduced_q15_fp16.yaml", "results/reduced_q15_fp16"),
    ("smoke 0.5B fp32", "configs/local_smoke_q05_fp32.yaml", "results/smoke_q05_fp32"),
]
VALIDATIONS = [("validation 0.5B fp32", "results/pilot_q05_fp32/cache_validation.json"),
               ("validation 1.5B fp16", "results/reduced_q15_fp16/cache_validation.json")]


def main():
    tok = AutoTokenizer.from_pretrained(resolve_model_path("Qwen/Qwen2.5-1.5B-Instruct")[0])
    tpl = PromptTemplate.from_tokenizer(tok)
    for label, path in VALIDATIONS:
        p = PROJECT_ROOT / path
        n = len(read_json(p)["cases"]) if p.exists() else 0
        print(f"{label:24s} {n:3d}/10 cases  {100 * n / 10:5.1f}%")
    for label, cfg_path, out in ITEMS:
        cfg = load_config(PROJECT_ROOT / cfg_path)
        conds, _ = build_conditions(cfg, tok, tpl)
        keys = {(c.condition_id, b, r) for c in conds for b in cfg["baselines"] for r in range(cfg.get("reps", 1))}
        runs = [r for r in read_jsonl(PROJECT_ROOT / out / "runs.jsonl")
                if (r["condition_id"], r["baseline"], r["rep"]) in keys]
        done = {(r["condition_id"], r["baseline"], r["rep"]) for r in runs if r["status"] in ("ok", "vram_spill")}
        failed = sum(r["status"] not in ("ok", "vram_spill") for r in runs)
        # rep 0 answers every question, later reps only a subset -> estimate per rep separately
        def mean_wall(rep0: bool):
            w = [r["wall_s"] for r in runs if r["status"] == "ok" and (r["rep"] == 0) == rep0]
            return sum(w) / len(w) if w else None
        left0 = sum(1 for k in keys - done if k[2] == 0)
        left1 = len(keys - done) - left0
        m0, m1 = mean_wall(True), mean_wall(False)
        eta = None
        if m0 or m1:
            eta = (left0 * (m0 or m1 * 4) + left1 * (m1 or m0 / 4)) / 60
        pct = 100 * len(done) / len(keys)
        print(f"{label:24s} {len(done):4d}/{len(keys)} runs  {pct:5.1f}%  failed={failed}  "
              f"ETA={'?' if eta is None else f'{eta:.0f} min'}  ({len(conds)} conditions)")


if __name__ == "__main__":
    main()
