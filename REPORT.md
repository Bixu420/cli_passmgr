# Password Manager CLI – Security & Design Report

## 1. Introduction

This report describes the security design of the Password Manager CLI
application, focusing on:

- Encryption methods  
- Memory management practices  
- Authentication and access control  
- Protection against common vulnerabilities  
- Testing performed to validate security and functionality  

The CLI is intended for local use only, with all secrets stored encrypted
in a SQLite database.

---

## 2. Encryption Methods

### 2.1 Data Encrypted

The following fields are always stored in encrypted form:

- Account passwords (`password_encrypted`)  
- Notes (`notes_encrypted`)  

Usernames, service names, and URLs are considered less sensitive but can be
treated as sensitive depending on threat model; they are stored in plaintext
for usability (search, display) but can be encrypted in a future version.

### 2.2 Algorithms & Libraries

- **Key Derivation**: PBKDF2-HMAC-SHA256  
  - Iterations: 200,000  
  - Salt: 16 bytes randomly generated per user  
- **Password Hashing (Master Password)**: bcrypt  
  - Per-password random salt  
  - Resistant to brute-force attacks  
- **Symmetric Encryption**: Fernet (from `cryptography` library)  
  - Uses AES in authenticated mode (AES-128 with HMAC)
  - Provides confidentiality and integrity of encrypted data  

### 2.3 Key Derivation Flow

1. On user registration (`init` command):
   - Generate KDF salt `kdf_salt` (16 random bytes).
   - Hash master password with bcrypt → `password_hash`.
   - Store `username`, `password_hash`, `kdf_salt` in `users` table.

2. On login (`add`, `list`, `show`, `delete`):
   - Fetch stored `password_hash` and `kdf_salt`.
   - Verify master password with bcrypt.
   - Derive 32-byte key using PBKDF2 with `kdf_salt`.
   - Convert derived key to Fernet key (URL-safe base64).
   - Use this key for encrypt/decrypt operations in this session only.

The encryption key is **never stored on disk**, and is only kept in memory
for the duration of the CLI process.

---

## 3. Authentication & Access Control

### 3.1 Authentication

- Authentication is based on **username + master password**.
- The master password is:
  - Never stored in plaintext.
  - Verified using bcrypt.
- On authentication success:
  - The app returns `(user_id, key)` to higher-level functions.
- On failure:
  - A generic `Invalid username or password` message is shown.
  - A warning is logged.

### 3.2 Access Control Model

- Each credential entry belongs to exactly one user (`user_id`).
- All repository operations enforce ownership:

  - `list_entries(user_id)` filters by `user_id`
  - `get_entry(user_id, entry_id)` filters by both `user_id` and `id`
  - `delete_entry(user_id, entry_id)` deletes only matching user-owned entries

This prevents one user from viewing or deleting another user’s entries,
even if they know the entry ID.

---

## 4. Memory Management Practices

### 4.1 Goals

- Avoid long-lived plaintext secrets in memory.  
- Limit the scope and lifetime of master password and decrypted credentials.  

### 4.2 Techniques Used

- Master password is collected via `getpass()` (not echoed to terminal).
- After authentication and key derivation, variables holding plaintext passwords
  are explicitly set to `None` and allowed to be garbage-collected.
- Decrypted passwords and notes in `show` are held only inside a short-lived
  function scope and wiped at the end.

Example pattern:

```python
pw = decrypt(key, row["password_encrypted"])
print("Password:", pw)
pw = None  # best-effort wiping
```

While Python cannot guarantee immediate memory erasure (due to copies,
interning, and GC behavior), this approach **reduces exposure time** and
keeps secrets out of long-lived data structures and logs.

### 4.3 No Secrets in Logs

- Logging intentionally excludes:
  - master passwords
  - account passwords
  - notes
  - encryption keys
- Logs include only metadata like:
  - username
  - user_id
  - entry_id
  - operation type (add/list/show/delete)
  - outcome (success/failure)

---

## 5. Security Features

### 5.1 Protection Against Unauthorized Access

- Master password required for all sensitive operations (`add`, `list`,
  `show`, `delete`).
- Entries are bound to user IDs; attempts to access or delete another user’s
  entries fail with generic messages.

### 5.2 Input Validation & Error Handling

- `init` enforces minimum master password length and non-empty username.
- Commands requiring entry IDs require `--id`; missing IDs produce a clear
  CLI error rather than a traceback.
- On errors, the CLI prints **generic messages** and avoids exposing internal
  exceptions or stack traces to the user.

### 5.3 Protection Against Common Issues

- **SQL Injection**: The CLI uses Python’s `sqlite3` with parameterized queries
  (e.g., `WHERE user_id = ? AND id = ?`). No SQL strings contain unescaped
  user input interpolation.
- **Information Leakage**:
  - No stack traces printed to the user.
  - No secrets in logs.
  - `list` never shows passwords or notes; only metadata.
- **Brute Force on Vault Contents**:
  - Data encrypted with strong KDF + AES.
  - Bcrypt for master password hashing slows brute-force attacks
    against the master password.

### 5.4 Logging & Audit Trail

- `cli.log` records:
  - User creation events
  - Login success/failure
  - Entry creation and deletion events
- This provides an audit trail for suspicious activity while avoiding
storage of sensitive data.

---

## 6. Testing and Results

### 6.1 Functional Testing

Key functional tests performed (see `TESTS.md` for full details):

- **Initialization (F-INIT-01)**  
  - Result: `vault.db` created, user row inserted, log entry recorded.

- **Add Entry (F-ADD-01)**  
  - Result: Entry stored, `password_encrypted` contains ciphertext, not plaintext.

- **List Entries (F-LIST-01)**  
  - Result: IDs, names, usernames, URLs printed; passwords and notes omitted.

- **Show Entry (F-SHOW-01)**  
  - Result: Decryption returns correct password and notes for a valid ID.

- **Delete Entry (F-DEL-01)**  
  - Result: Entry removed; subsequent list does not show it.

All functional tests behaved as expected.

### 6.2 Access Control Tests

- **AC-USER-01: Per-user List Isolation**  
  - Different user sees only their own entries.  
- **AC-USER-02: Cross-User Show**  
  - Attempt to show another user’s entry returns `Entry not found.`  
- **AC-USER-03: Cross-User Delete**  
  - Attempts to delete entries owned by others fail with
    `Entry not found or not owned by you.`  

All access control tests passed, confirming user isolation.

### 6.3 Error Handling & Validation Tests

- Incorrect master password produces a generic `Invalid username or password`
  with no stack trace.
- Missing `--id` for `show`/`delete` produces a clear CLI usage error.
- Too-short master passwords are rejected at `init`.

These tests show robust, user-friendly error handling that does not reveal
internal details.

### 6.4 Security-Oriented Tests

- **No plaintext secrets in `cli.log`**: Verified by manual inspection.  
- **Encrypted fields unreadable in DB**: `SELECT password_encrypted FROM entries`
  shows ciphertext only.  
- **Master password not stored**: `SELECT password_hash` shows bcrypt hashes,
  distinct from plaintext passwords.

All security tests confirm that the design meets the stated requirements.

---

## 7. Conclusion

The Password Manager CLI provides:

- Strong encryption of stored credentials
- Secure derivation of encryption keys from master passwords
- Best-effort memory management practices to minimize secret exposure
- Robust authentication and access control per user
- Safe error handling and logging without leaking sensitive information

Combined with the test results documented in `TESTS.md`, this
implementation satisfies the requirements for a secure password manager
application, including:

- A secure CLI application with a user manual  
- A detailed report of encryption, memory, and security features  
- A set of test cases and results demonstrating both functionality and security  
