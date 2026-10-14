"""B5 - Prefix Invalidation: reuse the longest common *token* prefix of old and new sequences."""
from src.baselines.base import PrefixReuseBaseline


class PrefixInvalidation(PrefixReuseBaseline):
    name = "B5_prefix_invalidation"
    label = "B5 Prefix Invalidation"

    def propose_reuse(self, new_ser, new_tk, new_types) -> int:
        return len(new_tk.ids)  # verify_reuse() clamps this to the token LCP
