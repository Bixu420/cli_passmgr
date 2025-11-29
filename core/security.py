import datetime
import bcrypt
from .db import get_connection
from .crypto import generate_salt, derive_key
from .logging_config import logger


def create_user(username: str, master_password: str):
    conn = get_connection()
    cur = conn.cursor()

    # check if exists
    cur.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cur.fetchone():
        conn.close()
        raise ValueError("User already exists")

    salt = bcrypt.gensalt()
    pw_hash = bcrypt.hashpw(master_password.encode("utf-8"), salt)

    kdf_salt = generate_salt()

    cur.execute(
        """
        INSERT INTO users (username, password_hash, kdf_salt, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            username,
            pw_hash,
            kdf_salt,
            datetime.datetime.utcnow().isoformat(timespec="seconds"),
        ),
    )
    conn.commit()
    conn.close()

    logger.info("User created username=%s", username)


def verify_user(username: str, master_password: str):
    """
    Verify username + master_password.
    Returns (user_id, encryption_key) on success.
    Raises ValueError on failure.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, password_hash, kdf_salt FROM users WHERE username = ?",
        (username,),
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        logger.warning("Login failed username=%s reason=no_such_user", username)
        raise ValueError("Invalid username or password")

    stored_hash = row["password_hash"]
    if not bcrypt.checkpw(master_password.encode("utf-8"), stored_hash):
        conn.close()
        logger.warning("Login failed username=%s reason=bad_password", username)
        raise ValueError("Invalid username or password")

    user_id = row["id"]
    kdf_salt = row["kdf_salt"]
    key = derive_key(master_password, kdf_salt)

    conn.close()
    logger.info("Login successful username=%s user_id=%s", username, user_id)
    return user_id, key
