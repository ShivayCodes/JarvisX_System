import os
import re
import sqlite3
import json
import datetime
from collections import deque
from typing import Optional, List, Dict

from jarvis_x.core.config import Config


class KnowledgeBase:
    def __init__(self):
        self.conn = sqlite3.connect(Config.DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        with self.conn:
            self.conn.execute("""CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_input TEXT, response TEXT,
                emotion TEXT DEFAULT 'neutral',
                feedback INTEGER DEFAULT 0,
                timestamp TEXT DEFAULT (datetime('now'))
            )""")
            self.conn.execute("""CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern TEXT UNIQUE, response TEXT,
                confidence REAL DEFAULT 0.5,
                weight REAL DEFAULT 1.0,
                timestamp TEXT DEFAULT (datetime('now'))
            )""")
            self.conn.execute("""CREATE TABLE IF NOT EXISTS learning_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event TEXT, detail TEXT,
                timestamp TEXT DEFAULT (datetime('now'))
            )""")

    def save_interaction(self, user_input: str, response: str, emotion: str = "neutral"):
        with self.conn:
            self.conn.execute(
                "INSERT INTO interactions (user_input, response, emotion) VALUES (?, ?, ?)",
                (user_input, response, emotion)
            )

    def learn(self, pattern: str, response: str, confidence: float = 0.7):
        with self.conn:
            self.conn.execute(
                "INSERT OR REPLACE INTO knowledge (pattern, response, confidence) VALUES (?, ?, ?)",
                (pattern.lower(), response, confidence)
            )

    def get_confidence(self, pattern: str) -> float:
        row = self.conn.execute(
            "SELECT confidence FROM knowledge WHERE pattern = ?",
            (pattern.lower(),)
        ).fetchone()
        return float(row["confidence"]) if row else 0.5

    def adjust_confidence(self, pattern: str, delta: float):
        pattern_lower = pattern.lower()
        row = self.conn.execute(
            "SELECT id, confidence FROM knowledge WHERE pattern = ?",
            (pattern_lower,)
        ).fetchone()
        if not row:
            return
        new_conf = max(0.05, min(1.0, row["confidence"] + delta))
        with self.conn:
            self.conn.execute(
                "UPDATE knowledge SET confidence = ? WHERE id = ?",
                (new_conf, row["id"])
            )
            self.log_learning("adjust_confidence", f"{pattern_lower}: {row['confidence']}->{new_conf}")

    def recall(self, text: str) -> Optional[str]:
        words = set(re.findall(r'\b\w{3,}\b', text.lower()))
        if not words:
            return None
        cur = self.conn.execute("SELECT pattern, response, confidence, weight FROM knowledge")
        best, best_score = None, 0
        for pat, resp, conf, weight in cur.fetchall():
            pat_words = set(re.findall(r'\b\w{3,}\b', pat.lower()))
            if not pat_words:
                continue
            if len(pat_words) < 2 and len(words) > len(pat_words) * 3:
                continue
            overlap = len(words & pat_words)
            total = len(words | pat_words)
            if total == 0:
                continue
            len_ratio = min(len(pat_words), len(words)) / max(len(pat_words), len(words))
            jaccard = overlap / total
            exact_boost = 0.15 if overlap == len(pat_words) else 0.0
            score = jaccard * 0.5 + conf * 0.35 * (weight or 1.0) + exact_boost
            if score > best_score and score >= Config.CONFIDENCE_THRESHOLD:
                best_score = score
                best = resp
        return best

    def record_feedback(self, user_input: str, positive: bool):
        with self.conn:
            self.conn.execute(
                "UPDATE interactions SET feedback = ? WHERE user_input = ? AND feedback = 0",
                (1 if positive else -1, user_input)
            )

    def get_last_feedback(self) -> Optional[int]:
        row = self.conn.execute(
            "SELECT feedback FROM interactions ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return row["feedback"] if row else 0

    def find_similar(self, text: str, limit: int = 5) -> List[Dict]:
        words = set(re.findall(r'\b\w{3,}\b', text.lower()))
        if not words:
            return []
        cur = self.conn.execute(
            "SELECT user_input, response, feedback FROM interactions ORDER BY id DESC LIMIT 100"
        )
        scored = []
        for r in cur.fetchall():
            r_words = set(re.findall(r'\b\w{3,}\b', r["user_input"].lower()))
            if not r_words:
                continue
            overlap = len(words & r_words)
            total = len(words | r_words)
            score = overlap / total if total else 0
            if score > 0.3:
                scored.append((score, r["user_input"], r["response"], r["feedback"]))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"input": s[1], "response": s[2], "feedback": s[3]} for s in scored[:limit]]

    def log_learning(self, event: str, detail: str = ""):
        with self.conn:
            self.conn.execute(
                "INSERT INTO learning_log (event, detail) VALUES (?, ?)",
                (event, detail)
            )

    def get_stats(self) -> dict:
        cur = self.conn.execute("SELECT COUNT(*) as c FROM interactions")
        interactions = cur.fetchone()["c"]
        cur = self.conn.execute("SELECT COUNT(*) as c FROM knowledge")
        facts = cur.fetchone()["c"]
        cur = self.conn.execute(
            "SELECT emotion, COUNT(*) as c FROM interactions WHERE emotion != '' GROUP BY emotion"
        )
        emotions = {row["emotion"]: row["c"] for row in cur.fetchall()}
        return {"interactions": interactions, "facts": facts, "emotions": emotions}

    def get_recent_history(self, n: int = 10) -> List[Dict]:
        cur = self.conn.execute(
            "SELECT user_input, response, timestamp FROM interactions ORDER BY id DESC LIMIT ?",
            (n,)
        )
        return [{"in": r["user_input"], "out": r["response"], "ts": r["timestamp"]}
                for r in cur.fetchall()]

    def close(self):
        self.conn.close()
