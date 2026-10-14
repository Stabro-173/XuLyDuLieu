"""Exact-cache equivalence validation of reuse strategies against one-shot Full Recompute."""
from __future__ import annotations

from src.baselines import REGISTRY
from src.baselines.full_recompute import FullRecompute
from src.cache import kv_utils
from src.data.knowledge import KnowledgeSnapshot
from src.data.updates import UpdateEvent, UpdateFactory, apply_update
from src.data.qa_generator import eligible_fields

TOLERANCES = {
    # relative = max|diff| / max|reference| over all layers; logits = max |diff| of first-token logits
    "float32": {"kv_rel_max": 1e-4, "logits_max_abs": 1e-3},
    "float16": {"kv_rel_max": 1e-2, "logits_max_abs": 0.5},
    "bfloat16": {"kv_rel_max": 5e-2, "logits_max_abs": 1.0},
}
PROBES = [
    "Công ty đã thực hiện tổng cộng bao nhiêu dự án?",
    "Giờ làm việc của công ty là khi nào?",
]


def _max_abs(cache) -> float:
    return max(max(k.abs().max().item(), v.abs().max().item()) for k, v in kv_utils.kv_pairs(cache))


def validation_cases(snap0: KnowledgeSnapshot, held_out_doc, seed: int = 0, corpus_text: str = "") -> list[tuple[str, UpdateEvent]]:
    """The ten mandated scenarios built against snap0 (each is an independent single event)."""
    fac = UpdateFactory(seed, corpus_text)
    dyn = snap0.dynamic_docs
    projs = [d for d in dyn if d.doc_kind == "project"]
    area = [d for d in projs if "area_m2" in eligible_fields(d)]
    inv = [d for d in projs if "investment" in eligible_fields(d)]
    loc = [d for d in projs if "location" in eligible_fields(d)]
    first = dyn[0]
    first_field = "total_projects" if first.doc_kind == "company_stats" else eligible_fields(first)[0]
    cases = [
        ("01_no_change", UpdateEvent("v_01", "no_update", version_before=0, version_after=1)),
        ("02_first_dynamic_doc", fac.field_update(snap0, [(first.doc_id, first_field)], "first")),
        ("03_middle_dynamic_doc", fac.field_update(snap0, [(area[len(area) // 2].doc_id, "area_m2")], "middle")),
        ("04_last_dynamic_doc", fac.field_update(snap0, [(area[-1].doc_id, "area_m2")], "last")),
        ("05_single_numeric_field", fac.field_update(snap0, [(inv[0].doc_id, "investment")], "numeric")),
        ("06_token_count_changes", fac.field_update(snap0, [(loc[0].doc_id, "location")], "token_len")),
        ("07_append_document", fac.add_doc(snap0, held_out_doc)),
        ("08_delete_document", fac.delete_doc(snap0, projs[len(projs) // 2].doc_id)),
        ("09_multiple_documents", fac.field_update(snap0, [(d.doc_id, "area_m2") for d in area[:3]], "multi")),
        ("10_stable_document_changes", fac.field_update(snap0, [("company_profile", "working_hours")], "stable")),
    ]
    for _, ev in cases:  # all built against v0
        ev.version_before, ev.version_after = 0, 1
    return cases


def validate_case(engine, snap0: KnowledgeSnapshot, event: UpdateEvent, methods: list[str],
                  probes: list[str] | None = None, max_new_tokens: int = 16) -> dict:
    probes = probes or PROBES
    snap1 = apply_update(snap0, event)
    tol = TOLERANCES[str(engine.dtype).replace("torch.", "")]

    ref = FullRecompute(engine)
    ref.initialize(snap1)
    ref_scale = _max_abs(ref.cache)
    ref_ans = [ref.answer(q, keep_logits=True) for q in probes]
    out = {"update_type": event.update_type, "ref_tokens": len(ref.ids), "methods": {}}

    for name in methods:
        m = REGISTRY[name](engine)
        m.initialize(snap0)
        upd = m.update(event, snap1)
        r = {"reused_tokens": upd["reused_tokens"], "recomputed_tokens": upd["recomputed_tokens"],
             "reuse_shortened": upd.get("reuse_shortened"), "token_ids_equal": m.ids == ref.ids,
             "cache_len": kv_utils.cache_len(m.cache), "ref_cache_len": kv_utils.cache_len(ref.cache)}
        if r["token_ids_equal"] and r["cache_len"] == r["ref_cache_len"]:
            cmp = kv_utils.compare(m.cache, ref.cache)
            r["kv_max_abs"], r["kv_mean_abs"] = cmp["max_abs"], cmp["mean_abs"]
            r["kv_rel_max"] = cmp["max_abs"] / ref_scale
            r["kv_layer_max"] = [max(x["k_max"], x["v_max"]) for x in cmp["per_layer"]]
            # numerical floor: one-shot vs two-chunk full prefill split at the same reuse point
            split = upd["reused_tokens"]
            if 0 < split < len(ref.ids):
                c, _ = engine.prefill(ref.ids[:split])
                c, _ = engine.prefill(ref.ids[split:], c)
                fl = kv_utils.compare(c, ref.cache)
                r["chunking_floor_kv_max_abs"] = fl["max_abs"]
                r["chunking_floor_kv_mean_abs"] = fl["mean_abs"]
                del c
            else:
                r["chunking_floor_kv_max_abs"] = 0.0 if split in (0, len(ref.ids)) else None
        else:
            r["kv_max_abs"] = r["kv_rel_max"] = None
        logit_d, tok_agree, ans_agree, argmax_agree = [], [], [], []
        for q, ra in zip(probes, ref_ans):
            a = m.answer(q, keep_logits=True)
            logit_d.append((a["first_logits"] - ra["first_logits"]).abs().max().item())
            argmax_agree.append(int(a["first_logits"].argmax()) == int(ra["first_logits"].argmax()))
            tok_agree.append(a["generated_ids"] == ra["generated_ids"])
            ans_agree.append(a["answer"] == ra["answer"])
        r.update({"logits_max_abs": max(logit_d), "first_token_agreement": all(argmax_agree),
                  "generated_token_agreement": sum(tok_agree) / len(tok_agree),
                  "answer_agreement": sum(ans_agree) / len(ans_agree)})
        exact_ok = (r["token_ids_equal"] and r["kv_rel_max"] is not None and r["kv_rel_max"] <= tol["kv_rel_max"]
                    and r["logits_max_abs"] <= tol["logits_max_abs"])
        r["status"] = "PASS" if exact_ok else "FAIL"
        r["exact_method"] = getattr(m, "exact", False)
        out["methods"][name] = r
        del m
    out["tolerance"] = tol
    return out
