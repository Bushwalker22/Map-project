@echo off
rem Double-click to create any missing terrain textures in ASSETS\textures.
rem Existing PNG files are left alone, so your own edits are safe.
cd /d "%~dp0"
python tools\generate_textures.py
pause
