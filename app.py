from flask import Flask, render_template, request, redirect, url_for, session, flash
import re
import os

import random
import smtplib
from email.mime.text import MIMEText

import uuid
from datetime import datetime, timedelta
import qrcode

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import io

from flask import send_file, request

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from utils.db import create_tables, get_connection
from utils.auth import login_user, get_user_count
from utils.course import (
    get_course,
    add_course,
    get_course_count,
    update_course,
    delete_course
)

app = Flask(__name__)

# =========================
# APP CONFIG
# =========================

app.secret_key = "secret123"

UPLOAD_FOLDER = "static/images"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

ADMIN_EMAIL = "elearningonecreativity@gmail.com"

create_tables()

# =========================
# RESET SYSTEM MEMORY
# =========================
reset_codes = {}

# =========================
# EMAIL FUNCTION
# =========================
def send_reset_email(to_email, reset_link):

    sender_email = "elearningonecreativity@gmail.com"
    sender_password = "geaf qxmk tvfi dvbd"

    msg = MIMEText(f"""
Click the link below to reset your password:

{reset_link}

This link expires in 10 minutes.
""")

    msg["Subject"] = "ELOC Password Reset"
    msg["From"] = sender_email
    msg["To"] = to_email

    try:
        print("🚀 TRYING TO SEND EMAIL...")

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()

        print("✅ EMAIL SENT SUCCESSFULLY")

    except Exception as e:
        print("❌ EMAIL ERROR:", e)   

def fix_users_table():
    conn = get_connection()

    columns = conn.execute("PRAGMA table_info(users)").fetchall()
    column_names = [col['name'] for col in columns]

    # ✅ Add status column if missing
    if 'status' not in column_names:
        conn.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'active'")
        print("✅ Added missing 'status' column")

    # ✅ Add profile_pic if missing
    if 'profile_pic' not in column_names:
        conn.execute("ALTER TABLE users ADD COLUMN profile_pic TEXT DEFAULT 'default.png'")
        print("✅ Added missing 'profile_pic' column")

    conn.commit()
    conn.close()


# 👉 RUN FIX AUTOMATICALLY
fix_users_table()

# =========================
# HOME
# =========================
@app.route('/')
def home():

    conn = get_connection()

    featured_courses = conn.execute("""
        SELECT * FROM courses
        ORDER BY id DESC
        LIMIT 6
    """).fetchall()

    conn.close()

    return render_template("index.html", featured_courses=featured_courses)

# =========================
# REGISTER
# =========================
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not email or not password:
            flash("All fields are required!")
            return redirect("/register")

        # =========================
        # STRONG PASSWORD VALIDATION
        # =========================
        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'

        if not re.match(pattern, password):
            flash("Password must include uppercase, lowercase, number, and special character")
            return redirect("/register")

        # =========================
        # DATABASE CONNECTION
        # =========================
        conn = get_connection()

        # =========================
        # PREVENT PASSWORD REUSE
        # =========================
        existing_users = conn.execute("""
            SELECT password FROM users
        """).fetchall()

        for user_row in existing_users:
            if check_password_hash(user_row['password'], password):
                conn.close()
                flash("This password has been used before. Choose a new one.")
                return redirect("/register")

        # =========================
        # HASH PASSWORD
        # =========================
        hashed_password = generate_password_hash(password)

        # =========================
        # INSERT USER
        # =========================
        conn.execute("""
            INSERT INTO users (username, email, password)
            VALUES (?, ?, ?)
        """, (username, email, hashed_password))

        conn.commit()
        conn.close()

        flash("Account created successfully!")
        return redirect("/login")

    return render_template("register.html")

