"""Build the conditions (snapshots, synthetic updates, questions) of a profile and save them.

Usage: python scripts/generate_benchmark.py --config configs/pilot.yaml
"""
import argparse
from collections import Counter

import _bootstrap  # noqa: F401
from transformers import AutoTokenizer

from src.benchmark.experiment_manager import build_conditions, load_config
from src.utils import resolve_model_path
from src.data.knowledge import PromptTemplate
from src.utils import PROJECT_ROOT, write_json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    a = ap.parse_args()
    cfg = load_config(a.config)
    tok = AutoTokenizer.from_pretrained(resolve_model_path(cfg["model"]["name"])[0])
    conds, failures = build_conditions(cfg, tok, PromptTemplate.from_tokenizer(tok))
    out = PROJECT_ROOT / "data" / "benchmark" / cfg["profile"]
    for c in conds:
        write_json(out / "conditions" / f"{c.condition_id}.json", {
            "condition_id": c.condition_id, "budget": c.budget, "seed": c.seed, "scenario": c.scenario,
            "position": c.position, "stable_ratio_target": c.stable_ratio_target, "meta": c.meta,
            "snapshots": [s.to_dict() for s in c.snapshots], "events": [e.to_dict() for e in c.events],
            "questions": c.questions})
    qs = [q for c in conds for q in c.questions]
    cov = {"profile": cfg["profile"], "n_conditions": len(conds), "not_constructible": failures,
           "n_questions": len(qs), "questions_by_group": dict(Counter(q["group"] for q in qs)),
           "questions_by_type": dict(Counter(q["question_type"] for q in qs)),
           "n_update_events": sum(len(c.events) for c in conds),
           "update_types": dict(Counter(e.update_type for c in conds for e in c.events)),
           "distinct_source_docs_in_questions": len({d for q in qs for d in q["source_doc_ids"]})}
    write_json(out / "coverage.json", cov)
    print({k: v for k, v in cov.items() if k != "not_constructible"}, "not constructible:", len(failures))


if __name__ == "__main__":
    main()
