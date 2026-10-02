"""
Print a bcrypt hash for APP_PASSWORD_HASH.

    cd backend
    python scripts/hash_password.py

Paste the output into backend/.env inside single quotes:
    APP_PASSWORD_HASH='$2b$12$....'
"""

import getpass

import bcrypt


def main() -> None:
    password = getpass.getpass("New LifeOps password: ")
    confirm = getpass.getpass("Repeat password: ")

    if password != confirm:
        raise SystemExit("Passwords don't match.")

    if len(password.encode()) > 72:
        raise SystemExit("bcrypt only supports passwords up to 72 bytes.")

    print(bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode())


if __name__ == "__main__":
    main()
