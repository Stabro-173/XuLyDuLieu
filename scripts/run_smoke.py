"""SMOKE profile end to end: cache validation (small budget) + benchmark + report.

Usage: python scripts/run_smoke.py [--device cpu --allow-cpu]
"""
import subprocess
import sys

import _bootstrap  # noqa: F401
from src.utils import PROJECT_ROOT

if __name__ == "__main__":
    extra = sys.argv[1:]
    py = sys.executable
    steps = [
        [py, "scripts/prepare_dataset.py"],
        [py, "scripts/validate_cache.py", "--config", "configs/smoke.yaml", "--budget", "1024",
         "--out", "results/smoke/cache_validation.json", *extra],
        [py, "scripts/run_benchmark.py", "--config", "configs/smoke.yaml", "--out", "results/smoke", *extra],
        [py, "scripts/generate_report.py", "--results", "results/smoke"],
    ]
    for s in steps:
        print(">>", " ".join(s), flush=True)
        subprocess.run(s, cwd=PROJECT_ROOT, check=True)
