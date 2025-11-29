import argparse
from getpass import getpass

from core.db import init_db
from core.security import create_user, verify_user
from core.crypto import encrypt, decrypt, wipe_string
from core.repository import create_entry, list_entries, get_entry, delete_entry


def cmd_init():
    print("=== Initialize password vault ===")
    username = input("Choose username: ").strip()
    if not username:
        print("Username required.")
        return

    master = getpass("Create master password: ")
    master2 = getpass("Confirm master password: ")
    if master != master2:
        print("Passwords do not match.")
        return

    if len(master) < 8:
        print("Master password too short (min 8 chars).")
        return

    init_db()
    try:
        create_user(username, master)
    except ValueError as e:
        print("Error:", e)
        return

    print("Vault initialized for user:", username)
    master = wipe_string(master)
    master2 = wipe_string(master2)


def authenticate():
    username = input("Username: ").strip()
    if not username:
        print("Username required.")
        return None, None, None

    master = getpass("Master password: ")
    try:
        user_id, key = verify_user(username, master)
    except ValueError as e:
        print(e)
        return None, None, None

    # symbolic wipe
    master = wipe_string(master)
    return username, user_id, key


def cmd_add():
    print("=== Add entry ===")
    username, user_id, key = authenticate()
    if user_id is None:
        return

    name = input("Name (e.g. GitHub): ").strip()
    if not name:
        print("Name is required.")
        return

    uname = input("Account username: ").strip() or None
    pw = getpass("Account password: ")
    url = input("URL (optional): ").strip() or None
    notes = input("Notes (optional): ").strip() or None

    enc_pw = encrypt(key, pw)
    enc_notes = encrypt(key, notes) if notes else None

    entry_id = create_entry(
        user_id=user_id,
        name=name,
        username=uname,
        password_encrypted=enc_pw,
        url=url,
        notes_encrypted=enc_notes,
    )

    print(f"Entry created with ID: {entry_id}")

    # wipe sensitive stuff
    pw = wipe_string(pw)
    notes = wipe_string(notes)


def cmd_list():
    print("=== List entries ===")
    username, user_id, key = authenticate()
    if user_id is None:
        return

    rows = list_entries(user_id)
    if not rows:
        print("No entries.")
        return

    print(f"\nEntries for {username}:\n")
    print(f"{'ID':<5}{'Name':<20}{'Username':<20}{'URL'}")
    print("-" * 60)
    for r in rows:
        print(
            f"{r['id']:<5}{(r['name'] or ''):<20}{(r['username'] or ''):<20}{r['url'] or ''}"
        )
    print()


def cmd_show(entry_id: int | None):
    if not entry_id:
        print("Error: --id required for show")
        return

    print("=== Show entry ===")
    _, user_id, key = authenticate()
    if user_id is None:
        return

    row = get_entry(user_id, entry_id)
    if not row:
        print("Entry not found.")
        return

    pw = decrypt(key, row["password_encrypted"])
    notes = ""
    if row["notes_encrypted"]:
        notes = decrypt(key, row["notes_encrypted"])

    print("\nEntry details:")
    print(f"Name: {row['name']}")
    print(f"Username: {row['username']}")
    print(f"Password: {pw}")
    print(f"URL: {row['url']}")
    if notes:
        print(f"Notes: {notes}")
    print()

    # wipe decrypted values
    pw = wipe_string(pw)
    notes = wipe_string(notes)


def cmd_delete(entry_id: int | None):
    if not entry_id:
        print("Error: --id required for delete")
        return

    print("=== Delete entry ===")
    _, user_id, key = authenticate()
    if user_id is None:
        return

    confirm = input(f"Type YES to delete entry {entry_id}: ").strip()
    if confirm != "YES":
        print("Aborted.")
        return

    ok = delete_entry(user_id, entry_id)
    if not ok:
        print("Entry not found or not owned by you.")
        return

    print(f"Entry {entry_id} deleted.")


def main():
    parser = argparse.ArgumentParser(description="Standalone Password Manager CLI")
    parser.add_argument("cmd", choices=["init", "add", "list", "show", "delete"])
    parser.add_argument("--id", type=int, help="Entry ID for show/delete")

    args = parser.parse_args()

    if args.cmd == "init":
        cmd_init()
    elif args.cmd == "add":
        cmd_add()
    elif args.cmd == "list":
        cmd_list()
    elif args.cmd == "show":
        cmd_show(args.id)
    elif args.cmd == "delete":
        cmd_delete(args.id)


if __name__ == "__main__":
    main()
