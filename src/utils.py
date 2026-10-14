"""Small shared helpers: hashing, JSON(L) IO, seeding, timing."""
from __future__ import annotations

import hashlib
import json
import os
import random
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: str | os.PathLike) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: str | os.PathLike, obj: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=str)


def read_json(path: str | os.PathLike) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def append_jsonl(path: str | os.PathLike, rows: Iterable[dict]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")


def read_jsonl(path: str | os.PathLike) -> list[dict]:
    if not Path(path).exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def set_seed(seed: int) -> None:
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import numpy as np

        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def cuda_sync() -> None:
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.synchronize()
    except ImportError:
        pass


@contextmanager
def timed(store: dict, key: str, sync: bool = True):
    """Wall-clock timer (seconds); synchronises CUDA before and after when asked."""
    if sync:
        cuda_sync()
    t0 = time.perf_counter()
    try:
        yield
    finally:
        if sync:
            cuda_sync()
        store[key] = store.get(key, 0.0) + (time.perf_counter() - t0)


def resolve_model_path(name: str) -> tuple[str, str | None]:
    """Prefer a pinned local copy in models/<basename> (with a REVISION file) over the hub id."""
    local = PROJECT_ROOT / "models" / name.split("/")[-1]
    if (local / ".complete").exists():  # written only after all files are downloaded and verified
        rev = (local / "REVISION").read_text().strip() if (local / "REVISION").exists() else None
        return str(local), rev
    return name, None
