from contextlib import closing
import sqlite3
from typing import Optional
from models.utils import get_dict_cursor


class MetadataModel:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
    def check_db(self) -> bool:
        """检查vars表是否存在"""
        with closing(self._conn.cursor()) as cursor:
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='metadata'
            """)
            return cursor.fetchone() is not None

    def init_db(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key VARCHAR(256) PRIMARY KEY,
                value TEXT
            )
        """)

    def set_var(self, key: str, value: str):
        self._conn.execute("""
            INSERT INTO metadata (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, value))

    def get_var(self, key: str) -> Optional[str]:
        with closing(get_dict_cursor(self._conn)) as cursor:
            cursor.execute("""
                SELECT value FROM metadata WHERE key = ?
            """, (key,))
            row = cursor.fetchone()
            return row['value'] if row else None
