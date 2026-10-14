"""Phase 1: load the raw export (read-only), build canonical documents, profile and partition them.

Outputs: data/processed/documents.json, dataset_profile.json, partition_manifest.json
"""
import argparse
from collections import Counter

import _bootstrap  # noqa: F401
from src.benchmark.experiment_manager import RAW_PATH, load_partition_config
from src.data.knowledge import KnowledgeSnapshot
from src.data.loader import load_export
from src.data.partitioner import partition
from src.data.preprocessor import build_documents
from src.data.qa_generator import eligible_fields
from src.utils import PROJECT_ROOT, sha256_file, write_json

OUT = PROJECT_ROOT / "data" / "processed"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokenizer", default="Qwen/Qwen2.5-1.5B-Instruct")
    ap.add_argument("--no-tokenizer", action="store_true", help="skip token counts (offline)")
    a = ap.parse_args()

    raw = load_export(RAW_PATH)
    docs, rep = build_documents(raw)
    assert sha256_file(RAW_PATH) == raw.sha256, "raw file must not change"
    write_json(OUT / "documents.json", {"source_sha256": raw.sha256, "export_date": raw.export_date,
                                        "documents": [d.to_dict() for d in docs]})

    tok = None
    if not a.no_tokenizer:
        from transformers import AutoTokenizer
        from src.utils import resolve_model_path
        tok = AutoTokenizer.from_pretrained(resolve_model_path(a.tokenizer)[0])
    ntok = (lambda t: len(tok(t, add_special_tokens=False)["input_ids"])) if tok else (lambda t: None)

    ordered, why = partition(docs, load_partition_config())
    snap = KnowledgeSnapshot(0, ordered)
    snap.validate_order()
    why_map = {w["doc_id"]: w["rationale"] for w in why}
    manifest = [{"order": i, "doc_id": d.doc_id, "doc_kind": d.doc_kind, "knowledge_type": d.knowledge_type,
                 "tokens": ntok(d.text), "chars": len(d.text), "content_hash": d.content_hash,
                 "rationale": why_map[d.doc_id]} for i, d in enumerate(snap.docs)]
    tot = {k: sum(m["tokens"] or 0 for m in manifest if m["knowledge_type"] == k) for k in ("stable", "dynamic")}
    write_json(OUT / "partition_manifest.json", {
        "tokenizer": a.tokenizer if tok else None, "stable_tokens": tot["stable"], "dynamic_tokens": tot["dynamic"],
        "stable_ratio": tot["stable"] / max(1, tot["stable"] + tot["dynamic"]) if tok else None,
        "documents": manifest})

    fact_counts = Counter(f for d in docs for f in eligible_fields(d))
    profile = {
        "source_file": RAW_PATH.name, "source_sha256": raw.sha256, "export_date": raw.export_date,
        "database": raw.database, "record_counts": raw.record_counts, "preprocessing": rep.to_dict(),
        "documents_by_kind": dict(Counter(d.doc_kind for d in docs)),
        "eligible_fact_fields": dict(fact_counts), "eligible_facts_total": sum(fact_counts.values()),
        "total_tokens_all_documents": sum(m["tokens"] or 0 for m in manifest) if tok else None,
        "tokens_by_kind": {k: sum(m["tokens"] or 0 for m in manifest if m["doc_kind"] == k)
                           for k in set(m["doc_kind"] for m in manifest)} if tok else None,
    }
    write_json(OUT / "dataset_profile.json", profile)
    print(f"documents: {len(docs)}  eligible facts: {profile['eligible_facts_total']}  "
          f"tokens(all docs): {profile['total_tokens_all_documents']}")
    print("by kind:", profile["documents_by_kind"])
    print("facts:", dict(fact_counts))
    if tok:
        print("tokens by kind:", profile["tokens_by_kind"], " stable ratio (default partition):",
              round(manifest and tot["stable"] / (tot["stable"] + tot["dynamic"]), 3))


if __name__ == "__main__":
    main()
