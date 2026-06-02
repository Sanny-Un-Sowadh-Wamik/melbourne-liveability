"""Deploy the liveability dashboard to a public HF **Docker** Space.

Auth: HF token from the standard cache or HF_TOKEN env var — no secret in this file.

Usage:
    python scripts/deploy_hf_space.py --user Sanny2005 --space melbourne-liveability
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parent.parent

FRONTMATTER = """---
title: Melbourne Liveability
emoji: "🗺️"
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Interactive Melbourne suburb liveability map (prototype)
---

# 🗺️ Melbourne Suburb Liveability — live demo

Interactive choropleth for **[melbourne-liveability](https://github.com/Sanny-Un-Sowadh-Wamik/melbourne-liveability)** —
260 real Greater-Melbourne suburbs, a PCA-weighted composite index, and user-adjustable weights.

⚠️ **Methodology prototype:** suburb geometry + transport/walkability/affordability are real;
green space, education, health, safety & demographics are *modelled* placeholders (live OSM/ABS
feeds were unreachable at build time). Not for real decisions.
"""

DOCKERFILE = """FROM python:3.11-slim
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH PYTHONUNBUFFERED=1
WORKDIR /home/user/app
COPY --chown=user requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt
COPY --chown=user . .
EXPOSE 7860
CMD ["streamlit", "run", "dashboard/app.py", \\
     "--server.port=7860", "--server.address=0.0.0.0", \\
     "--server.headless=true", "--browser.gatherUsageStats=false"]
"""


def _stage(stage: Path) -> int:
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    for d in ("dashboard", "src", "config"):
        shutil.copytree(ROOT / d, stage / d)
    shutil.copytree(ROOT / "data" / "sample", stage / "data" / "sample")
    shutil.copy(ROOT / "requirements.txt", stage / "requirements.txt")
    (stage / "README.md").write_text(FRONTMATTER)
    (stage / "Dockerfile").write_text(DOCKERFILE)
    for pat in ("__pycache__", "*.egg-info"):
        for p in stage.rglob(pat):
            shutil.rmtree(p, ignore_errors=True)
    for p in stage.rglob("*.pyc"):
        p.unlink()
    return sum(1 for x in stage.rglob("*") if x.is_file())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", default="Sanny2005")
    ap.add_argument("--space", default="melbourne-liveability")
    args = ap.parse_args()

    repo_id = f"{args.user}/{args.space}"
    api = HfApi()
    api.create_repo(repo_id, repo_type="space", space_sdk="docker", exist_ok=True)
    stage = Path("/tmp/hf_liveability")
    n = _stage(stage)
    print(f"uploading {n} files…")
    api.upload_folder(
        folder_path=str(stage), repo_id=repo_id, repo_type="space", commit_message="Deploy liveability dashboard"
    )
    print("SPACE_URL=https://huggingface.co/spaces/" + repo_id)


if __name__ == "__main__":
    main()
