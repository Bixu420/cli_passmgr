import sqlite3
from pathlib import Path
from .config import DB_PATH
from .logging_config import logger


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # users table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash BLOB NOT NULL,
            kdf_salt BLOB NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    # entries table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            username TEXT,
            password_encrypted BLOB NOT NULL,
            url TEXT,
            notes_encrypted BLOB,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    conn.commit()
    conn.close()
    logger.info("Database initialized at %s", DB_PATH)
