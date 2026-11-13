#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .build-venv
.build-venv/bin/python -m pip install -r requirements.txt pyinstaller
.build-venv/bin/python -m PyInstaller --noconfirm --clean --name ClaudeChatExporter --add-data "web:web" --collect-all reportlab app.py
printf '\nBuild complete: dist/ClaudeChatExporter/\n'
