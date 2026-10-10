"""
Starts the Hex Map Editor.

Double-click run_editor.bat, or in a terminal type:   python editor_main.py
"""

import os
import sys

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"   # hide pygame's hello message

from editor.app import EditorApp

if __name__ == "__main__":
    # "--screenshot file.png" draws one frame, saves it and quits (for testing).
    screenshot = None
    if "--screenshot" in sys.argv:
        screenshot = sys.argv[sys.argv.index("--screenshot") + 1]
    EditorApp().run(screenshot_path=screenshot)
