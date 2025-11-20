@echo off
setlocal EnableExtensions

echo Nightfall Survivors playable slice
python -m tools.launch_game --duration 300 %*
