@echo off
cd /d "%~dp0"
echo RootCause frontend: http://127.0.0.1:5500
python -m http.server 5500 --bind 127.0.0.1
