"""Skill registry and management."""


class SkillRegistry:
    """Central registry for JARVIS-X skills."""

    def __init__(self):
        """Initialize the skill registry."""
        self.registry = {}

    def register(self, name: str, skill_func):
        """
        Register a new skill.
        
        Args:
            name: Skill name.
            skill_func: Callable that processes a query.
        """
        self.registry[name] = skill_func

    def get(self, name: str):
        """
        Get a skill by name.
        
        Args:
            name: Skill name.
            
        Returns:
            Callable or None if not found.
        """
        return self.registry.get(name)

    def list_skills(self) -> list:
        """List all registered skills."""
        return list(self.registry.keys())
