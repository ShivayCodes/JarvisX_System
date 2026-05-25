import os
import platform as _platform
from pathlib import Path

IS_WINDOWS = _platform.system() == "Windows"
IS_LINUX = _platform.system() == "Linux"
IS_MAC = _platform.system() == "Darwin"

_script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_root_dir = os.path.dirname(_script_dir)


class Config:
    OWNER = os.getenv("USER") or os.getenv("USERNAME") or "User"
    DB_PATH = os.path.join(_root_dir, "jarvis_v6.db")
    MEMORY_DIR = os.path.join(_root_dir, "jarvis_memory")
    BROWSER_PROFILE = os.path.join(os.path.expanduser("~"), ".jarvis_stealth_context")
    HEADLESS = True
    VIEWPORT = {"width": 1366, "height": 768}
    DELAY_MIN = 0.1
    DELAY_MAX = 0.7
    MOUSE_ARC_NOISE = 5.0
    ALLOWED_DIRS = [os.path.expanduser("~")]
    GUI_TITLE = "JARVIS-X v7.0"
    GUI_WIDTH = 800
    GUI_HEIGHT = 600
    APP_NAME = "JarvisX"
    CONTEXT_WINDOW = 50
    CONFIDENCE_THRESHOLD = 0.3


os.makedirs(Config.MEMORY_DIR, exist_ok=True)
