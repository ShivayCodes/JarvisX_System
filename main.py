#!/usr/bin/env python3
"""
JARVIS-X v7.0 — Self-Learning AI Assistant
CLI: python jarvis_v6.py --cli
GUI: python jarvis_v6.py
Install startup: python jarvis_v6.py --install
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jarvis_x.core.config import Config
from jarvis_x.core.engine import JarvisEngine
from jarvis_x.io.cli import JarvisCLI
from jarvis_x.io.gui import JarvisGUI
from jarvis_x.core.plugin_manager import PluginManager


class AutoStart:
    @staticmethod
    def install():
        script = os.path.abspath(__file__)
        from jarvis_x.core.config import IS_WINDOWS, IS_LINUX, IS_MAC
        if IS_WINDOWS:
            startup = os.path.join(os.getenv("APPDATA", ""),
                                   r"Microsoft\Windows\Start Menu\Programs\Startup")
            if not os.path.isdir(startup):
                print("Startup folder not found.")
                return False
            vbs_content = f'''CreateObject("WScript.Shell").Run """{sys.executable}"" ""{script}""", 0, False'''
            vbs_path = os.path.join(startup, "JarvisX.launch.vbs")
            with open(vbs_path, "w") as f:
                f.write(vbs_content)
            print(f"Auto-start installed: {vbs_path}")
            return True
        elif IS_LINUX:
            from pathlib import Path
            autostart_dir = Path.home() / ".config" / "autostart"
            autostart_dir.mkdir(parents=True, exist_ok=True)
            desktop = autostart_dir / "jarvisx.desktop"
            desktop.write_text(
                f"[Desktop Entry]\nType=Application\nName=JarvisX\n"
                f"Exec={sys.executable} {script}\n"
                f"Terminal=false\nX-GNOME-Autostart-enabled=true\n"
            )
            print(f"Auto-start installed: {desktop}")
            return True
        elif IS_MAC:
            from pathlib import Path
            plist_dir = Path.home() / "Library" / "LaunchAgents"
            plist_dir.mkdir(parents=True, exist_ok=True)
            plist = plist_dir / "com.jarvisx.plist"
            plist.write_text(
                f'<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
                f'"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
                f'<plist version="1.0"><dict>\n'
                f'<key>Label</key><string>com.jarvisx</string>\n'
                f'<key>ProgramArguments</key><array><string>{sys.executable}</string><string>{script}</string></array>\n'
                f'<key>RunAtLoad</key><true/>\n'
                f'<key>KeepAlive</key><false/>\n'
                f'</dict></plist>\n'
            )
            print(f"Auto-start installed: {plist}")
            return True
        print(f"Auto-start not supported on {sys.platform}")
        return False

    @staticmethod
    def remove():
        from jarvis_x.core.config import IS_WINDOWS, IS_LINUX, IS_MAC
        if IS_WINDOWS:
            startup = os.path.join(os.getenv("APPDATA", ""),
                                   r"Microsoft\Windows\Start Menu\Programs\Startup")
            vbs_path = os.path.join(startup, "JarvisX.launch.vbs")
            if os.path.isfile(vbs_path):
                os.remove(vbs_path)
                print("Auto-start removed.")
                return True
            print("No auto-start found.")
            return False
        elif IS_LINUX:
            from pathlib import Path
            desktop = Path.home() / ".config" / "autostart" / "jarvisx.desktop"
            if desktop.exists():
                desktop.unlink()
                print("Auto-start removed.")
                return True
            print("No auto-start found.")
            return False
        elif IS_MAC:
            from pathlib import Path
            plist = Path.home() / "Library" / "LaunchAgents" / "com.jarvisx.plist"
            if plist.exists():
                plist.unlink()
                print("Auto-start removed.")
                return True
            print("No auto-start found.")
            return False
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="JARVIS-X v7.0 - Self-Learning AI Assistant")
    parser.add_argument("--cli", action="store_true", help="Run in CLI mode")
    parser.add_argument("--install", action="store_true", help="Install auto-start on boot")
    parser.add_argument("--remove", action="store_true", help="Remove auto-start")
    args = parser.parse_args()

    if args.install:
        AutoStart.install()
        return
    if args.remove:
        AutoStart.remove()
        return

    engine = JarvisEngine()

    pm = PluginManager(engine)
    pm.discover()

    if args.cli:
        JarvisCLI(engine).run()
    else:
        try:
            import tkinter
            gui = JarvisGUI(engine)
            gui.run()
        except ImportError:
            print("Tkinter not available. Falling back to CLI mode.")
            JarvisCLI(engine).run()


if __name__ == "__main__":
    main()
