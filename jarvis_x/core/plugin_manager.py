"""Plugin discovery and management for JARVIS-X."""
import importlib
from pathlib import Path


class PluginManager:
    """Discovers and manages plugins."""

    def __init__(self, engine):
        """
        Initialize the plugin manager.
        
        Args:
            engine: The JarvisEngine instance.
        """
        self.engine = engine
        self.plugins = {}

    def discover(self):
        """Discover available plugins in the skills directory."""
        skills_dir = Path(__file__).parent.parent / "skills"
        if skills_dir.exists():
            for skill_file in skills_dir.glob("*.py"):
                if skill_file.name.startswith("_"):
                    continue
                skill_name = skill_file.stem
                try:
                    module = importlib.import_module(f"jarvis_x.skills.{skill_name}")
                    if hasattr(module, "register"):
                        module.register(self.engine)
                        self.plugins[skill_name] = module
                except Exception as e:
                    print(f"Warning: Failed to load plugin {skill_name}: {e}")