# =========================
# LOGIN
# =========================
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        user = login_user(email, password)

        if not user:
            flash("Invalid login details")
            return redirect('/login')

        try:
            conn = get_connection()

            # 🔍 get full user row
            db_user = conn.execute("""
                SELECT * FROM users WHERE id=?
            """, (user['id'],)).fetchone()

            conn.close()

            if not db_user:
                flash("User not found")
                return redirect('/login')

            # ✅ CLEAN & SAFE STATUS CHECK
            status = db_user['status'] if 'status' in db_user.keys() else 'active'

            if status == 'disabled':
                flash("Your account has been disabled by admin.")
                return redirect('/login')

            # ✅ LOGIN SUCCESS
            session['user_id'] = db_user['id']
            session['username'] = db_user['username']
            session['email'] = db_user['email']
            session['profile_pic'] = db_user['profile_pic'] or 'default.png'

            return redirect(url_for('dashboard'))

        except Exception as e:
            print("LOGIN ERROR:", e)
            flash("Server error. Please try again.")
            return redirect('/login')

    return render_template("login.html")

# =========================
# FORGOT PASSWORD
# =========================
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():

    if request.method == 'POST':

        email = request.form['email']
        print("📩 EMAIL ENTERED:", email)

        conn = get_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE email=?",
            (email,)
        ).fetchone()

        if user:

            token = str(uuid.uuid4())
            expiry = datetime.now() + timedelta(minutes=10)

            conn.execute("""
                INSERT INTO password_resets (email, token, expires_at)
                VALUES (?, ?, ?)
            """, (email, token, expiry))

            conn.commit()
            conn.close()

            reset_link = url_for('reset_password', token=token, _external=True)

            print("🔗 RESET LINK:", reset_link)

            send_reset_email(email, reset_link)

            flash("✅ Reset link sent! Check your email.")
            return redirect(url_for('forgot_password'))

        conn.close()
        flash("Email not found")

    return render_template("forgot_password.html")
# =========================
# RESET PASSWORD
# =========================
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):

    conn = get_connection()

    record = conn.execute("""
        SELECT * FROM password_resets WHERE token=?
    """, (token,)).fetchone()

    if not record:
        conn.close()
        flash("Invalid or expired link")
        return redirect(url_for('forgot_password'))

    # Check expiry
    if datetime.now() > datetime.fromisoformat(record['expires_at']):
        conn.close()
        flash("Reset link expired")
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':

        new_password = request.form['password']

        # =========================
        # STRONG PASSWORD CHECK
        # =========================
        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'

        if not re.match(pattern, new_password):
            flash("Password must include uppercase, lowercase, number, and symbol")
            return redirect(request.url)

        # =========================
        # PREVENT REUSE
        # =========================
        existing_passwords = conn.execute("""
            SELECT password FROM users
        """).fetchall()

        for row in existing_passwords:
            if check_password_hash(row['password'], new_password):
                flash("You cannot reuse an old password")
                return redirect(request.url)

        hashed = generate_password_hash(new_password)

        conn.execute("""
            UPDATE users SET password=? WHERE email=?
        """, (hashed, record['email']))

        conn.execute("""
            DELETE FROM password_resets WHERE token=?
        """, (token,))

        conn.commit()
        conn.close()

        flash("Password reset successful!")
        return redirect(url_for('login'))

    conn.close()
    return render_template("reset_password.html")
# =========================
# DASHBOARD
# =========================
@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_connection()

    # 📚 ALL COURSES (for browsing)
    all_courses = conn.execute("""
        SELECT * FROM courses 
        ORDER BY id DESC
    """).fetchall()

    # 🎯 ENROLLED COURSES WITH PROGRESS
    courses = conn.execute("""
        SELECT c.*,
               COALESCE(p.progress, 0) AS progress
        FROM courses c
        INNER JOIN enrollments e 
            ON c.id = e.course_id
        LEFT JOIN progress p
            ON c.id = p.course_id 
            AND p.user_id = e.user_id
        WHERE e.user_id = ?
        ORDER BY c.id DESC
    """, (user_id,)).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        username=session['username'],
        profile_pic=session.get('profile_pic', 'default.png'),
        all_courses=all_courses,
        courses=courses,
        total_courses=get_course_count(),
        total_users=get_user_count()
    )

