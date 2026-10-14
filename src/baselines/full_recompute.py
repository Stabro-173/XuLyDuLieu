"""B1 - Full Recompute: discard the cache and prefill the whole updated knowledge sequence.
The exact full-prefill *reference* for cache strategies (not a factual-correctness oracle)."""
from src.baselines.base import PrefixReuseBaseline


class FullRecompute(PrefixReuseBaseline):
    name = "B1_full_recompute"
    label = "B1 Full Recompute"

    def propose_reuse(self, new_ser, new_tk, new_types) -> int:
        return 0
