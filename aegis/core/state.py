import sqlite3
from datetime import date

class AegisStateTracker:
    def __init__(self, db_path: str = "aegis_state.db"):
        self.db_path = db_path
        # We keep the connection open for the lifetime of the tracker
        # This is especially important for :memory: databases
        self.conn = sqlite3.connect(self.db_path)
        self._init_db()
        self.daily_spend_total = self._get_today_spent()

    def _init_db(self):
        cursor = self.conn.cursor()
        # Create daily_budget table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_budget (
                date TEXT PRIMARY KEY,
                spent_amount FLOAT
            )
        """)
        # Create issued_seals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS issued_seals (
                seal_id TEXT PRIMARY KEY,
                amount FLOAT,
                vendor TEXT,
                status TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def _get_today_spent(self) -> float:
        today = date.today().isoformat()
        cursor = self.conn.cursor()
        cursor.execute("SELECT spent_amount FROM daily_budget WHERE date = ?", (today,))
        row = cursor.fetchone()
        return row[0] if row else 0.0

    def can_spend(self, amount: float, max_daily_budget: float) -> bool:
        spent_today = self._get_today_spent()
        return (spent_today + amount) <= max_daily_budget

    def add_spend(self, amount: float):
        today = date.today().isoformat()
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO daily_budget (date, spent_amount) 
            VALUES (?, ?) 
            ON CONFLICT(date) DO UPDATE SET spent_amount = spent_amount + ?
        """, (today, amount, amount))
        self.conn.commit()
        self.daily_spend_total = self._get_today_spent()

    def record_seal(self, seal_id: str, amount: float, vendor: str, status: str = "Issued"):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO issued_seals (seal_id, amount, vendor, status)
            VALUES (?, ?, ?, ?)
        """, (seal_id, amount, vendor, status))
        self.conn.commit()

    def mark_used(self, seal_id: str):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE issued_seals SET status = 'Used' WHERE seal_id = ?", (seal_id,))
        self.conn.commit()

    def is_used(self, seal_id: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("SELECT status FROM issued_seals WHERE seal_id = ?", (seal_id,))
        row = cursor.fetchone()
        return row is not None and row[0] == "Used"

    def close(self):
        if hasattr(self, 'conn'):
            self.conn.close()
