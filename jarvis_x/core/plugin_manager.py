import os
import importlib
import pkgutil
from typing import Dict

from jarvis_x.core.config import Config


class PluginManager:
    def __init__(self, engine):
        self.engine = engine
        self.skills: Dict[str, object] = {}

    def discover(self):
        skills_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills")
        if not os.path.isdir(skills_dir):
            return
        for importer, modname, ispkg in pkgutil.iter_modules([skills_dir]):
            if modname == "base" or modname.startswith("_"):
                continue
            try:
                mod = importlib.import_module(f"jarvis_x.skills.{modname}")
                if hasattr(mod, "register"):
                    mod.register(self.engine, self)
            except Exception as e:
                print(f"[PluginManager] Failed to load {modname}: {e}")

    def register_skill(self, name: str, handler):
        self.skills[name] = handler
        self.engine.kb.log_learning("plugin_loaded", name)
