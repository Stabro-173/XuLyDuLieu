from src.baselines.append_correction import AppendCorrection
from src.baselines.document_cache import DocumentCacheApprox, DocumentCacheExact
from src.baselines.full_recompute import FullRecompute
from src.baselines.layered_cag import LayeredCAG
from src.baselines.prefix_invalidation import PrefixInvalidation
from src.baselines.stale_cag import StaleCAG

REGISTRY = {cls.name: cls for cls in (StaleCAG, FullRecompute, AppendCorrection, DocumentCacheExact,
                                      DocumentCacheApprox, LayeredCAG, PrefixInvalidation)}
EXACT_METHODS = ("B3_document_cache", "B4_layered", "B5_prefix_invalidation")