# =========================
# COURSE PAGE
# =========================
@app.route('/course/<int:course_id>')
def course(course_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_connection()

    # 📚 GET COURSE
    course = conn.execute("""
        SELECT * FROM courses WHERE id=?
    """, (course_id,)).fetchone()

    # ✅ CHECK ENROLLMENT
    enrolled_check = conn.execute("""
        SELECT * FROM enrollments
        WHERE user_id=? AND course_id=?
    """, (session['user_id'], course_id)).fetchone()

    enrolled = enrolled_check is not None

    # 🎥 GET LESSONS
    lessons = conn.execute("""
        SELECT * FROM lessons
        WHERE course_id=?
        ORDER BY position ASC
    """, (course_id,)).fetchall()

    # ✅ GET COMPLETED LESSONS
    completed_data = conn.execute("""
        SELECT lesson_id FROM lesson_progress
        WHERE user_id=? AND completed=1
    """, (session['user_id'],)).fetchall()

    completed_lessons = [l['lesson_id'] for l in completed_data]

    # =========================
    # 🧠 NEW: AUTO PROGRESS CALCULATION
    # =========================
    total_lessons = len(lessons)
    completed_count = len([l for l in lessons if l['id'] in completed_lessons])

    if total_lessons > 0:
        current_progress = int((completed_count / total_lessons) * 100)
    else:
        current_progress = 0

    # =========================
    # 💾 SAVE/UPDATE PROGRESS (AUTO)
    # =========================
    existing = conn.execute("""
        SELECT * FROM progress
        WHERE user_id=? AND course_id=?
    """, (session['user_id'], course_id)).fetchone()

    if existing:
        conn.execute("""
            UPDATE progress
            SET progress=?
            WHERE user_id=? AND course_id=?
        """, (current_progress, session['user_id'], course_id))
    else:
        conn.execute("""
            INSERT INTO progress (user_id, course_id, progress)
            VALUES (?, ?, ?)
        """, (session['user_id'], course_id, current_progress))

    conn.commit()
    conn.close()

    return render_template(
        "view_course.html",
        course=course,
        progress=current_progress,
        enrolled=enrolled,
        lessons=lessons,
        completed_lessons=completed_lessons
    )
    
@app.route('/course/<int:course_id>/complete', methods=['POST'])
def complete_course(course_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_connection()

    # check existing progress
    row = conn.execute("""
        SELECT progress FROM progress
        WHERE user_id=? AND course_id=?
    """, (session['user_id'], course_id)).fetchone()

    if row:
        new_progress = min(row['progress'] + 20, 100)

        conn.execute("""
            UPDATE progress
            SET progress=?
            WHERE user_id=? AND course_id=?
        """, (new_progress, session['user_id'], course_id))
    else:
        conn.execute("""
            INSERT INTO progress (user_id, course_id, progress)
            VALUES (?, ?, 20)
        """, (session['user_id'], course_id))

    conn.commit()
    conn.close()

    return redirect(url_for('course', course_id=course_id))
        
@app.route('/courses')
def courses():

    conn = get_connection()

    all_courses = conn.execute("""
        SELECT * FROM courses ORDER BY id DESC
    """).fetchall()

    enrolled_ids = []
    progress_data = {}

    if 'user_id' in session:

        # ✅ GET ENROLLED COURSES
        rows = conn.execute("""
            SELECT course_id FROM enrollments WHERE user_id=?
        """, (session['user_id'],)).fetchall()

        enrolled_ids = [row['course_id'] for row in rows]

        # ✅ GET PROGRESS FOR EACH COURSE
        progress_rows = conn.execute("""
            SELECT course_id, progress FROM progress
            WHERE user_id=?
        """, (session['user_id'],)).fetchall()

        progress_data = {row['course_id']: row['progress'] for row in progress_rows}

    conn.close()

    return render_template(
        "courses.html",
        all_courses=all_courses,
        enrolled_ids=enrolled_ids,
        progress_data=progress_data   # ✅ NEW
    )
    
@app.route('/my-courses')
def my_courses():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_connection()

    my_courses_list = conn.execute("""
        SELECT c.*
        FROM courses c
        JOIN enrollments e ON c.id = e.course_id
        WHERE e.user_id = ?
    """, (session['user_id'],)).fetchall()

    enrolled_ids = [course['id'] for course in my_courses_list]

    conn.close()

    return render_template(
        "courses.html",
        all_courses=my_courses_list,
        enrolled_ids=enrolled_ids
    )
@app.route('/enroll/<int:course_id>')
def enroll(course_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_connection()

    # ✅ CHECK IF ALREADY ENROLLED
    existing = conn.execute("""
        SELECT * FROM enrollments
        WHERE user_id=? AND course_id=?
    """, (session['user_id'], course_id)).fetchone()

    # ✅ INSERT ONLY IF NOT EXISTS
    if not existing:
        conn.execute("""
            INSERT INTO enrollments (user_id, course_id)
            VALUES (?, ?)
        """, (session['user_id'], course_id))
        conn.commit()

    conn.close()

    # ✅ REDIRECT BACK TO COURSE PAGE
    return redirect(url_for('course', course_id=course_id))
    
@app.route('/admin/add-course', methods=['GET', 'POST'])
def add_course_page():

    if session.get('email') != ADMIN_EMAIL:
        return "Access Denied"

    if request.method == 'POST':

        title = request.form['title']
        description = request.form['description']
        content = request.form['content']
        video_url = request.form['video_url']

        # =========================
        # 📄 PDF UPLOAD (SAFE ADDITION)
        # =========================
        pdf_file = request.files.get('pdf_file')
        pdf_filename = None

        if pdf_file and pdf_file.filename != "":
            pdf_folder = "static/pdfs"
            os.makedirs(pdf_folder, exist_ok=True)

            filename = secure_filename(pdf_file.filename)
            unique_filename = f"{uuid.uuid4().hex}_{filename}"

            pdf_path = os.path.join(pdf_folder, unique_filename)
            pdf_file.save(pdf_path)

            pdf_filename = unique_filename

        # =========================
        # SAVE TO DATABASE
        # =========================
        conn = get_connection()

        conn.execute("""
            INSERT INTO courses (title, description, content, video_url, pdf_file)
            VALUES (?, ?, ?, ?, ?)
        """, (title, description, content, video_url, pdf_filename))

        conn.commit()
        conn.close()

        return redirect('/courses')

    return render_template("add_course.html")

# =========================
# ADD LESSON (MULTIPLE VIDEOS PER COURSE)
# =========================
@app.route('/admin/add-lesson/<int:course_id>', methods=['GET', 'POST'])
def add_lesson(course_id):

    if session.get('email') != ADMIN_EMAIL:
        return "Access Denied"

    if request.method == 'POST':

        titles = request.form.getlist('title[]')
        video_urls = request.form.getlist('video_url[]')
        positions = request.form.getlist('position[]')

        conn = get_connection()

        for i in range(len(titles)):
            if titles[i].strip() != "" and video_urls[i].strip() != "":
                conn.execute("""
                    INSERT INTO lessons (course_id, title, video_url, position)
                    VALUES (?, ?, ?, ?)
                """, (
                    course_id,
                    titles[i],
                    video_urls[i],
                    int(positions[i]) if positions[i] else i + 1
                ))

        conn.commit()
        conn.close()

        return redirect(f'/course/{course_id}')

    return render_template("add_lesson.html", course_id=course_id)
    
@app.route('/certificate/<int:course_id>')
def certificate(course_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_connection()

    # 📚 GET COURSE
    course = conn.execute("""
        SELECT * FROM courses WHERE id=?
    """, (course_id,)).fetchone()

    # 👤 GET USER
    user = conn.execute("""
        SELECT * FROM users WHERE id=?
    """, (session['user_id'],)).fetchone()

    # 🔥 CHECK USING LESSON SYSTEM (FIXED)
    total_lessons = conn.execute("""
        SELECT COUNT(*) as total FROM lessons WHERE course_id=?
    """, (course_id,)).fetchone()['total']

    completed_lessons = conn.execute("""
        SELECT COUNT(*) as total FROM lesson_progress lp
        JOIN lessons l ON lp.lesson_id = l.id
        WHERE lp.user_id=? AND l.course_id=? AND lp.completed=1
    """, (session['user_id'], course_id)).fetchone()['total']

    if total_lessons == 0 or completed_lessons < total_lessons:
        conn.close()
        return "Complete all lessons first"

    # 🔍 CHECK EXISTING CERTIFICATE
    cert = conn.execute("""
        SELECT * FROM certificates
        WHERE user_id=? AND course_id=?
    """, (session['user_id'], course_id)).fetchone()

    # 🆕 CREATE CERTIFICATE IF NOT EXISTS
    if not cert:
        cert_id = str(uuid.uuid4()).split('-')[0].upper()

        conn.execute("""
            INSERT INTO certificates (user_id, course_id, certificate_id, date_issued)
            VALUES (?, ?, ?, ?)
        """, (
            session['user_id'],
            course_id,
            cert_id,
            datetime.now().strftime("%Y-%m-%d")
        ))

        conn.commit()

        cert = conn.execute("""
            SELECT * FROM certificates
            WHERE user_id=? AND course_id=?
        """, (session['user_id'], course_id)).fetchone()

    # 🔗 GENERATE QR CODE
    verify_url = url_for(
        'verify_certificate',
        cert_id=cert['certificate_id'],
        _external=True
    )

    qr = qrcode.make(verify_url)

    qr_folder = "static/qrcodes"
    os.makedirs(qr_folder, exist_ok=True)

    qr_path = f"{qr_folder}/{cert['certificate_id']}.png"
    qr.save(qr_path)

    conn.close()

    return render_template(
        "certificate.html",
        user=user,
        course=course,
        cert=cert,
        qr_path=qr_path
    )

@app.route('/admin/manage-lessons/<int:course_id>')
def manage_lessons(course_id):

    if session.get('email') != ADMIN_EMAIL:
        return "Access Denied"

    conn = get_connection()

    course = conn.execute("""
        SELECT * FROM courses WHERE id=?
    """, (course_id,)).fetchone()

    lessons = conn.execute("""
        SELECT * FROM lessons
        WHERE course_id=?
        ORDER BY position ASC
    """, (course_id,)).fetchall()

    conn.close()

    return render_template(
        "manage_lessons.html",
        course=course,
        lessons=lessons
    )

@app.route('/admin/edit-lesson/<int:lesson_id>', methods=['POST'])
def edit_lesson(lesson_id):

    if session.get('email') != ADMIN_EMAIL:
        return "Access Denied"

    title = request.form['title']
    video_url = request.form['video_url']
    position = request.form['position']

    conn = get_connection()

    conn.execute("""
        UPDATE lessons
        SET title=?, video_url=?, position=?
        WHERE id=?
    """, (title, video_url, position, lesson_id))

    conn.commit()
    conn.close()

    return redirect(request.referrer)
    
@app.route('/admin/delete-lesson/<int:lesson_id>')
def delete_lesson(lesson_id):

    if session.get('email') != ADMIN_EMAIL:
        return "Access Denied"

    conn = get_connection()

    conn.execute("""
        DELETE FROM lessons WHERE id=?
    """, (lesson_id,))

    conn.commit()
    conn.close()

    return redirect(request.referrer)
    
@app.route('/admin/quick-add-lesson/<int:course_id>', methods=['POST'])
def quick_add_lesson(course_id):

    if session.get('email') != ADMIN_EMAIL:
        return "Access Denied"

    title = request.form['title']
    video_url = request.form['video_url']
    position = request.form['position']

    conn = get_connection()

    conn.execute("""
        INSERT INTO lessons (course_id, title, video_url, position)
        VALUES (?, ?, ?, ?)
    """, (course_id, title, video_url, position))

    conn.commit()
    conn.close()

    return redirect(request.referrer)

@app.route('/admin/delete-course/<int:course_id>')
def delete_course_route(course_id):  # ✅ renamed here

    if session.get('email') != ADMIN_EMAIL:
        return "Access Denied"

    try:
        conn = get_connection()

        # delete lessons first
        conn.execute("DELETE FROM lessons WHERE course_id=?", (course_id,))

        # delete course
        conn.execute("DELETE FROM courses WHERE id=?", (course_id,))

        conn.commit()
        conn.close()

        flash("✅ Course deleted successfully")
        return redirect('/dashboard')

    except Exception as e:
        print("DELETE ERROR:", e)
        return "Error deleting course"

@app.route('/transcript')
def transcript():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_connection()

    data = conn.execute("""
        SELECT c.title, p.progress
        FROM courses c
        JOIN progress p ON c.id = p.course_id
        WHERE p.user_id=? AND p.progress=100
    """, (session['user_id'],)).fetchall()

    conn.close()

    return render_template("transcript.html", courses=data)
        
@app.route('/verify/<cert_id>')
def verify_certificate(cert_id):

    conn = get_connection()

    cert = conn.execute("""
        SELECT * FROM certificates WHERE certificate_id=?
    """, (cert_id,)).fetchone()

    if not cert:
        conn.close()
        return "Invalid Certificate"

    user = conn.execute("""
        SELECT * FROM users WHERE id=?
    """, (cert['user_id'],)).fetchone()

    course = conn.execute("""
        SELECT * FROM courses WHERE id=?
    """, (cert['course_id'],)).fetchone()

    conn.close()

    return f"""
    <h2>Certificate Verified ✅</h2>
    <p><b>Name:</b> {user['username']}</p>
    <p><b>Course:</b> {course['title']}</p>
    <p><b>Date:</b> {cert['date_issued']}</p>
    """
 
@app.route('/certificate/pdf/<int:course_id>')
def certificate_pdf(course_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_connection()
    user_id = session['user_id']

    # COURSE
    course = conn.execute("""
        SELECT * FROM courses WHERE id=?
    """, (course_id,)).fetchone()

    # USER
    user = conn.execute("""
        SELECT * FROM users WHERE id=?
    """, (user_id,)).fetchone()

    # CERTIFICATE
    cert = conn.execute("""
        SELECT * FROM certificates
        WHERE user_id=? AND course_id=?
    """, (user_id, course_id)).fetchone()

    if not cert:
        conn.close()
        return "Certificate not found"

    # =========================
    # SERIAL NUMBER FIX
    # =========================
    serial_number = cert['serial_number'] if 'serial_number' in cert.keys() else None

    if not serial_number:

        last_serial = conn.execute("""
            SELECT MAX(id) as max_id FROM certificates
        """).fetchone()

        next_serial = (last_serial['max_id'] or 0) + 1
        serial_code = f"ELOC-2026-{str(next_serial).zfill(6)}"

        conn.execute("""
            UPDATE certificates
            SET serial_number=?
            WHERE id=?
        """, (serial_code, cert['id']))

        conn.commit()

        # reload cert
        cert = conn.execute("""
            SELECT * FROM certificates
            WHERE user_id=? AND course_id=?
        """, (user_id, course_id)).fetchone()

    conn.close()

# =========================
    # PDF GENERATION (FINAL SAFE + GOLD FRAME)
    # =========================
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    import os

    os.makedirs("static/certificates", exist_ok=True)

    file_path = f"static/certificates/{cert['certificate_id']}.pdf"

    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=60,
        bottomMargin=60
    )

    styles = getSampleStyleSheet()

    # =========================
    # STYLES
    # =========================
    center = ParagraphStyle(
        "center",
        parent=styles["Normal"],
        alignment=1,
        fontName="Helvetica",
        fontSize=13,
        spaceAfter=14
    )

    title = ParagraphStyle(
        "title",
        parent=styles["Title"],
        alignment=1,
        fontName="Times-Bold",
        fontSize=28,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=18
    )

    name_style = ParagraphStyle(
        "name",
        parent=styles["Normal"],
        alignment=1,
        fontName="Times-Bold",
        fontSize=22,
        spaceAfter=14
    )

    course_style = ParagraphStyle(
        "course",
        parent=styles["Normal"],
        alignment=1,
        fontName="Times-Italic",
        fontSize=18,
        textColor=colors.HexColor("#1f3a8a"),
        spaceAfter=14
    )

    small = ParagraphStyle(
        "small",
        parent=styles["Normal"],
        alignment=1,
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=10
    )

    content = []

    # =========================
    # LOGO (CENTERED)
    # =========================
    logo_path = "static/images/logo.png"
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=0.7*inch, height=0.7*inch)
        logo.hAlign = "CENTER"
        content.append(logo)

    content.append(Spacer(1, 15))

    # BRAND
    content.append(Paragraph("E-Learning One Creativity", center))

    # TITLE
    content.append(Paragraph("CERTIFICATE OF COMPLETION", title))

    content.append(Spacer(1, 10))

    # TEXT FLOW
    content.append(Paragraph("This is proudly awarded to", center))
    content.append(Paragraph(f"<b>{user['username']}</b>", name_style))
    content.append(Paragraph("for successfully completing", center))
    content.append(Paragraph(f"<b>{course['title']}</b>", course_style))

    content.append(Spacer(1, 20))

    # DETAILS
    content.append(Paragraph(f"Certificate ID: {cert['certificate_id']}", small))
    content.append(Paragraph(f"Serial Number: {cert['serial_number']}", small))
    content.append(Paragraph(f"Issued Date: {cert['date_issued']}", small))

    verify_url = request.host_url + "verify/" + cert['certificate_id']
    content.append(Paragraph(f"Verify: {verify_url}", small))

    content.append(Spacer(1, 20))

    # QR CODE
    qr_path = f"static/qrcodes/{cert['certificate_id']}.png"
    if os.path.exists(qr_path):
        qr = Image(qr_path, width=1.1*inch, height=1.1*inch)
        qr.hAlign = "CENTER"
        content.append(qr)

    content.append(Spacer(1, 20))

    # SIGNATURE
    signature_path = "static/images/signature.png"
    if os.path.exists(signature_path):
        sign = Image(signature_path, width=2*inch, height=0.8*inch)
        sign.hAlign = "CENTER"
        content.append(sign)

    content.append(Paragraph("Authorized Signature", small))

    content.append(Spacer(1, 15))

    # STAMP
    stamp_path = "static/images/stamp.png"
    if os.path.exists(stamp_path):
        stamp = Image(stamp_path, width=1.1*inch, height=1.1*inch)
        stamp.hAlign = "CENTER"
        content.append(stamp)

    content.append(Paragraph("Official Seal", small))

    # =========================
    # GOLD FRAME (SAFE - NO LAYOUT ERROR)
    # =========================
    def draw_border(canvas, doc):
        canvas.saveState()

        # Outer gold border
        canvas.setStrokeColor(colors.HexColor("#d4af37"))
        canvas.setLineWidth(3)
        canvas.rect(30, 30, A4[0]-60, A4[1]-60)

        # Inner soft gold border (shaded effect)
        canvas.setStrokeColor(colors.HexColor("#f5e6b1"))
        canvas.setLineWidth(1)
        canvas.rect(40, 40, A4[0]-80, A4[1]-80)

        canvas.restoreState()

    doc.build(content, onFirstPage=draw_border, onLaterPages=draw_border)

    conn.close()

    return send_file(file_path, as_attachment=True)

@app.route('/update-progress/<int:course_id>')
def update_progress(course_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_connection()

    # Check if progress already exists
    existing = conn.execute("""
        SELECT * FROM progress
        WHERE user_id=? AND course_id=?
    """, (session['user_id'], course_id)).fetchone()

    if existing:
        conn.execute("""
            UPDATE progress
            SET progress=100
            WHERE user_id=? AND course_id=?
        """, (session['user_id'], course_id))
    else:
        conn.execute("""
            INSERT INTO progress (user_id, course_id, progress)
            VALUES (?, ?, 100)
        """, (session['user_id'], course_id))

    conn.commit()
    conn.close()

    return redirect(url_for('course', course_id=course_id))
@app.route('/lesson/complete/<int:lesson_id>', methods=['POST'])
def complete_lesson(lesson_id):

    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_connection()

    # mark lesson complete
    conn.execute("""
        INSERT OR REPLACE INTO lesson_progress (user_id, lesson_id, completed)
        VALUES (?, ?, 1)
    """, (user_id, lesson_id))

    conn.commit()
    conn.close()

    return redirect(request.referrer)
 
@app.route('/profile', methods=['GET', 'POST'])
def profile():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_connection()

    # ✅ GET USER
    user = conn.execute("""
        SELECT * FROM users WHERE id=?
    """, (session['user_id'],)).fetchone()

    if request.method == 'POST':

        username = request.form['username']
        email = request.form['email']

        # keep existing image if no new one
        profile_pic = user['profile_pic'] if user['profile_pic'] else 'default.png'

        file = request.files.get('profile_pic')

        if file and file.filename != "":
            filename = secure_filename(file.filename)

            # create unique filename
            unique_filename = f"{session['user_id']}_{filename}"

            file_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
            file.save(file_path)

            profile_pic = unique_filename

        # ✅ UPDATE USER
        conn.execute("""
            UPDATE users
            SET username=?, email=?, profile_pic=?
            WHERE id=?
        """, (username, email, profile_pic, session['user_id']))

        conn.commit()

        # ✅ UPDATE SESSION (VERY IMPORTANT)
        session['username'] = username
        session['email'] = email
        session['profile_pic'] = profile_pic

        conn.close()

        return redirect(url_for('profile'))

    conn.close()

    return render_template("profile.html", user=user)
         
# =========================
# LOGOUT
# =========================
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!")
    return redirect(url_for('home'))

# =========================
# ADMIN - USER MANAGEMENT
# =========================

@app.route('/admin/users')
def admin_users():

    if session.get('email') != ADMIN_EMAIL:
        return redirect('/login')

    try:
        conn = get_connection()

        users = conn.execute("""
            SELECT id, username, email,
                   COALESCE(profile_pic, 'default.png') as profile_pic,
                   COALESCE(status, 'active') as status
            FROM users
            ORDER BY id DESC
        """).fetchall()

        conn.close()

        return render_template('admin_users.html', users=users)

    except Exception as e:
        print("ADMIN USERS ERROR:", e)
        return f"Error loading users: {e}"
    
@app.route('/admin/user/toggle/<int:user_id>')
def toggle_user(user_id):

    if session.get('email') != ADMIN_EMAIL:
        return redirect('/login')

    conn = get_connection()

    user = conn.execute("""
        SELECT COALESCE(status, 'active') as status
        FROM users
        WHERE id=?
    """, (user_id,)).fetchone()

    if not user:
        conn.close()
        return "User not found"

    current_status = user['status']
    new_status = 'disabled' if current_status == 'active' else 'active'

    conn.execute("""
        UPDATE users
        SET status=?
        WHERE id=?
    """, (new_status, user_id))

    conn.commit()
    conn.close()

    return redirect('/admin/users')


@app.route('/admin/user/delete/<int:user_id>')
def delete_user(user_id):

    if session.get('email') != ADMIN_EMAIL:
        return redirect('/login')

    conn = get_connection()

    conn.execute("""
        DELETE FROM users WHERE id=?
    """, (user_id,))

    conn.commit()
    conn.close()

    return redirect('/admin/users')
    
# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)
