import os
import platform as _platform
from pathlib import Path

IS_WINDOWS = _platform.system() == "Windows"
IS_LINUX = _platform.system() == "Linux"
IS_MAC = _platform.system() == "Darwin"

_project_root = Path(__file__).resolve().parents[2]
_root_dir = str(_project_root)


class Config:
    OWNER = os.getenv("USER") or os.getenv("USERNAME") or "User"
    DB_PATH = os.path.join(_root_dir, "data", "jarvis_v6.db")
    MEMORY_DB_PATH = os.path.join(_root_dir, "data", "memory.db")
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
    CRITICAL_THINKING = True
    DATASET_POOL_DIR = os.path.join(_root_dir, "dataset_pool")
    CACHE_DIR = os.path.join(_root_dir, "cache")
    TF_IDF_MIN_DF = 1
    TF_IDF_MAX_DF = 0.95
    SIMILARITY_THRESHOLD = 0.35
    MARKOV_ORDER = 2
    WEIGHT_DECAY_RATE = 0.95
    CONFIDENCE_MIN_THRESHOLD = 0.3
    VECTOR_CACHE_SIZE = 10000
    BATCH_FEEDBACK_SIZE = 100
    MEMORY_COMPACTION_INTERVAL = 7
    LLM_ENABLED = True
    HF_MODEL_ID = os.getenv("JARVISX_HF_MODEL", "HuggingFaceTB/SmolLM2-360M-Instruct")
    EMBEDDING_MODEL_ID = os.getenv("JARVISX_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    HF_MAX_NEW_TOKENS = int(os.getenv("JARVISX_MAX_NEW_TOKENS", "256"))
    HF_TEMPERATURE = float(os.getenv("JARVISX_TEMPERATURE", "0.3"))
    HF_TOP_P = float(os.getenv("JARVISX_TOP_P", "0.9"))
    RAG_INDEX_PATH = os.path.join(_root_dir, "cache", "rag_documents.json")
    RAG_MIN_SCORE = 0.35
    SYSTEM_PROMPT = (
        "You are JARVIS-X, a local-first AI assistant. "
        "Your goal is to help the user with any queries. You must follow the instructions below:\n"
        "1. Give concise final answers. Do not expose private chain-of-thought or hidden reasoning.\n"
        "2. If you need info not directly in context, you can make tool calls by writing: [TOOL: name key=val]. Available tools are:\n"
        "   - sys_info: get system info\n"
        "   - find_files: query a file name pattern (use query=\"...\")\n"
        "   - web_open: open a URL in user browser (use url=\"...\")\n"
        "   - web_scrape: scrape and learn from a URL (use url=\"...\")\n"
        "3. If you want to create or edit a web app, a script, or an interactive document, you can generate an Artifact using the tag: [ARTIFACT: filename]content[/ARTIFACT]. Keep the code complete and premium.\n"
        "4. Always output final helpful replies after the </thinking> block."
    )


os.makedirs(Config.MEMORY_DIR, exist_ok=True)
os.makedirs(Config.DATASET_POOL_DIR, exist_ok=True)
os.makedirs(Config.CACHE_DIR, exist_ok=True)
os.makedirs(os.path.dirname(Config.DB_PATH), exist_ok=True)
