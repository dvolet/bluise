from utils.db import get_connection
from werkzeug.security import generate_password_hash, check_password_hash


# =========================
# REGISTER USER
# =========================
def register_user(username, email, password):
    conn = get_connection()

    hashed_password = generate_password_hash(password)

    try:
        conn.execute(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            (username, email, hashed_password)
        )
        conn.commit()
        return True

    except Exception as e:
        print("REGISTER ERROR:", e)
        return False

    finally:
        conn.close()


# =========================
# LOGIN USER (FIXED & SAFE)
# =========================
def login_user(email, password):
    conn = get_connection()

    user = conn.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    conn.close()

    if not user:
        return None

    # 🔥 SAFE ACCESS (avoids Render / SQLite row issues)
    db_password = dict(user)["password"]

    if check_password_hash(db_password, password):
        return user

    return None


# =========================
# USER COUNT
# =========================
def get_user_count():
    conn = get_connection()
    count = conn.execute(
        "SELECT COUNT(*) as total FROM users"
    ).fetchone()
    conn.close()

    return count["total"]
