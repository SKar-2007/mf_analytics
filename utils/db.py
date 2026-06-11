import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

import pandas as pd
from sqlalchemy import create_engine, text

try:
    from config import config
except ImportError:
    config = None


class DatabaseManager:
    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = db_path or (
            config.db_path if config else Path("data/db/bluestock_mf.db")
        )
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._engine = create_engine(f"sqlite:///{self._db_path}")

    @property
    def engine(self):
        return self._engine

    def query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        try:
            with self._engine.connect() as conn:
                return pd.read_sql(text(sql), conn, params=params)
        except Exception:
            return pd.DataFrame()

    def execute(self, sql: str) -> None:
        with self._engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()

    def table_exists(self, name: str) -> bool:
        df = self.query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=:name",
            {"name": name},
        )
        return not df.empty

    def table_row_count(self, name: str) -> int:
        df = self.query(f"SELECT COUNT(*) as cnt FROM {name}")
        return int(df.iloc[0]["cnt"]) if not df.empty else 0

    def list_tables(self) -> List[str]:
        df = self.query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        return df["name"].tolist() if not df.empty else []

    def to_sql(self, df: pd.DataFrame, table: str, **kwargs) -> int:
        df.to_sql(table, self._engine, if_exists="append", index=False, **kwargs)
        return len(df)

    def drop_table(self, name: str) -> None:
        self.execute(f"DROP TABLE IF EXISTS {name}")

    def schema_info(self, table: str) -> List[tuple]:
        with self._engine.connect() as conn:
            result = conn.execute(text(f"PRAGMA table_info({table})"))
            return result.fetchall()

    def summary(self) -> Dict[str, int]:
        return {t: self.table_row_count(t) for t in self.list_tables() if t != "sqlite_sequence"}


db = DatabaseManager()
