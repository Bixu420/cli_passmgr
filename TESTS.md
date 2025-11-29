# Password Manager CLI – Test Plan & Results

This document defines and summarizes the test cases used to validate the
Password Manager CLI's functionality and security.

---

## 1. Scope

Covers:

- Vault initialization
- User creation & authentication
- Credential CRUD operations
- Per-user access control
- Error handling & input validation
- Secure logging behavior (no secrets)
- Encryption at rest

---

## 2. Functional Test Cases

### F-INIT-01 – Initialize New Vault

**Steps:**
1. Ensure `data/vault.db` does not exist or move it aside.
2. Run `python cli.py init`.
3. Use username `alice`, master password `StrongPass123!`.

**Expected Result:**
- CLI prints: `Vault initialized for user: alice`.
- `data/vault.db` is created.
- `cli.log` contains a user creation event.

**Status:** PASSED

---

### F-INIT-02 – Prevent Duplicate User Registration

**Steps:**
1. With existing user `alice`, rerun `python cli.py init`.
2. Use username `alice` again.

**Expected Result:**
- CLI reports that the user already exists or equivalent error.
- No second user row created.

**Status:** PASSED

---

### F-ADD-01 – Add Entry

**Steps:**
1. Run `python cli.py add`.
2. Authenticate as `alice` with valid master password.
3. Add an entry: `Name=github`, `Username=alice_dev`, `Password=Gh!tHub-Secret`, `URL=https://github.com`, `Notes=personal`.

**Expected Result:**
- CLI prints `Entry created with ID: <id>`.
- `entries` table contains a new row with that `id`.
- `password_encrypted` is non-empty and not equal to `Gh!tHub-Secret`.

**Status:** PASSED

---

### F-LIST-01 – List Entries

**Steps:**
1. Run `python cli.py list`.
2. Authenticate as `alice`.

**Expected Result:**
- CLI prints a table of entries showing:
  - `ID`, `Name`, `Username`, `URL`.
- Passwords and notes are not displayed.

**Status:** PASSED

---

### F-SHOW-01 – Show Entry by ID

**Steps:**
1. Note an `id` from `F-LIST-01`.
2. Run `python cli.py show --id <id>`.
3. Authenticate as `alice`.

**Expected Result:**
- CLI prints entry details including the *correct* decrypted password and notes.

**Status:** PASSED

---

### F-DEL-01 – Delete Entry

**Steps:**
1. Run `python cli.py delete --id <id>` for an existing entry.
2. Authenticate as `alice`.
3. Confirm deletion with `YES` when prompted.

**Expected Result:**
- CLI prints `Entry <id> deleted.`.
- The entry no longer appears in `list`.
- `cli.log` records a delete event.

**Status:** PASSED

---

## 3. Access Control Test Cases

### AC-USER-01 – Per-User List Isolation

**Steps:**
1. Ensure `alice` has entries.
2. Create another user `bob` via `init`.
3. Run `python cli.py list` and log in as `bob`.

**Expected Result:**
- `bob` sees either no entries or only his own (if any).
- `alice`'s entries are not visible.

**Status:** PASSED

---

### AC-USER-02 – Show Other User’s Entry

**Steps:**
1. Note an entry ID belonging to `alice`.
2. Run `python cli.py show --id <alice_id>` and authenticate as `bob`.

**Expected Result:**
- CLI reports `Entry not found.` or equivalent.
- No decrypted data printed.

**Status:** PASSED

---

### AC-USER-03 – Delete Other User’s Entry

**Steps:**
1. Use an entry ID belonging to `alice`.
2. Run `python cli.py delete --id <alice_id>` and log in as `bob`.
3. Confirm deletion with `YES`.

**Expected Result:**
- CLI prints `Entry not found or not owned by you.`.
- Entry remains accessible for `alice`.

**Status:** PASSED

---

## 4. Error Handling & Input Validation Tests

### ERR-AUTH-01 – Wrong Master Password

**Steps:**
1. Run `python cli.py list`.
2. Enter correct username `alice`, but wrong master password.

**Expected Result:**
- CLI prints `Invalid username or password`.
- No stack trace is printed.

**Status:** PASSED

---

### ERR-INIT-01 – Empty Username on Init

**Steps:**
1. Run `python cli.py init`.
2. Press Enter at username prompt.

**Expected Result:**
- CLI prints `Username required.`.
- No DB changes occur.

**Status:** PASSED

---

### ERR-INIT-02 – Short Master Password

**Steps:**
1. Run `python cli.py init`.
2. Provide username, but master password of fewer than 8 characters.

**Expected Result:**
- CLI rejects password with `Master password too short` (or similar).

**Status:** PASSED

---

### ERR-SHOW-01 – Missing --id

**Steps:**
1. Run `python cli.py show` without `--id`.

**Expected Result:**
- CLI prints `Error: --id required for show`.
- Program exits gracefully without DB operations.

**Status:** PASSED

---

### ERR-DEL-01 – Missing --id for Delete

**Steps:**
1. Run `python cli.py delete` without `--id`.

**Expected Result:**
- CLI prints `Error: --id required for delete`.

**Status:** PASSED

---

## 5. Security-Oriented Tests

### SEC-LOG-01 – No Secrets in Logs

**Steps:**
1. Perform init, add, list, show, delete operations.
2. Open `data/cli.log` in a text editor.
3. Search for known master passwords and site passwords.

**Expected Result:**
- No plaintext master passwords or site passwords appear in logs.
- Logs contain only high-level events.

**Status:** PASSED

---

### SEC-DB-01 – Encrypted Passwords in DB

**Steps:**
1. After adding an entry, run:
   ```bash
   sqlite3 data/vault.db "SELECT password_encrypted FROM entries LIMIT 1;"
   ```

**Expected Result:**
- Output appears as unreadable ciphertext, not the plaintext password.

**Status:** PASSED

---

### SEC-DB-02 – Hashed Master Passwords

**Steps:**
1. Run:
   ```bash
   sqlite3 data/vault.db "SELECT password_hash FROM users;"
   ```

**Expected Result:**
- Values appear as bcrypt hashes.
- They are not equal to the master password in plaintext.

**Status:** PASSED

---

## 6. Summary of Results

All planned test cases for:

- Functional behavior  
- Access control  
- Error handling  
- Logging safety  
- Encryption at rest  

have **passed**, demonstrating that the CLI application behaves correctly
and securely under expected usage.

This satisfies the deliverable:

- A secure password manager CLI with a manual  
- A report of encryption, memory management, and security features  
- A set of test cases and results showing security and functionality  
