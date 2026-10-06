#!/usr/bin/env bash
set -euo pipefail
python3 -m unittest -v tests/test_demo.py
python3 -m bidbox.agent "$@"
echo "Output: outputs/evaluation_pack.json"
