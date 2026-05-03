# =========================
# DATABASE CONNECTION
# =========================
def get_connection():
    import os
    import sqlite3

    # Render persistent disk path
    db_path = os.getenv("DB_PATH", "/var/data/database.db")

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# =========================
# CREATE TABLES (SAFE MIGRATION VERSION)
# =========================
def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # =========================
    # USERS TABLE
    # =========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT UNIQUE,
        password TEXT,
        profile_pic TEXT DEFAULT 'default.png'
    )
    """)

    # USERS MIGRATION
    cols = cursor.execute("PRAGMA table_info(users)").fetchall()
    col_names = [c[1] for c in cols]

    if "profile_pic" not in col_names:
        cursor.execute("ALTER TABLE users ADD COLUMN profile_pic TEXT DEFAULT 'default.png'")

    # =========================
    # COURSES TABLE
    # =========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        content TEXT,
        video_url TEXT
    )
    """)

    # =========================
    # ADD PDF COLUMN (SAFE FIX)
    # =========================
    try:
        columns = cursor.execute("PRAGMA table_info(courses)").fetchall()
        column_names = [col[1] for col in columns]

        if "pdf_file" not in column_names:
            cursor.execute("ALTER TABLE courses ADD COLUMN pdf_file TEXT")
    except Exception as e:
        print("PDF column check error:", e)

    # =========================
    # LESSONS TABLE
    # =========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        title TEXT,
        video_url TEXT,
        position INTEGER DEFAULT 1
    )
    """)

    # =========================
    # LESSON PROGRESS
    # =========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lesson_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        lesson_id INTEGER,
        completed INTEGER DEFAULT 0
    )
    """)

    # =========================
    # ENROLLMENTS
    # =========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        course_id INTEGER
    )
    """)

    # =========================
    # PROGRESS
    # =========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        course_id INTEGER,
        progress INTEGER DEFAULT 0
    )
    """)

    # =========================
    # CERTIFICATES (FIXED + SAFE MIGRATION)
    # =========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS certificates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        course_id INTEGER,
        certificate_id TEXT UNIQUE,
        date_issued TEXT
    )
    """)

    # 🔥 SAFE ADD COLUMN (THIS FIXES YOUR ERROR PERMANENTLY)
    cert_cols = cursor.execute("PRAGMA table_info(certificates)").fetchall()
    cert_col_names = [c[1] for c in cert_cols]

    if "serial_number" not in cert_col_names:
        try:
            cursor.execute("""
            ALTER TABLE certificates ADD COLUMN serial_number TEXT
            """)
        except:
            pass

    # =========================
    # PASSWORD RESET
    # =========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS password_resets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        token TEXT NOT NULL,
        expires_at TEXT NOT NULL
    )
    """)

    # INDEX
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_reset_token
    ON password_resets(token)
    """)

    conn.commit()
    conn.close()
