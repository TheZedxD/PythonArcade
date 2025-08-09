@echo off
setlocal
set ROOT=%~dp0..
call "%ROOT%\.venv\Scripts\activate"
python "%ROOT%\arcade\main.py"
