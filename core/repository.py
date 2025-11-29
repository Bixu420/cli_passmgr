import datetime
from typing import List, Optional
from .db import get_connection
from .logging_config import logger


def create_entry(
    user_id: int,
    name: str,
    username: Optional[str],
    password_encrypted: bytes,
    url: Optional[str],
    notes_encrypted: Optional[bytes],
):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO entries (user_id, name, username, password_encrypted, url, notes_encrypted, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            name,
            username,
            password_encrypted,
            url,
            notes_encrypted,
            datetime.datetime.utcnow().isoformat(timespec="seconds"),
        ),
    )
    conn.commit()
    entry_id = cur.lastrowid
    conn.close()

    logger.info("Entry created user_id=%s entry_id=%s name=%s", user_id, entry_id, name)
    return entry_id


def list_entries(user_id: int) -> list:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, name, username, url
        FROM entries
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_entry(user_id: int, entry_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT *
        FROM entries
        WHERE user_id = ? AND id = ?
        """,
        (user_id, entry_id),
    )
    row = cur.fetchone()
    conn.close()
    return row


def delete_entry(user_id: int, entry_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM entries WHERE user_id = ? AND id = ?",
        (user_id, entry_id),
    )
    deleted = cur.rowcount
    conn.commit()
    conn.close()

    if deleted:
        logger.info("Entry deleted user_id=%s entry_id=%s", user_id, entry_id)
        return True
    else:
        logger.warning("Entry delete failed user_id=%s entry_id=%s", user_id, entry_id)
        return False
