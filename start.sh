#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo "首次运行：正在准备本地环境。"
  python3 -m venv .venv
fi
if ! .venv/bin/python -c "import reportlab, markdown_it" >/dev/null 2>&1; then
  .venv/bin/python -m pip install -r requirements.txt
fi
exec .venv/bin/python app.py
