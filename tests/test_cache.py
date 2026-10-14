"""Cache-correctness tests on a tiny randomly initialised Qwen2 model (fp32, CPU) with the real
Qwen2.5 tokenizer. They check the *logic* of exact reuse (token boundaries, cropping, positions,
no contamination) independently of fp16 GPU numerics, which scripts/validate_cache.py covers."""
import pytest
import torch

pytest.importorskip("transformers")
from transformers import AutoTokenizer, Qwen2Config, Qwen2ForCausalLM  # noqa: E402

from src.baselines import REGISTRY  # noqa: E402
from src.cache import kv_utils  # noqa: E402
from src.cache.cache_validation import validate_case, validation_cases  # noqa: E402
from src.cache.engine import CAGEngine, EngineConfig, resolve_model_path  # noqa: E402
from src.data.knowledge import KnowledgeSnapshot, serialize  # noqa: E402
from src.data.loader import load_export  # noqa: E402
from src.data.partitioner import PartitionConfig, partition  # noqa: E402
from src.data.preprocessor import build_documents  # noqa: E402
from src.data.updates import apply_update  # noqa: E402
from src.utils import PROJECT_ROOT  # noqa: E402

MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
EXACT = ["B3_document_cache", "B4_layered", "B5_prefix_invalidation"]


@pytest.fixture(scope="module")
def engine():
    tok = AutoTokenizer.from_pretrained(resolve_model_path(MODEL)[0])
    torch.manual_seed(0)
    cfg = Qwen2Config(vocab_size=151936, hidden_size=64, intermediate_size=128, num_hidden_layers=2,
                      num_attention_heads=4, num_key_value_heads=2, max_position_embeddings=32768,
                      rope_theta=1_000_000.0, tie_word_embeddings=True)
    cfg._attn_implementation = "sdpa"
    model = Qwen2ForCausalLM(cfg).float().eval()
    return CAGEngine(EngineConfig(model_name="tiny-random-qwen2", device="cpu", allow_cpu=True,
                                  max_new_tokens=6), model=model, tokenizer=tok)


@pytest.fixture(scope="module")
def setup():
    raw = load_export(PROJECT_ROOT / "data" / "raw" / "database_export_2026-01-23T02-02-46.json")
    docs = build_documents(raw)[0]
    keep = {"company_profile", "company_stats", "taxonomy_interior_styles", "news_26",
            "project_77", "project_76", "project_73", "project_65", "project_59", "project_47"}
    sel = [d for d in docs if d.doc_id in keep]
    held = next(d for d in docs if d.doc_id == "project_64")
    ordered, _ = partition(sel, PartitionConfig())
    return KnowledgeSnapshot(0, ordered), held


def test_prompt_split_tokenization(engine, setup):
    snap, _ = setup
    ser = serialize(snap, engine.template)
    qtext = engine.template.question_text("Diện tích dự án #77 là bao nhiêu?")
    a = engine.tok(ser.text, add_special_tokens=False)["input_ids"]
    b = engine.tok(qtext, add_special_tokens=False)["input_ids"]
    full = engine.tok.apply_chat_template(
        [{"role": "system", "content": ser.text[len(engine.template.pre):]},
         {"role": "user", "content": "Diện tích dự án #77 là bao nhiêu?"}], tokenize=False, add_generation_prompt=True)
    assert ser.text + qtext == full
    assert a + b == engine.tok(full, add_special_tokens=False)["input_ids"]


@pytest.mark.parametrize("case_idx", range(10))
def test_exact_methods_match_full_recompute(engine, setup, case_idx):
    snap, held = setup
    name, ev = validation_cases(snap, held)[case_idx]
    res = validate_case(engine, snap, ev, EXACT + ["B3a_document_cache_approx"], max_new_tokens=6)
    for m in EXACT:
        r = res["methods"][m]
        assert r["token_ids_equal"], (name, m)
        assert r["status"] == "PASS", (name, m, r)
        assert r["generated_token_agreement"] == 1.0, (name, m)
    approx = res["methods"]["B3a_document_cache_approx"]
    assert approx["token_ids_equal"]  # same tokens, different (approximate) KV
    assert approx["kv_rel_max"] > 1e-3  # missing cross-document attention must show up


def test_reuse_lengths_follow_strategy(engine, setup):
    snap, held = setup
    cases = dict(validation_cases(snap, held))
    ev = cases["03_middle_dynamic_doc"]
    s1 = apply_update(snap, ev)
    reused = {}
    for m in EXACT + ["B1_full_recompute"]:
        b = REGISTRY[m](engine)
        b.initialize(snap)
        reused[m] = b.update(ev, s1)["reused_tokens"]
        stable_end = b.tk.stable_token_end
    assert reused["B1_full_recompute"] == 0
    assert reused["B4_layered"] == stable_end
    assert reused["B5_prefix_invalidation"] >= reused["B3_document_cache"] >= reused["B4_layered"]

    ev = cases["10_stable_document_changes"]  # stable change: layered must invalidate inside the prefix
    b = REGISTRY["B4_layered"](engine)
    b.initialize(snap)
    old_stable_end = b.tk.stable_token_end
    r = b.update(ev, apply_update(snap, ev))
    assert r["reused_tokens"] < old_stable_end


def test_question_does_not_contaminate_cache(engine, setup):
    snap, _ = setup
    b = REGISTRY["B4_layered"](engine)
    b.initialize(snap)
    before = [(k.clone(), v.clone()) for k, v in kv_utils.kv_pairs(b.cache)]
    a1 = b.answer("Công ty có bao nhiêu kỹ sư?")
    a2 = b.answer("Công ty có bao nhiêu kỹ sư?")
    assert a1["generated_ids"] == a2["generated_ids"]
    for (k0, v0), (k1, v1) in zip(before, kv_utils.kv_pairs(b.cache)):
        assert torch.equal(k0, k1) and torch.equal(v0, v1)


def test_stale_keeps_old_cache_and_append_grows(engine, setup):
    snap, held = setup
    ev = dict(validation_cases(snap, held))["03_middle_dynamic_doc"]
    s1 = apply_update(snap, ev)
    st = REGISTRY["B0_stale"](engine)
    st.initialize(snap)
    ids0 = list(st.ids)
    st.update(ev, s1)
    assert st.ids == ids0
    ap = REGISTRY["B2_append_correction"](engine)
    ap.initialize(snap)
    n0 = len(ap.ids)
    r = ap.update(ev, s1)
    assert len(ap.ids) == n0 + r["recomputed_tokens"] and kv_utils.cache_len(ap.cache) == len(ap.ids)
    assert ap.ids[:n0] == ids0
    assert "thay đổi từ" in ap.corrections[0]


def test_rope_rerotation_layer0(engine):
    """Layer-0 keys depend only on the token and its position, so re-rotating keys prefilled at
    position p to p+d must equal prefilling at p+d."""
    ids = engine.tok("Xin chào công ty kiến trúc", add_special_tokens=False)["input_ids"]
    c1, _ = engine.prefill(ids, start_pos=0)
    c2, _ = engine.prefill(ids, start_pos=37)
    k1 = kv_utils.kv_pairs(c1)[0][0]
    k2 = kv_utils.kv_pairs(c2)[0][0]
    rot = kv_utils.rerotate_keys(k1, torch.full((len(ids),), 37.0), engine.inv_freq)
    assert torch.allclose(rot, k2, atol=1e-4)
