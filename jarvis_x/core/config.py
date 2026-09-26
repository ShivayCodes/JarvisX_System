"""Configuration management for JARVIS-X."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Platform detection
IS_WINDOWS = sys.platform == "win32"
IS_LINUX = sys.platform == "linux"
IS_MAC = sys.platform == "darwin"

# Load environment
load_dotenv()


class Config:
    """Central configuration object for JARVIS-X."""

    # Paths
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    DATASET_POOL_DIR = BASE_DIR / "dataset_pool"
    DB_PATH = DATA_DIR / "jarvis.db"
    MEMORY_PATH = DATA_DIR / "memory"
    EMBEDDINGS_PATH = DATA_DIR / "embeddings"

    # AI Models
    HF_MODEL = os.getenv("JARVISX_HF_MODEL", "HuggingFaceTB/SmolLM2-360M-Instruct")
    EMBEDDING_MODEL = os.getenv("JARVISX_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    # LLM Parameters
    MAX_NEW_TOKENS = int(os.getenv("JARVISX_MAX_NEW_TOKENS", "256"))
    TEMPERATURE = float(os.getenv("JARVISX_TEMPERATURE", "0.3"))
    TOP_P = float(os.getenv("JARVISX_TOP_P", "0.9"))

    # Features
    ENABLE_VOICE = os.getenv("JARVISX_ENABLE_VOICE", "false").lower() == "true"
    ENABLE_VISION = os.getenv("JARVISX_ENABLE_VISION", "false").lower() == "true"

    @classmethod
    def ensure_directories(cls):
        """Create required directories if they don't exist."""
        for directory in [cls.DATA_DIR, cls.DATASET_POOL_DIR, cls.MEMORY_PATH, cls.EMBEDDINGS_PATH]:
            directory.mkdir(parents=True, exist_ok=True)
