"""Build controlled experiment conditions: knowledge selection under a token budget, partitioning,
synthetic update scenarios and their question sets. Everything is deterministic given the seed."""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from src.data.documents import KnowledgeDoc
from src.data.knowledge import KnowledgeSnapshot, serialize
from src.data.partitioner import PartitionConfig, partition, partition_to_target_ratio
from src.data.qa_generator import QAGenerator, eligible_fields
from src.data.updates import UpdateEvent, UpdateFactory, apply_update

SCENARIOS = {
    # name: (description, number of events)
    "no_update": "control: event with no changes",
    "numeric_area": "project area changes",
    "numeric_investment": "project investment changes",
    "company_count": "company total project count changes",
    "text_location": "project location changes",
    "text_investor": "project investor changes",
    "date_completion": "project completion date changes",
    "multi_field": "area and location of one project change together",
    "multi_doc": "area of three projects changes in one event",
    "repeated": "same field of one project updated in 3 successive versions",
    "sequential": "k successive single-field updates on different projects",
    "append_doc": "a new project document is appended",
    "delete_doc": "a dynamic project document is deleted",
    "stable_edit": "a stable document (company working hours) changes",
}


@dataclass
class Condition:
    condition_id: str
    budget: int
    seed: int
    scenario: str
    position: str  # begin | middle | end | random | n/a
    stable_ratio_target: float | None
    n_sequential: int = 1
    snapshots: list[KnowledgeSnapshot] = field(default_factory=list)
    events: list[UpdateEvent] = field(default_factory=list)
    questions: list[dict] = field(default_factory=list)
    meta: dict = field(default_factory=dict)


def doc_tokens(tok, doc: KnowledgeDoc) -> int:
    return len(tok(doc.text + "\n\n", add_special_tokens=False)["input_ids"])


def header_tokens(tok, template) -> int:
    ser = serialize(KnowledgeSnapshot(0, []), template)
    return len(tok(ser.text, add_special_tokens=False)["input_ids"])


def select_documents(docs: list[KnowledgeDoc], tok, template, budget: int, seed: int,
                     reserve_projects: int = 1) -> tuple[list[KnowledgeDoc], list[KnowledgeDoc]]:
    """Greedy, whole-document selection under `budget` knowledge tokens (no truncation).
    Keeps the stable-kind and project shares roughly balanced. Returns (selected, held_out_projects)."""
    rng = random.Random(seed)
    by_kind = {}
    for d in docs:
        by_kind.setdefault(d.doc_kind, []).append(d)
    projects = sorted(by_kind.get("project", []), key=lambda d: d.source_id)
    # prefer projects with several unambiguous fields (more QA/update material)
    rich = [p for p in projects if {"area_m2", "investment", "completed_date"} <= set(eligible_fields(p))]
    poor = [p for p in projects if p not in rich]
    rng.shuffle(rich)
    rng.shuffle(poor)
    project_q = rich + poor
    held_out = project_q[-reserve_projects:] if reserve_projects else []
    project_q = project_q[: len(project_q) - reserve_projects] if reserve_projects else project_q
    stable_q = list(by_kind.get("taxonomy", [])) + sorted(by_kind.get("news", []), key=lambda d: d.source_id)
    selected = list(by_kind.get("company_profile", [])) + list(by_kind.get("company_stats", []))
    used = header_tokens(tok, template) + sum(doc_tokens(tok, d) for d in selected)
    if used > budget:
        raise ValueError(f"budget {budget} too small for the mandatory company documents ({used})")
    acc = {"stable": 0, "proj": 0}
    queues = {"stable": stable_q, "proj": project_q}
    while queues["stable"] or queues["proj"]:
        order = sorted(queues, key=lambda k: acc[k])
        progressed = False
        for k in order:
            q = queues[k]
            while q:
                d = q[0]
                tc = doc_tokens(tok, d)
                if used + tc <= budget:
                    q.pop(0)
                    selected.append(d)
                    used += tc
                    acc[k] += tc
                    progressed = True
                    break
                q.pop(0)  # does not fit; try the next candidate of this kind
            if progressed:
                break
        if not progressed:
            break
    return selected, held_out


