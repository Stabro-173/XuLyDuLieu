"""Generate notebooks/colab_benchmark.ipynb (kept as code so it stays in sync with the scripts)."""
import nbformat as nbf

import _bootstrap  # noqa: F401
from src.utils import PROJECT_ROOT

md = nbf.v4.new_markdown_cell
code = nbf.v4.new_code_cell

cells = [
    md("# Dynamic Knowledge Updating in CAG — Colab benchmark (SMOKE profile)\n\n"
       "Runs the whole pipeline on a single GPU (T4 16 GB is enough; tested locally on a 4 GB GTX 1650):\n"
       "dataset preparation → synthetic updates/QA → exact-cache validation → 7 methods "
       "(B0–B5 + approximate B3a) → metrics → figures.\n\n"
       "**Runtime → Change runtime type → T4 GPU** before running. All numbers you see are produced by "
       "this run; nothing is precomputed."),
    code("!nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv"),
    md("## 1. Get the project\nEither upload `cag-benchmark.zip` (the repository folder, without `.venv`, "
       "`models`, `.wheels`) to the Colab file browser, or mount Google Drive where the folder lives."),
    code("import os, zipfile\n"
         "USE_DRIVE = False  # set True if the folder is in Google Drive\n"
         "if USE_DRIVE:\n"
         "    from google.colab import drive; drive.mount('/content/drive')\n"
         "    PROJECT = '/content/drive/MyDrive/cag-benchmark'\n"
         "else:\n"
         "    PROJECT = '/content/cag-benchmark'\n"
         "    if not os.path.exists(PROJECT) and os.path.exists('/content/cag-benchmark.zip'):\n"
         "        zipfile.ZipFile('/content/cag-benchmark.zip').extractall('/content')\n"
         "assert os.path.exists(PROJECT), 'upload cag-benchmark.zip or set USE_DRIVE'\n"
         "%cd {PROJECT}"),
    md("## 2. Install dependencies\nColab already ships CUDA PyTorch; only the remaining packages are installed."),
    code("!pip -q install -r requirements-colab.txt\n"
         "import torch, transformers\n"
         "print(torch.__version__, torch.version.cuda, torch.cuda.is_available(), transformers.__version__)\n"
         "assert torch.cuda.is_available(), 'No GPU: use run_smoke.py --device cpu --allow-cpu for a labelled CPU smoke test'"),
    md("## 3. Dataset\nThe source export must be at `data/raw/database_export_2026-01-23T02-02-46.json` "
       "(it is never modified; its SHA-256 is recorded)."),
    code("RAW = 'data/raw/database_export_2026-01-23T02-02-46.json'\n"
         "if not os.path.exists(RAW):\n"
         "    from google.colab import files\n"
         "    up = files.upload()\n"
         "    os.makedirs('data/raw', exist_ok=True)\n"
         "    os.replace(list(up)[0], RAW)\n"
         "!python scripts/prepare_dataset.py\n"
         "import json; prof = json.load(open('data/processed/dataset_profile.json', encoding='utf-8'))\n"
         "print(prof['record_counts']); print(prof['documents_by_kind']); print('tokens:', prof['tokens_by_kind'])"),
    md("## 4. Synthetic updates and evaluation questions"),
    code("!python scripts/generate_benchmark.py --config configs/smoke.yaml\n"
         "print(json.load(open('data/benchmark/smoke/coverage.json', encoding='utf-8')))"),
    md("## 5. Unit tests (data, evaluators, cache logic on a tiny fp32 model)"),
    code("!python -m pytest -q tests"),
    md("## 6. Exact-cache validation on the real model (10 mandated update scenarios)\n"
       "B3/B4/B5 must match one-shot Full Recompute within the dtype tolerance; B3a is approximate and is "
       "expected to deviate."),
    code("!python scripts/validate_cache.py --config configs/smoke.yaml --budget 1024 --out results/smoke/cache_validation.json"),
    md("## 7. Benchmark (SMOKE): build initial caches, apply updates, answer questions, measure"),
    code("!python scripts/run_benchmark.py --config configs/smoke.yaml --out results/smoke"),
    md("## 8. Metrics, tables and figures"),
    code("!python scripts/generate_report.py --results results/smoke\n"
         "import pandas as pd\n"
         "s = pd.read_csv('results/smoke/benchmark_summary.csv')\n"
         "cols = ['baseline','scenario','update_latency_s_mean','query_latency_s_mean','updated_fact_accuracy',\n"
         "        'stale_answer_rate','unchanged_fact_accuracy','cache_reuse_ratio','peak_gpu_allocated_mb','validation_status']\n"
         "s.groupby('baseline')[cols[2:-1]].mean()"),
    code("from IPython.display import Image, display\nimport glob\n"
         "for p in sorted(glob.glob('results/smoke/figures/*.png')):\n    print(p); display(Image(p, width=640))"),
    md("## 9. Export"),
    code("!zip -qr smoke_results.zip results/smoke reports data/benchmark/smoke\n"
         "try:\n    from google.colab import files; files.download('smoke_results.zip')\n"
         "except Exception as e:\n    print('download manually:', e)"),
]
nb = nbf.v4.new_notebook(cells=cells, metadata={
    "accelerator": "GPU", "colab": {"gpuType": "T4"},
    "kernelspec": {"name": "python3", "display_name": "Python 3"}})
out = PROJECT_ROOT / "notebooks" / "colab_benchmark.ipynb"
nbf.write(nb, out)
print("wrote", out)
