@echo off
rem Double-click this file to start the Hex Map Editor.
cd /d "%~dp0"
python editor_main.py
rem If something went wrong, keep the window open so the error can be read.
if errorlevel 1 pause
