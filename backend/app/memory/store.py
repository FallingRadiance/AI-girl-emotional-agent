import sqlite3
import json
import time
from pathlib import Path
from typing import Dict, List

DB_PATH = Path(__file__).resolve().parents[2] / "app_data" / "memory.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


class MemoryStore:
    def __init__(self) -> None:
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()
        self.session_meta: Dict[str, Dict[str, float]] = {}

    def _init_tables(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS short_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                ts REAL NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS long_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                ts REAL NOT NULL,
                UNIQUE(session_id, key, value)
            )
            """
        )
        self.conn.commit()

    def append_short(self, session_id: str, role: str, content: str) -> None:
        now = time.time()
        self.conn.execute(
            "INSERT INTO short_memory(session_id, role, content, ts) VALUES(?,?,?,?)",
            (session_id, role, content, now),
        )
        self.conn.commit()
        # Keep only latest 30 turns per session.
        self.conn.execute(
            """
            DELETE FROM short_memory
            WHERE id IN (
              SELECT id FROM short_memory
              WHERE session_id = ?
              ORDER BY ts DESC
              LIMIT -1 OFFSET 30
            )
            """,
            (session_id,),
        )
        self.conn.commit()

    def list_short(self, session_id: str, limit: int = 12) -> List[Dict[str, str]]:
        rows = self.conn.execute(
            "SELECT role, content, ts FROM short_memory WHERE session_id=? ORDER BY ts DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        out = [{"role": r["role"], "content": r["content"], "ts": str(r["ts"])} for r in rows]
        out.reverse()
        return out

    def add_long(self, session_id: str, key: str, value: str) -> None:
        now = time.time()
        self.conn.execute(
            "INSERT OR IGNORE INTO long_memory(session_id, key, value, ts) VALUES(?,?,?,?)",
            (session_id, key, value, now),
        )
        self.conn.commit()

    def list_long(self, session_id: str, limit: int = 50) -> List[Dict[str, str]]:
        rows = self.conn.execute(
            "SELECT key, value, ts FROM long_memory WHERE session_id=? ORDER BY ts DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        return [{"key": r["key"], "value": r["value"], "ts": str(r["ts"])} for r in rows]

    def touch_user(self, session_id: str) -> None:
        meta = self.session_meta.setdefault(session_id, {})
        meta["last_user_at"] = time.time()

    def touch_agent(self, session_id: str) -> None:
        meta = self.session_meta.setdefault(session_id, {})
        meta["last_agent_at"] = time.time()

    def idle_seconds(self, session_id: str) -> float:
        meta = self.session_meta.get(session_id, {})
        last_user = meta.get("last_user_at", 0.0)
        return max(0.0, time.time() - last_user)

    def should_trigger_proactive(self, session_id: str, threshold_seconds: float) -> bool:
        meta = self.session_meta.get(session_id, {})
        last_user_at = meta.get("last_user_at")
        if not last_user_at:
            # Do not proactively speak before the user has ever sent a message.
            return False

        if time.time() - last_user_at < threshold_seconds:
            return False

        # Only one proactive message per user turn to avoid repeated spam.
        last_proactive_user_at = meta.get("last_proactive_user_at", 0.0)
        return last_proactive_user_at < last_user_at

    def mark_proactive_sent(self, session_id: str) -> None:
        now = time.time()
        meta = self.session_meta.setdefault(session_id, {})
        meta["last_proactive_at"] = now
        meta["last_proactive_user_at"] = meta.get("last_user_at", 0.0)


store = MemoryStore()
