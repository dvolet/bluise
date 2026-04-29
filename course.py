from utils.db import get_connection


def get_all_courses():
    conn = get_connection()
    courses = conn.execute("SELECT * FROM courses").fetchall()
    conn.close()
    return courses


def get_course(course_id):
    conn = get_connection()
    course = conn.execute(
        "SELECT * FROM courses WHERE id = ?", (course_id,)
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


def get_course_count():
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) as total FROM courses").fetchone()
    conn.close()
    return count["total"]


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
    conn.execute("DELETE FROM courses WHERE id=?", (course_id,))
    conn.commit()
    conn.close()


def enroll_user(user_id, course_id):
    conn = get_connection()
    conn.execute(
        "INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)",
        (user_id, course_id)
    )
    conn.commit()
    conn.close()

def get_user_courses(user_id):
    conn = get_connection()
    courses = conn.execute("""
        SELECT courses.*
        FROM courses
        JOIN enrollments ON courses.id = enrollments.course_id
        WHERE enrollments.user_id = ?
    """, (user_id,)).fetchall()

    conn.close()
    return courses

def start_course(user_id, course_id):
    conn = get_connection()

    existing = conn.execute("""
        SELECT * FROM progress
        WHERE user_id=? AND course_id=?
    """, (user_id, course_id)).fetchone()

    if not existing:
        conn.execute("""
            INSERT INTO progress (user_id, course_id, progress)
            VALUES (?, ?, 0)
        """, (user_id, course_id))

    conn.commit()
    conn.close()

def get_user_courses(user_id):
    conn = get_connection()

    courses = conn.execute("""
        SELECT courses.*, progress.progress
        FROM courses
        JOIN enrollments ON courses.id = enrollments.course_id
        LEFT JOIN progress 
            ON courses.id = progress.course_id 
            AND progress.user_id = enrollments.user_id
        WHERE enrollments.user_id = ?
    """, (user_id,)).fetchall()

    conn.close()
    return courses