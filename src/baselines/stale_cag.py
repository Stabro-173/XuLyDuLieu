"""B0 - Stale CAG: the underlying data changes but the cache is left untouched."""
from src.baselines.base import Baseline


class StaleCAG(Baseline):
    name = "B0_stale"
    label = "B0 Stale (no update)"
    exact = False

    def update(self, event, snapshot) -> dict:
        # Deliberately does nothing: answers keep coming from the original cache.
        self.n_updates += 1
        self.last_update = self._stats_row({}, reused=len(self.ids), recomputed=0, stale=True)
        self.last_update["cache_reuse_ratio"] = None  # reused-but-invalid tensors are not valid reuse
        self.last_update["reused_tokens"] = 0
        self.last_update["stale_tokens_kept"] = len(self.ids)
        return self.last_update
