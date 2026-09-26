"""Environment initialization for JARVIS-X."""
from pathlib import Path
from jarvis_x.core.config import Config


def initialize_environment() -> str:
    """
    Initialize the JARVIS-X environment.
    
    Returns:
        str: Initialization summary.
    """
    Config.ensure_directories()
    
    summary_lines = [
        "✓ Environment Initialized",
        f"  Data directory: {Config.DATA_DIR}",
        f"  Dataset pool: {Config.DATASET_POOL_DIR}",
        f"  Memory store: {Config.MEMORY_PATH}",
        f"  Embeddings: {Config.EMBEDDINGS_PATH}",
        f"  Database: {Config.DB_PATH}",
    ]
    
    # Create .env if it doesn't exist
    env_path = Config.BASE_DIR / ".env"
    if not env_path.exists():
        example_path = Config.BASE_DIR / ".env.example"
        if example_path.exists():
            import shutil
            shutil.copy(example_path, env_path)
            summary_lines.append(f"  Created .env from template")
    
    return "\n".join(summary_lines)
