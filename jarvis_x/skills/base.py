class BaseSkill:
    """Extend this class to create a new skill plugin."""
    name = "base"
    description = ""
    triggers = []

    def __init__(self, engine, plugin_manager):
        self.engine = engine
        self.pm = plugin_manager

    def register(self):
        for trigger in self.triggers:
            self.pm.register_skill(trigger, self)


def register(engine, plugin_manager):
    """Override in each skill to auto-register."""
    pass
