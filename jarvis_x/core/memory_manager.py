import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional


class MemoryManager:
    """Persistent memory helpers for local learning state."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.path.join(Path(__file__).resolve().parents[2], "data", "memory.db")
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS responses (
                    query_hash TEXT PRIMARY KEY,
                    response TEXT,
                    confidence REAL DEFAULT 0.5,
                    last_used TEXT,
                    feedback_count INTEGER DEFAULT 0
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    entity_type TEXT,
                    entity_value TEXT,
                    context TEXT
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    session_id TEXT,
                    timestamp TEXT,
                    user_msg TEXT,
                    bot_response TEXT,
                    feedback INTEGER DEFAULT 0
                )
            """)

    def store_response(self, query: str, response: str, confidence: float = 0.5):
        query_hash = str(hash(query))
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO responses (query_hash, response, confidence, last_used) VALUES (?, ?, ?, datetime('now'))",
                (query_hash, response, confidence)
            )

    def get_response(self, query: str) -> Optional[Dict[str, object]]:
        query_hash = str(hash(query))
        row = self.conn.execute("SELECT * FROM responses WHERE query_hash = ?", (query_hash,)).fetchone()
        return dict(row) if row else None

    def log_conversation(self, session_id: str, user_msg: str, bot_response: str, feedback: int = 0):
        with self.conn:
            self.conn.execute(
                "INSERT INTO conversation_history (session_id, timestamp, user_msg, bot_response, feedback) VALUES (?, datetime('now'), ?, ?, ?)",
                (session_id, user_msg, bot_response, feedback)
            )

    def close(self):
        self.conn.close()
