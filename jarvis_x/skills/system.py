import platform
import sys
from pathlib import Path

from jarvis_x.core.config import Config
from jarvis_x.skills.base import BaseSkill


class SystemSkill(BaseSkill):
    name = "system"
    description = "System info, file operations"

    def handle_sys_info(self, intent):
        return (f"OS: {platform.system()} {platform.release()}\n"
                f"Python: {sys.version.split()[0]}\n"
                f"Arch: {platform.machine()}\n"
                f"Host: {platform.node()}")

    def handle_find_files(self, intent):
        query = intent.entities.get('query', '*')
        found = []
        for base in Config.ALLOWED_DIRS:
            try:
                found.extend(str(p) for p in Path(base).rglob(f"*{query}*") if p.is_file())
            except (PermissionError, OSError):
                continue
        found = found[:10]
        if found:
            return f"Found {len(found)} files:\n" + "\n".join(found[:5])
        return "No files found."


def register(engine, plugin_manager):
    skill = SystemSkill(engine, plugin_manager)
    plugin_manager.register_skill("sys_info", skill.handle_sys_info)
    plugin_manager.register_skill("find_files", skill.handle_find_files)
