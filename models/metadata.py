import sqlite3
from typing import Optional


class MetadataModel:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def init_db(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS vars (
                    key VARCHAR(256) PRIMARY KEY,
                    value TEXT
                )
            """)
            self.conn.commit()

    def set_var(self, key: str, value: str):
        with self.conn:
            self.conn.execute("""
                INSERT INTO vars (key, value) 
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """, (key, value))

    def get_var(self, key: str) -> Optional[str]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT value FROM vars WHERE key = ?
        """, (key,))
        row = cursor.fetchone()
        return row[0] if row else None
