import os
from pathlib import Path

from jarvis_x.core.config import Config


def initialize_environment() -> str:
    """Create offline runtime directories and initialize the local memory database."""
    directories = [
        Config.MEMORY_DIR,
        Config.DATASET_POOL_DIR,
        Config.CACHE_DIR,
        os.path.dirname(Config.DB_PATH),
        os.path.dirname(Config.MEMORY_DB_PATH),
    ]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

    for subdir in ["faq", "documentation", "knowledge", "training"]:
        Path(Config.DATASET_POOL_DIR, subdir).mkdir(parents=True, exist_ok=True)

    try:
        from jarvis_x.memory.store import KnowledgeBase
        kb = KnowledgeBase()
        kb.close()
    except Exception:
        pass

    return (
        "Initialized local environment: "
        f"memory dir={Config.MEMORY_DIR}, dataset pool={Config.DATASET_POOL_DIR}, cache={Config.CACHE_DIR}"
    )
