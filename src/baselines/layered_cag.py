"""B4 - Layered CAG: [instruction][stable prefix][dynamic suffix].

Dynamic-only change  -> keep the stable-prefix KV, drop the *entire* dynamic suffix, re-prefill it.
Stable change        -> fall back to the start of the first changed stable document (everything
                        after it, including the whole dynamic suffix, is recomputed).
The reusable length is always verified against the token-level common prefix."""
from src.baselines.base import PrefixReuseBaseline


class LayeredCAG(PrefixReuseBaseline):
    name = "B4_layered"
    label = "B4 Layered CAG"

    def propose_reuse(self, new_ser, new_tk, new_types) -> int:
        i = self._first_change(new_ser, new_types)
        if i is None:
            return len(new_tk.ids)
        n_stable_old = sum(1 for x in self.types if x == "stable")
        n_stable_new = sum(1 for x in new_types if x == "stable")
        if i >= n_stable_old and i >= n_stable_new:
            # only the dynamic suffix changed: the layer boundary must be at the same token in both
            if new_tk.stable_token_end != self.tk.stable_token_end:
                return min(new_tk.stable_token_end, self.tk.stable_token_end)
            return new_tk.stable_token_end
        self.last_fallback = "stable_changed"
        return self._doc_start_token(new_ser, new_tk, i)
