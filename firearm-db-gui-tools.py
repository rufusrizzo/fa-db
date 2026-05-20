#!/usr/bin/env python3
"""
firearm-db-tools.py  —  CLI companion for firearms_encrypted.db
================================================================
Usage:
  python firearm-db-tools.py backup   [--label TEXT] [--dir DIR]
  python firearm-db-tools.py export   [--out FILE]
  python firearm-db-tools.py rekey

Run from the same directory as firearms_encrypted.db, or pass --db PATH.
"""

import argparse
import getpass
import os
import sys
import tempfile
from datetime import datetime

try:
    import sqlcipher3
except ImportError:
    sys.exit("Error: sqlcipher3 is not installed. Run: pip install sqlcipher3")

# ── Config ────────────────────────────────────────────────────────────────────
DEFAULT_DB      = "firearms_encrypted.db"
DEFAULT_BACKUPS = "backups"
CIPHER_COMPAT   = 4


# ── Helpers ───────────────────────────────────────────────────────────────────

def prompt_password(prompt: str = "Database password: ") -> str:
    pw = getpass.getpass(prompt)
    if not pw:
        sys.exit("Error: password cannot be empty.")
    return pw


def open_conn(db_path: str, password: str):
    """Open an authenticated SQLCipher connection."""
    conn = sqlcipher3.connect(db_path)
    conn.execute(f"PRAGMA key='{password}';")
    conn.execute(f"PRAGMA cipher_compatibility = {CIPHER_COMPAT};")
    return conn


def verify_password(db_path: str, password: str) -> bool:
    """Return True if the password unlocks the database."""
    try:
        conn = open_conn(db_path, password)
        conn.execute("SELECT count(*) FROM sqlite_master;").fetchone()
        conn.close()
        return True
    except Exception:
        return False


def db_size(path: str) -> str:
    mb = os.path.getsize(path) / (1024 * 1024)
    return f"{mb:.2f} MB"


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_backup(db_path: str, backup_dir: str, label: str | None) -> None:
    """Copy the encrypted DB to a timestamped backup file."""
    password = prompt_password()

    if not verify_password(db_path, password):
        sys.exit("Error: incorrect password or corrupted database.")

    os.makedirs(backup_dir, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    label_part = f"_{label.strip().replace(' ', '-')}" if label else ""
    backup_name = f"firearms_backup_{ts}{label_part}.db"
    backup_path = os.path.join(backup_dir, backup_name)

    print(f"Creating encrypted backup → {backup_path}")

    src  = open_conn(db_path, password)
    dest = sqlcipher3.connect(backup_path)
    dest.execute(f"PRAGMA key='{password}';")
    dest.execute(f"PRAGMA cipher_compatibility = {CIPHER_COMPAT};")

    src.backup(dest)   # page-by-page, safe with WAL mode
    dest.close()
    src.close()

    print(f"Done. ({db_size(backup_path)}) — same password as the live database.")


def cmd_export(db_path: str, out_path: str) -> None:
    """Export a decrypted plain SQLite copy for testing."""
    print("WARNING: the output file will be UNENCRYPTED.")
    print("         Anyone with the file can read all records.")
    confirm = input("Continue? [y/N] ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    password = prompt_password()

    if not verify_password(db_path, password):
        sys.exit("Error: incorrect password or corrupted database.")

    if os.path.exists(out_path):
        overwrite = input(f"'{out_path}' already exists. Overwrite? [y/N] ").strip().lower()
        if overwrite != "y":
            print("Cancelled.")
            return
        os.remove(out_path)

    print(f"Exporting plaintext database → {out_path}")

    conn = open_conn(db_path, password)
    conn.execute(f"ATTACH DATABASE '{out_path}' AS plaintext KEY '';")
    conn.execute("SELECT sqlcipher_export('plaintext');")
    conn.execute("DETACH DATABASE plaintext;")
    conn.close()

    print(f"Done. ({db_size(out_path)})")
    print("Remember to delete this file when you're finished testing.")


def cmd_rekey(db_path: str, backup_dir: str) -> None:
    """Change the database encryption password in-place."""
    print("=== Change Database Password ===")
    print("A backup will be created automatically before any changes are made.")
    print()

    current_pw = prompt_password("Current password: ")

    if not verify_password(db_path, current_pw):
        sys.exit("Error: incorrect password or corrupted database.")

    new_pw = getpass.getpass("New password: ")
    if not new_pw:
        sys.exit("Error: new password cannot be empty.")

    confirm_pw = getpass.getpass("Confirm new password: ")
    if new_pw != confirm_pw:
        sys.exit("Error: passwords do not match.")

    if new_pw == current_pw:
        sys.exit("New password is the same as the current password. Nothing changed.")

    # Step 1: backup before touching anything
    os.makedirs(backup_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    pre_backup = os.path.join(backup_dir, f"firearms_pre_rekey_{ts}.db")

    print(f"\nCreating pre-change backup → {pre_backup}")
    try:
        src  = open_conn(db_path, current_pw)
        dest = sqlcipher3.connect(pre_backup)
        dest.execute(f"PRAGMA key='{current_pw}';")
        dest.execute(f"PRAGMA cipher_compatibility = {CIPHER_COMPAT};")
        src.backup(dest)
        dest.close()
        src.close()
        print(f"Backup saved. ({db_size(pre_backup)})")
    except Exception as e:
        sys.exit(f"Could not create backup: {e}\nPassword NOT changed.")

    # Step 2: rekey
    print("Changing password...")
    try:
        conn = open_conn(db_path, current_pw)
        conn.execute(f"PRAGMA rekey='{new_pw}';")
        conn.close()
        print("Done. Password changed successfully.")
        print("Update your main app session — it will need the new password on next unlock.")
    except Exception as e:
        sys.exit(
            f"Rekey failed: {e}\n"
            f"Your original database is unchanged.\n"
            f"Backup is at: {pre_backup}"
        )


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="CLI tools for the encrypted firearms database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--db", default=DEFAULT_DB, metavar="PATH",
        help=f"Path to the encrypted database (default: {DEFAULT_DB})",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # backup
    p_backup = sub.add_parser("backup", help="Create a timestamped encrypted backup.")
    p_backup.add_argument("--label", metavar="TEXT", help="Optional label appended to the filename.")
    p_backup.add_argument("--dir", default=DEFAULT_BACKUPS, metavar="DIR",
                          help=f"Backup directory (default: {DEFAULT_BACKUPS}/)")

    # export
    p_export = sub.add_parser("export", help="Export a decrypted plain SQLite copy for testing.")
    p_export.add_argument("--out", default="firearms_plain_test.db", metavar="FILE",
                          help="Output filename (default: firearms_plain_test.db)")

    # rekey
    p_rekey = sub.add_parser("rekey", help="Change the database encryption password.")
    p_rekey.add_argument("--dir", default=DEFAULT_BACKUPS, metavar="DIR",
                         help=f"Directory for the automatic pre-change backup (default: {DEFAULT_BACKUPS}/)")

    args = parser.parse_args()

    if not os.path.exists(args.db):
        sys.exit(f"Error: database not found: {args.db}")

    if args.command == "backup":
        cmd_backup(args.db, args.dir, args.label)
    elif args.command == "export":
        cmd_export(args.db, args.out)
    elif args.command == "rekey":
        cmd_rekey(args.db, args.dir)


if __name__ == "__main__":
    main()
