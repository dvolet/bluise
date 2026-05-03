from utils.db import get_connection

# =========================
# COURSES
# =========================

def get_all_courses():
    conn = get_connection()
    courses = conn.execute("SELECT * FROM courses").fetchall()
    conn.close()
    return courses


def get_course(course_id):
    conn = get_connection()
    course = conn.execute(
        "SELECT * FROM courses WHERE id = ?",
        (course_id,)
    ).fetchone()
    conn.close()
    return course


def add_course(title, description, content, video_url):
    conn = get_connection()
    conn.execute(
        "INSERT INTO courses (title, description, content, video_url) VALUES (?, ?, ?, ?)",
        (title, description, content, video_url)
    )
    conn.commit()
    conn.close()


def update_course(course_id, title, description, content, video_url):
    conn = get_connection()
    conn.execute(
        "UPDATE courses SET title=?, description=?, content=?, video_url=? WHERE id=?",
        (title, description, content, video_url, course_id)
    )
    conn.commit()
    conn.close()


def delete_course(course_id):
    conn = get_connection()

    # 🔥 SAFE DELETE (removes related data too)
    conn.execute("DELETE FROM enrollments WHERE course_id=?", (course_id,))
    conn.execute("DELETE FROM progress WHERE course_id=?", (course_id,))
    conn.execute("DELETE FROM lessons WHERE course_id=?", (course_id,))
    conn.execute("DELETE FROM courses WHERE id=?", (course_id,))

    conn.commit()
    conn.close()


# =========================
# USER COURSES (FIXED - SINGLE VERSION)
# =========================

def get_user_courses(user_id):
    conn = get_connection()

    courses = conn.execute("""
        SELECT c.*, 
               COALESCE(p.progress, 0) AS progress
        FROM courses c
        JOIN enrollments e ON c.id = e.course_id
        LEFT JOIN progress p 
            ON c.id = p.course_id 
            AND p.user_id = e.user_id
        WHERE e.user_id = ?
    """, (user_id,)).fetchall()

    conn.close()
    return courses


# =========================
# ENROLLMENT (FIXED - NO DUPLICATES)
# =========================

def enroll_user(user_id, course_id):
    conn = get_connection()

    existing = conn.execute("""
        SELECT id FROM enrollments 
        WHERE user_id=? AND course_id=?
    """, (user_id, course_id)).fetchone()

    if not existing:
        conn.execute(
            "INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)",
            (user_id, course_id)
        )
        conn.commit()

    conn.close()


# =========================
# START COURSE PROGRESS
# =========================

def start_course(user_id, course_id):
    conn = get_connection()

    existing = conn.execute("""
        SELECT id FROM progress
        WHERE user_id=? AND course_id=?
    """, (user_id, course_id)).fetchone()

    if not existing:
        conn.execute("""
            INSERT INTO progress (user_id, course_id, progress)
            VALUES (?, ?, 0)
        """, (user_id, course_id))

    conn.commit()
    conn.close()


# =========================
# COUNT
# =========================

def get_course_count():
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) as total FROM courses").fetchone()
    conn.close()
    return count["total"]
