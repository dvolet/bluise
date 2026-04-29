from utils.db import get_connection
from werkzeug.security import generate_password_hash, check_password_hash

def register_user(username, email, password):
    conn = get_connection()
    cursor = conn.cursor()

    hashed_password = generate_password_hash(password)

    try:
        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, hashed_password)
        )
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()


def login_user(email, password):
    conn = get_connection()
    cursor = conn.cursor()

    user = cursor.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()

    conn.close()

    if user and check_password_hash(user["password"], password):
        return user
    return None

def get_user_count():
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) as total FROM users").fetchone()
    conn.close()
    return count["total"]