def _pick_by_position(cands: list[KnowledgeDoc], order: list[str], position: str, rng) -> KnowledgeDoc:
    cands = sorted(cands, key=lambda d: order.index(d.doc_id))
    if position == "begin":
        return cands[0]
    if position == "end":
        return cands[-1]
    if position == "middle":
        return cands[len(cands) // 2]
    return rng.choice(cands)


def build_condition(docs: list[KnowledgeDoc], tok, template, *, budget: int, seed: int, scenario: str,
                    position: str = "random", stable_ratio_target: float | None = None,
                    n_sequential: int = 1, qa_sizes: dict | None = None,
                    partition_cfg: PartitionConfig | None = None, corpus_text: str = "") -> Condition:
    rng = random.Random(f"{seed}-{scenario}-{position}-{budget}-{stable_ratio_target}-{n_sequential}")
    selected, held_out = select_documents(docs, tok, template, budget, seed)
    # candidate update targets (always dynamic in every partition) are projects with the needed fields
    field_for = {
        "numeric_area": ["area_m2"], "numeric_investment": ["investment"], "text_location": ["location"],
        "text_investor": ["investor"], "date_completion": ["completed_date"],
        "multi_field": ["area_m2", "location"], "multi_doc": ["area_m2"], "repeated": ["area_m2"],
        "no_update": [], "sequential": [], "append_doc": [], "delete_doc": [], "stable_edit": [],
        "company_count": [],
    }[scenario]
    projs = [d for d in selected if d.doc_kind == "project"]

    if stable_ratio_target is None:
        ordered, _ = partition(selected, partition_cfg or PartitionConfig())
    else:
        # pin all projects that could be update targets + company stats as dynamic (only as many as needed)
        need = [p for p in projs if all(f in eligible_fields(p) for f in field_for)] or projs
        n_pin = 3 if scenario in ("multi_doc", "sequential") else 1
        if scenario == "sequential":
            n_pin = max(n_pin, min(n_sequential, len(projs)))
        pinned = {d.doc_id for d in rng.sample(need, min(n_pin, len(need)))}
        if scenario == "company_count":
            pinned = {"company_stats"}
        ordered = partition_to_target_ratio(selected, stable_ratio_target, pinned, lambda d: doc_tokens(tok, d))
    snap0 = KnowledgeSnapshot(0, ordered)
    snap0.validate_order()
    order = [d.doc_id for d in snap0.docs]
    dyn_projs = [d for d in snap0.dynamic_docs if d.doc_kind == "project"]

    fac = UpdateFactory(seed, corpus_text)
    events: list[UpdateEvent] = []
    snaps = [snap0]

    def push(ev):
        events.append(ev)
        snaps.append(apply_update(snaps[-1], ev))

    def targets(fields):
        c = [d for d in dyn_projs if all(f in eligible_fields(d) for f in fields)]
        if not c:
            raise ValueError(f"no dynamic project has fields {fields}")
        return c

    if scenario == "no_update":
        push(UpdateEvent(fac._id(), "no_update", version_before=0, version_after=1))
    elif scenario in ("numeric_area", "numeric_investment", "text_location", "text_investor",
                      "date_completion", "multi_field"):
        d = _pick_by_position(targets(field_for), order, position, rng)
        push(fac.field_update(snaps[-1], [(d.doc_id, f) for f in field_for], scenario))
    elif scenario == "company_count":
        push(fac.field_update(snaps[-1], [("company_stats", "total_projects")], scenario))
    elif scenario == "multi_doc":
        c = targets(["area_m2"])
        ds = rng.sample(c, min(3, len(c)))
        push(fac.field_update(snaps[-1], [(d.doc_id, "area_m2") for d in ds], scenario))
    elif scenario == "repeated":
        d = _pick_by_position(targets(["area_m2"]), order, position, rng)
        hist = []
        for _ in range(max(n_sequential, 3)):
            ev = fac.field_update(snaps[-1], [(d.doc_id, "area_m2")], scenario,
                                  history={(d.doc_id, "area_m2"): hist})
            hist.append(ev.changes[0].old_value)
            push(ev)
    elif scenario == "sequential":
        fields = ["area_m2", "investment", "completed_date", "location", "investor"]
        pool = [(d, f) for d in dyn_projs for f in fields if f in eligible_fields(d)]
        rng.shuffle(pool)
        used_docs = set()
        for d, f in pool:
            if len(events) >= n_sequential:
                break
            if d.doc_id in used_docs and len(used_docs) < len(dyn_projs):
                continue
            used_docs.add(d.doc_id)
            push(fac.field_update(snaps[-1], [(d.doc_id, f)], scenario))
        if len(events) < n_sequential:
            raise ValueError(f"only {len(events)} sequential updates possible")
    elif scenario == "append_doc":
        if not held_out:
            raise ValueError("no held-out project to append")
        push(fac.add_doc(snaps[-1], held_out[0]))
    elif scenario == "delete_doc":
        d = _pick_by_position(dyn_projs, order, position, rng)
        push(fac.delete_doc(snaps[-1], d.doc_id))
    elif scenario == "stable_edit":
        if snap0.doc("company_profile").knowledge_type != "stable":
            raise ValueError("company_profile is not stable in this partition")
        push(fac.field_update(snaps[-1], [("company_profile", "working_hours")], scenario))
    else:
        raise ValueError(scenario)

    sizes = {"unchanged": 6, "same_doc_unchanged": 2, "old_value_probe": 4, "cross_document": 3,
             "unanswerable": 3, **(qa_sizes or {})}
    questions = QAGenerator(seed).generate(snaps[-1], events, sizes)
    cid = (f"b{budget}_s{seed}_{scenario}_{position}_r{'def' if stable_ratio_target is None else stable_ratio_target}"
           f"_k{n_sequential}")
    return Condition(cid, budget, seed, scenario, position, stable_ratio_target, n_sequential, snaps, events,
                     questions, meta={"n_selected_docs": len(selected),
                                      "held_out": [d.doc_id for d in held_out]})


def describe_positions(cond: Condition, tok, template) -> dict:
    """Token offsets of the first edited document in the full sequence and within the dynamic suffix."""
    from src.cache.token_boundaries import tokenize_knowledge

    s0 = cond.snapshots[0]
    ser = serialize(s0, template)
    tk = tokenize_knowledge(tok, ser)
    touched = [i for ev in cond.events for i in ev.touched_doc_ids]
    starts = [tk.doc_token_spans[d][0] for d in touched if d in tk.doc_token_spans]
    if not starts:
        starts = [len(tk.ids)]  # appended documents start at the end
    first = min(starts)
    dyn_len = len(tk.ids) - tk.stable_token_end
    return {
        "knowledge_tokens_v0": len(tk.ids),
        "stable_tokens": tk.stable_token_end,
        "dynamic_tokens": dyn_len,
        "stable_ratio_actual": tk.stable_token_end / len(tk.ids),
        "doc_tokens_stable": sum(e - s for d, (s, e) in tk.doc_token_spans.items() if s < tk.stable_token_end),
        "doc_tokens_total": sum(e - s for s, e in tk.doc_token_spans.values()),
        "edit_token_offset": first,
        "edit_pos_norm_full": first / len(tk.ids),
        "edit_pos_norm_dynamic": ((first - tk.stable_token_end) / dyn_len) if dyn_len and first >= tk.stable_token_end else None,
    }
