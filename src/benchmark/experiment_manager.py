"""Expand a YAML profile into concrete Conditions and keep the dataset artefacts consistent."""
from __future__ import annotations

import itertools
import logging
from pathlib import Path

import yaml

from src.benchmark.experiments import Condition, build_condition
from src.data.documents import KnowledgeDoc
from src.data.loader import load_export
from src.data.partitioner import PartitionConfig
from src.data.preprocessor import build_documents
from src.utils import PROJECT_ROOT, read_json

log = logging.getLogger("cag.experiments")
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "database_export_2026-01-23T02-02-46.json"
DOCS_PATH = PROJECT_ROOT / "data" / "processed" / "documents.json"


def load_config(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_partition_config() -> PartitionConfig:
    return PartitionConfig.from_dict(load_config(PROJECT_ROOT / "configs" / "partition.yaml"))


def load_documents() -> tuple[list[KnowledgeDoc], str]:
    """Processed documents (rebuilt from the raw export if missing) and the corpus text used to keep
    synthetic values disjoint from real ones."""
    raw = load_export(RAW_PATH)
    if DOCS_PATH.exists():
        docs = [KnowledgeDoc.from_dict(d) for d in read_json(DOCS_PATH)["documents"]]
    else:
        docs = build_documents(raw)[0]
    corpus = "\n".join(d.text for d in docs)
    return docs, corpus


def expand(cfg: dict) -> list[dict]:
    specs = []
    for ex in cfg["experiments"]:
        for budget, seed, scen, pos, ratio, k in itertools.product(
                ex["budgets"], ex["seeds"], ex["scenarios"], ex.get("positions", ["random"]),
                ex.get("stable_ratios", [None]), ex.get("n_sequential", [1])):
            specs.append({"experiment": ex["name"], "budget": budget, "seed": seed, "scenario": scen,
                          "position": pos, "stable_ratio_target": ratio, "n_sequential": k})
    return specs


def build_conditions(cfg: dict, tok, template) -> tuple[list[Condition], list[dict]]:
    docs, corpus = load_documents()
    pcfg = load_partition_config()
    conds, failures, seen = [], [], set()
    for s in expand(cfg):
        try:
            c = build_condition(docs, tok, template, budget=s["budget"], seed=s["seed"], scenario=s["scenario"],
                                position=s["position"], stable_ratio_target=s["stable_ratio_target"],
                                n_sequential=s["n_sequential"], qa_sizes=cfg.get("qa_sizes"),
                                partition_cfg=pcfg, corpus_text=corpus)
        except ValueError as e:  # e.g. not enough eligible documents under this budget
            failures.append({**s, "status": "not_constructible", "reason": str(e)})
            log.warning("condition %s not constructible: %s", s, e)
            continue
        c.meta["experiments"] = [s["experiment"]]
        if c.condition_id in seen:
            next(x for x in conds if x.condition_id == c.condition_id).meta["experiments"].append(s["experiment"])
            continue
        seen.add(c.condition_id)
        conds.append(c)
    return conds, failures
