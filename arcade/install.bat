@echo off
python -c "import sys; exit(0 if sys.version_info >= (3,9) else 1)" || (
  echo Python 3.9 or higher is required.
  exit /b 1
)
python -m venv venv
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
(
  echo @echo off
  echo call %%~dp0venv\Scripts\activate.bat
  echo python %%~dp0main.py
) > run.bat
