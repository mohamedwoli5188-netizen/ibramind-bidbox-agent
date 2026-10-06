#!/usr/bin/env bash
set -euo pipefail
python3 -m venv .venv 2>/dev/null || true
source .venv/bin/activate
python -m pip -q install -r requirements.txt
python -m unittest -v tests/test_demo.py
python -m bidbox.agent "$@"
echo "Output: outputs/evaluation_pack.json"
