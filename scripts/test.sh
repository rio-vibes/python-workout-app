#!/usr/bin/env bash
set -euo pipefail

python3 -m pip install -r requirements.txt -r requirements-dev.txt
python3 -m playwright install chromium
pytest -q
