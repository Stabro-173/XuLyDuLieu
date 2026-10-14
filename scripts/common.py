"""Shared CLI helpers: engine construction and environment capture."""
import json
import platform
import subprocess
import sys

import _bootstrap  # noqa: F401
from src.cache.engine import CAGEngine, EngineConfig


def make_engine(model_cfg: dict, device: str = "auto", allow_cpu: bool = False) -> CAGEngine:
    return CAGEngine(EngineConfig(
        model_name=model_cfg["name"], device=device, dtype=model_cfg.get("dtype", "auto"),
        attn_implementation=model_cfg.get("attn_implementation", "sdpa"),
        max_new_tokens=model_cfg.get("max_new_tokens", 32), allow_cpu=allow_cpu,
        revision=model_cfg.get("revision"), prefill_chunk=model_cfg.get("prefill_chunk")))


def environment(engine: CAGEngine | None = None) -> dict:
    env = {"python": sys.version, "platform": platform.platform()}
    try:
        env["pip_freeze"] = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True,
                                           text=True, timeout=120).stdout.splitlines()
    except Exception as e:  # pragma: no cover
        env["pip_freeze_error"] = str(e)
    try:
        env["nvidia_smi"] = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version",
                                            "--format=csv,noheader"], capture_output=True, text=True,
                                           timeout=30).stdout.strip()
    except Exception:
        env["nvidia_smi"] = None
    if engine is not None:
        env["engine"] = json.loads(json.dumps(engine.info.__dict__, default=str))
    return env
