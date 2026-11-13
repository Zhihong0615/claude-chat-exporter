@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo First run: preparing the local environment...
  py -3 -m venv .venv || exit /b 1
)
.venv\Scripts\python.exe -c "import reportlab" >nul 2>&1
if errorlevel 1 .venv\Scripts\python.exe -m pip install -r requirements.txt || exit /b 1
.venv\Scripts\python.exe app.py
endlocal
