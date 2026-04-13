import os
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("DB_DIR", str(BASE_DIR / "data"))).resolve()
DB_PATH = Path(os.getenv("DB_PATH", str(DATA_DIR / "tasks.db"))).resolve()


def get_db_connection():
    # Open a SQLite connection and return rows as dictionaries.
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    # Create the tasks table if it does not already exist.
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    print(f"Initializing SQLite database at: {DB_PATH}")
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.commit()
    connection.close()
