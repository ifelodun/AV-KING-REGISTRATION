import os
import getpass

from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

from database import get_db


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# CREATE ADMIN ACCOUNT
# ============================================================

def create_admin():

    print("=" * 60)
    print("AV KING RECRUITMENT SYSTEM")
    print("CREATE ADMINISTRATOR ACCOUNT")
    print("=" * 60)

    username = input("Enter admin username: ").strip()

    if not username:
        print("Username cannot be empty.")
        return

    full_name = input("Enter admin full name: ").strip()

    password = getpass.getpass(
        "Enter admin password: "
    )

    confirm_password = getpass.getpass(
        "Confirm admin password: "
    )

    if not password:
        print("Password cannot be empty.")
        return

    if password != confirm_password:
        print("Passwords do not match.")
        return

    if len(password) < 8:
        print("Password must be at least 8 characters.")
        return

    password_hash = generate_password_hash(
        password
    )

    conn = get_db()

    try:

        with conn.cursor() as cur:

            # Check whether username already exists
            cur.execute(
                """
                SELECT id
                FROM admin_users
                WHERE username = %s
                LIMIT 1
                """,
                (username,)
            )

            existing_admin = cur.fetchone()

            if existing_admin:

                print(
                    f"Admin username '{username}' already exists."
                )

                return

            # Create administrator
            cur.execute(
                """
                INSERT INTO admin_users (
                    username,
                    password_hash,
                    full_name
                )

                VALUES (
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    username,
                    password_hash,
                    full_name or None
                )
            )

        conn.commit()

        print()
        print("=" * 60)
        print("ADMIN ACCOUNT CREATED SUCCESSFULLY")
        print("=" * 60)
        print(f"Username: {username}")
        print("Password: ********")
        print()
        print("You can now log in through:")
        print("/admin/login")
        print("=" * 60)

    except Exception as e:

        conn.rollback()

        print()
        print("ERROR CREATING ADMIN ACCOUNT:")
        print(e)

    finally:

        conn.close()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    create_admin()
