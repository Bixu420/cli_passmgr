# Password Manager CLI (`pmcli`) – User & Operator Manual

## 1. Overview

`pmcli` is a **standalone, local-only password manager** that stores credentials
encrypted in a SQLite database. Access is protected by a **master password**
per user. Goals:

- Strong encryption for stored passwords and notes  
- No plaintext master passwords saved anywhere  
- Simple, secure command-line interface  
- No web interface or external network dependencies  

This manual explains how to install, use, and operate the CLI safely.

---

## 2. Architecture Overview

### 2.1 Components

- **CLI frontend**: `cli.py`
- **Core modules** (under `core/`):
  - `config.py` – paths for DB and log files  
  - `db.py` – SQLite schema + initialization  
  - `crypto.py` – key derivation, encrypt/decrypt, best-effort memory wipe helper  
  - `security.py` – user creation & authentication (bcrypt-based)  
  - `repository.py` – CRUD operations for entries  
  - `logging_config.py` – file-based logging (no secrets)  

- **Data directory**: `data/`
  - `vault.db` – encrypted vault storage  
  - `cli.log` – log file with high-level events (no secrets)  

### 2.2 Data Flow

1. User runs `cli.py` with a command (`init`, `add`, `list`, `show`, `delete`).
2. If needed, the CLI prompts for:
   - vault username
   - master password
3. `security.verify_user`:
   - Fetches bcrypt-hashed password + KDF salt from `users` table
   - Verifies the master password
   - Derives an encryption key using PBKDF2-HMAC-SHA256
4. `repository` functions read/write encrypted data to `vault.db`.
5. Decrypted secrets exist only temporarily in local variables and are wiped as soon as possible.

---

## 3. Installation

### 3.1 Requirements

- Python 3.10 or newer (3.12 tested)
- `venv` or virtualenv support

### 3.2 Project Layout (example)

```text
pmcli/
  cli.py
  requirements.txt
  core/
    __init__.py
    config.py
    crypto.py
    db.py
    logging_config.py
    repository.py
    security.py
  data/
    (vault.db and cli.log will be created automatically)
```

### 3.3 Install Dependencies

From inside `pmcli/`:

```bash
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

Typical `requirements.txt`:

```text
bcrypt
cryptography
```

---

## 4. Database & Files

### 4.1 Locations

Configured in `core/config.py`:

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "vault.db"
LOG_PATH = DATA_DIR / "cli.log"
```

- `vault.db` – SQLite database storing users and encrypted entries  
- `cli.log` – plain text log of high-level events (no sensitive data)  

You can change `DB_PATH` to store the vault elsewhere (e.g., an encrypted drive).

### 4.2 Database Schema (High-Level)

- `users` table
  - `id`, `username`, `password_hash`, `kdf_salt`, `created_at`
- `entries` table
  - `id`, `user_id`, `name`, `username`, `password_encrypted`,
    `url`, `notes_encrypted`, `created_at`

Each entry is linked to the owning user via `user_id`.

---

## 5. Security Model

### 5.1 Master Password

- Each user has a unique **master password**.
- Stored data:
  - `password_hash` – bcrypt hash of the master password  
  - `kdf_salt` – random salt used for key derivation
- The master password itself is **never stored**.

### 5.2 Key Derivation & Encryption

In `core/crypto.py`:

- Key derivation: PBKDF2-HMAC-SHA256 (200,000 iterations)
- The derived 32-byte key is converted to a Fernet key via URL-safe base64.
- Encryption: Fernet (AES in authenticated mode) encrypts:
  - `password_encrypted`
  - `notes_encrypted`

Decryption happens only when:

- `show` command is used for a specific entry ID.

### 5.3 Access Control

- Entries table includes `user_id`.
- Every read or delete operation filters by `(user_id, id)`.
- Users cannot access other users’ entries.

### 5.4 Secure Memory Handling (Best Effort)

- Master password is held just long enough for verification + key derivation.
- After use, variables storing passwords are set to `None` and allowed to be garbage-collected.
- Although Python cannot guarantee eradication from RAM, this pattern reduces exposure time.

### 5.5 Logging

- Log file: `data/cli.log`
- Logs:
  - User creation
  - Login success/failure
  - Entry creation/deletion
- Logs never contain:
  - plaintext passwords
  - master passwords
  - encryption keys
  - decrypted notes

---

## 6. Command Reference

