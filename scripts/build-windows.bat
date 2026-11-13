@echo off
setlocal
cd /d "%~dp0\.."
py -3 -m venv .build-venv || exit /b 1
call .build-venv\Scripts\activate.bat
python -m pip install -r requirements.txt pyinstaller || exit /b 1
python -m PyInstaller --noconfirm --clean --name ClaudeChatExporter --add-data "web;web" --collect-all reportlab app.py || exit /b 1
echo Build complete: dist\ClaudeChatExporter\
endlocal
