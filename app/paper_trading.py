from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class PaperTrading:
    def __init__(self, db_path: Optional[str] = None, initial_balance: Optional[float] = None):
        self.db_path = db_path or os.getenv("PAPER_DB", "paper_trading.db")
        self.initial_balance = initial_balance or float(os.getenv("PAPER_BALANCE", "10000"))
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS account (
                id INTEGER PRIMARY KEY CHECK (id = 1), balance REAL NOT NULL,
                updated_at TEXT NOT NULL
            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT NOT NULL,
                side TEXT NOT NULL, entry REAL NOT NULL, stop_loss REAL NOT NULL,
                take_profit REAL NOT NULL, quantity REAL NOT NULL, risk_amount REAL NOT NULL,
                status TEXT NOT NULL, exit REAL, pnl REAL, opened_at TEXT NOT NULL,
                closed_at TEXT
            )""")
            if conn.execute("SELECT 1 FROM account WHERE id=1").fetchone() is None:
                conn.execute("INSERT INTO account VALUES (1, ?, ?)", (self.initial_balance, self._now()))

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def account(self) -> Dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute("SELECT balance, updated_at FROM account WHERE id=1").fetchone()
        return {"balance": row[0], "updated_at": row[1]}

    def open_trade(self, signal: Dict[str, Any], risk_percent: float = 0.005) -> Dict[str, Any]:
        if signal.get("decision") not in ("BUY", "SELL"):
            raise ValueError("Solo se puede abrir una operación BUY o SELL")
        entry = float(signal["entry"])
        stop = float(signal["stop_loss"])
        target = float(signal["take_profit"])
        distance = abs(entry - stop)
        if distance <= 0:
            raise ValueError("El stop loss debe estar separado de la entrada")
        balance = self.account()["balance"]
        risk_amount = balance * risk_percent
        quantity = risk_amount / distance
        with self._connect() as conn:
            cursor = conn.execute("""INSERT INTO trades
                (symbol, side, entry, stop_loss, take_profit, quantity, risk_amount,
                 status, opened_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'OPEN', ?)""",
                (signal.get("symbol", "XAUUSD"), signal["decision"], entry, stop,
                 target, quantity, risk_amount, self._now()))
            trade_id = cursor.lastrowid
        return self.get_trade(trade_id)

    def close_trade(self, trade_id: int, exit_price: float) -> Dict[str, Any]:
        trade = self.get_trade(trade_id)
        if not trade or trade["status"] != "OPEN":
            raise ValueError("Operación no encontrada o ya cerrada")
        direction = 1 if trade["side"] == "BUY" else -1
        pnl = (float(exit_price) - trade["entry"]) * trade["quantity"] * direction
        with self._connect() as conn:
            conn.execute("UPDATE trades SET status='CLOSED', exit=?, pnl=?, closed_at=? WHERE id=?",
                         (exit_price, pnl, self._now(), trade_id))
            conn.execute("UPDATE account SET balance=balance+?, updated_at=? WHERE id=1",
                         (pnl, self._now()))
        return self.get_trade(trade_id)

    def get_trade(self, trade_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM trades WHERE id=?", (trade_id,)).fetchone()
        return dict(row) if row else None

    def list_trades(self, limit: int = 100) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM trades ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]