All commands are executed from the `pmcli` directory (with venv activated):

```bash
python cli.py <command> [options]
```

### 6.1 `init` – Initialize a Vault for a User

**Usage:**

```bash
python cli.py init
```

**Flow:**

1. Prompt: `Choose username:`  
2. Prompt: `Create master password:`  
3. Prompt: `Confirm master password:`  

Validation:

- Username cannot be empty.
- Master password must be at least 8 characters.
- Confirmation must match.

On success:

- Database is initialized (if needed).
- User is created in `users` table.
- A log entry is written.

### 6.2 `add` – Add a New Credential Entry

**Usage:**

```bash
python cli.py add
```

**Flow:**

1. Prompt: `Username:` (vault user)  
2. Prompt: `Master password:`  
3. On successful authentication:
   - `Name (e.g. GitHub):`
   - `Account username:`
   - `Account password:` (hidden)
   - `URL (optional):`
   - `Notes (optional):`
4. Password and notes are encrypted with derived key.
5. Entry is stored; CLI prints `Entry created with ID: <id>`.

### 6.3 `list` – List Entries (Safe – No Passwords)

**Usage:**

```bash
python cli.py list
```

**Flow:**

1. Prompt: `Username:`  
2. Prompt: `Master password:`  
3. On success, prints a table:

```text
Entries for alice:

ID   Name                Username            URL
------------------------------------------------------------
3    github              alice_dev           https://github.com
1    mail                alice@mail.com      https://mail.example.com
```

Passwords and notes **never** appear in the list output.

### 6.4 `show` – Show Decrypted Entry by ID

**Usage:**

```bash
python cli.py show --id <id>
```

If `--id` is missing, an error is displayed.

**Flow:**

1. Prompt: `Username:`  
2. Prompt: `Master password:`  
3. Fetch entry with `(user_id, id)`.
4. Decrypt `password_encrypted` and `notes_encrypted`.
5. Print details:

```text
Entry details:
Name: github
Username: alice_dev
Password: <decrypted password>
URL: https://github.com
Notes: personal account
```

Decrypted values are then wiped from local variables (best-effort).

### 6.5 `delete` – Delete Entry by ID

**Usage:**

```bash
python cli.py delete --id <id>
```

If `--id` is missing, displays an error.

**Flow:**

1. Prompt: `Username:`  
2. Prompt: `Master password:`  
3. Prompt: `Type YES to delete entry <id>:`  
4. On confirmation, deletes entry belonging to the user.

If the entry does not exist or belongs to another user, you see:

```text
Entry not found or not owned by you.
```

---

## 7. Input Validation & Error Handling

### 7.1 Input Validation

- `init` rejects:
  - empty username
  - mismatched or too-short master password
- Commands requiring `--id` (`show`, `delete`) enforce it.
- All interactive prompts strip leading/trailing whitespace.

### 7.2 Error Handling

Typical user-facing errors:

- `User already exists`
- `Invalid username or password`
- `Entry not found.`
- `Entry not found or not owned by you.`
- `Error: --id required`

No stack traces or internal details are shown to the user.

---

## 8. Usage Examples

### 8.1 First-Time Setup

```bash
python cli.py init
```

- Create `alice` with strong master password.

### 8.2 Add an Entry

```bash
python cli.py add
```

- Log in as `alice`
- Add `github` entry

### 8.3 List Entries

```bash
python cli.py list
```

- View IDs, names, usernames, URLs

### 8.4 Show an Entry by ID

```bash
python cli.py show --id 3
```

- See full decrypted entry 3

### 8.5 Delete an Entry

```bash
python cli.py delete --id 3
```

- Confirm deletion with `YES`

---

## 9. Troubleshooting

### Forgotten Master Password

- There is **no recovery** mechanism. This is by design for security.
- You must delete `vault.db` and re-initialize if the master password is lost.

### Database Errors or Corruption

- Stop using the tool immediately.
- Restore `vault.db` from a secure backup, if available.

### Log File Size

- Rotate or delete `cli.log` if it grows too large.
- Ensure your log directory is not world-readable on multi-user systems.

---

## 10. Security Notes

- Use a strong, unique master password.
- Prefer storing `vault.db` on an encrypted filesystem.
- Keep your system patched and access-controlled.
- Make secure backups of `vault.db` and store them in encrypted form.

This concludes the user & operator manual for the CLI password manager.
