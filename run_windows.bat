@echo off
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
  echo Virtual environment not found. Run: python -m venv venv
  pause
  exit /b 1
)
call venv\Scripts\activate
python -m pip install -r requirements.txt
python -m flask --app app init-db
python app.py
pause
