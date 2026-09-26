"""Memory storage and retrieval."""
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from jarvis_x.core.config import Config


class MemoryStore:
    """Persistent memory store for JARVIS-X."""

    def __init__(self):
        """Initialize the memory store."""
        Config.ensure_directories()
        self.db_path = Config.DB_PATH
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                response TEXT,
                intent TEXT,
                timestamp TEXT,
                embedding BLOB
            )
        """)
        conn.commit()
        conn.close()

    def store(self, memory_item: dict) -> bool:
        """
        Store a memory item.
        
        Args:
            memory_item: Dictionary containing query, response, intent, timestamp.
            
        Returns:
            bool: Success status.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO memories (query, response, intent, timestamp)
                VALUES (?, ?, ?, ?)
            """, (
                memory_item.get("query"),
                memory_item.get("response"),
                json.dumps(memory_item.get("intent", {})),
                memory_item.get("timestamp", datetime.now().isoformat())
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error storing memory: {e}")
            return False

    def search(self, query: str, limit: int = 5) -> list:
        """
        Search for similar memories.
        
        Args:
            query: Search query.
            limit: Maximum number of results.
            
        Returns:
            list: Matching memory items.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT query, response, intent, timestamp FROM memories
                WHERE query LIKE ? OR response LIKE ?
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", limit))
            results = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "query": r[0],
                    "content": r[1],
                    "intent": json.loads(r[2]),
                    "timestamp": r[3]
                }
                for r in results
            ]
        except Exception as e:
            print(f"Error searching memory: {e}")
            return []

    def count(self) -> int:
        """Get the total number of stored memories."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM memories")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception:
            return 0
