@echo off
setlocal EnableExtensions

echo Running Nightfall Survivors test suite...
python -m pip install -q pytest >nul 2>&1
python -m pytest -q

