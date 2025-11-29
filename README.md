# Password Manager CLI (`pmcli`) – User & Operator Manual

## 1. Overview

`pmcli` is a **standalone, local-only password manager** that stores credentials
encrypted in a SQLite database. Access is protected by a **master password**
per user. The goals:

- Strong encryption for stored passwords and notes  
- No plaintext master passwords saved anywhere  
- Simple, secure command-line interface  
- No web interface, no external network dependencies  

## 2. Architecture Overview

### 2.1 Components

- **CLI frontend**: `cli.py`
- **Core modules**: `core/`  
  - `config.py` – paths for DB and log files  
  - `db.py` – SQLite schema + initialization  
  - `crypto.py` – key derivation, encrypt/decrypt, memory wipe helper  
  - `security.py` – user creation & authentication (bcrypt-based)  
  - `repository.py` – CRUD operations for entries  
  - `logging_config.py` – file-based logging  

- **Data directory**: `data/`
  - `vault.db` – encrypted vault storage
  - `cli.log` – log file (no secrets logged)

## 3. Installation

### 3.1 Requirements

- Python 3.10+ (3.12 tested)
- `virtualenv` / `venv` module

### 3.2 Install Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install bcrypt cryptography
```

## 4. Database & Files

Paths are defined in `core/config.py`.

## 5. Security Model

- Master password hashed with bcrypt  
- Entry data encrypted with Fernet (AES-128 in GCM mode)  
- PBKDF2-HMAC-SHA256 key derivation  
- Per-user entry isolation  

## 6. Commands

### init  
Initialize vault for a new user.

### add  
Add an entry (encrypted before storing).

### list  
Show all entries **without passwords**.

### show --id N  
Decrypt and show a single entry by ID.

### delete --id N  
Delete an entry belonging to the user.

## 7. Troubleshooting

- Forgotten master password: no recovery possible.
- DB errors: delete `data/vault.db` and re-init vault.

