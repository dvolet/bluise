from flask import Flask, render_template, send_from_directory, request, redirect, url_for, session, jsonify, flash
import secrets
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import os
from werkzeug.utils import secure_filename
import re  # For password validation
from datetime import datetime

def log_activity(user_id, text):
    conn = sqlite3.connect('eloc.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute(
        "INSERT INTO user_activities (user_id, activity, timestamp) VALUES (?, ?, ?)",
        (user_id, text, now)
    )

    conn.commit()
    conn.close()
EMAIL_ADDRESS = "elearningonecreativity@gmail.com"
EMAIL_PASSWORD = "bzbgfuhsuldinffr"
app = Flask(__name__)
app.secret_key = "replace_with_strong_secret"

FLW_SECRET_KEY = "FLWSECK-d6aed55b227f0236ff4f009e02ee6fb9-19d4e3fc120vt-X"

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ----------------- INIT DB -----------------
def init_db():
    conn = sqlite3.connect('eloc.db')
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        kit_level TEXT,
        amount INTEGER,
        tx_ref TEXT UNIQUE
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS user_activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        activity TEXT
    )""")

    conn.commit()
    conn.close()

init_db()

conn = sqlite3.connect('eloc.db')
c = conn.cursor()
try:
    c.execute("ALTER TABLE purchases ADD COLUMN purchased_at TEXT")
    conn.commit()
    print("purchased_at column added")
except sqlite3.OperationalError:
    # Column already exists
    print("purchased_at column already exists")
conn.close()
# ----------------- ADD RESET TOKEN COLUMN -----------------
# Only needed once, safely adds column if missing
conn = sqlite3.connect('eloc.db')
c = conn.cursor()
try:
    c.execute("ALTER TABLE users ADD COLUMN reset_token TEXT")
    conn.commit()
except sqlite3.OperationalError:
    # Column already exists, skip
    pass
conn.close()

# Add timestamp to user_activities if missing
conn = sqlite3.connect('eloc.db')
c = conn.cursor()
try:
    c.execute("ALTER TABLE user_activities ADD COLUMN timestamp TEXT")
    conn.commit()
except sqlite3.OperationalError:
    # Column already exists
    pass
conn.close()
# ----------------- HELPERS -----------------
def log_activity(user_id, text):
    conn = sqlite3.connect('eloc.db')
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO user_activities (user_id, activity, timestamp) VALUES (?, ?, ?)",
              (user_id, text, now))
    conn.commit()
    conn.close()

def has_purchased(user_id, level):
    conn = sqlite3.connect('eloc.db')
    c = conn.cursor()
    c.execute("SELECT * FROM purchases WHERE user_id=? AND kit_level=?", (user_id, level))
    result = c.fetchone()
    conn.close()
    return result is not None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Error sending email: {e}")

# ----------------- PASSWORD VALIDATION -----------------
def validate_password(password):
    """
    Returns (True, "") if valid, or (False, "reason") if invalid
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character."
    return True, ""
        
# ----------------- ROUTES -----------------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/kit/<level>')
def kit(level):
    kits = {
        "beginner": {"title":"Beginner Kit","price":0,"items":["HTML Ebook","Videos","Project"]},
        "intermediate": {"title":"Intermediate Kit","price":100,"items":["Responsive Design","Templates"]},
        "professional": {"title":"Professional Kit","price":300,"items":["Client Projects","Freelancing Guide"]}
    }

    kit = kits.get(level)
    if not kit:
        return "Not found", 404

    purchased = False
    if 'user_id' in session:
        purchased = has_purchased(session['user_id'], level)
        log_activity(session['user_id'], f"Viewed {kit['title']}")

    return render_template("kit.html",
                           key=level,
                           title=kit["title"],
                           items=kit["items"],
                           price=kit["price"],
                           purchased=purchased)

# ----------------- DOWNLOAD -----------------
@app.route('/download/<level>/<filename>')
def download(level, filename):
    if level != "beginner":
        if 'user_id' not in session or not has_purchased(session['user_id'], level):
            return "Access denied", 403

    # ✅ ADD THIS LINE HERE
    if 'user_id' in session:
        log_activity(session['user_id'], f"Downloaded {level} kit")

    return send_from_directory(f'kits/{level}', filename, as_attachment=True)

# ----------------- SIGNUP -----------------
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        try:
            conn = sqlite3.connect('eloc.db')
            c = conn.cursor()
            c.execute("INSERT INTO users (name,email,password) VALUES (?,?,?)",
                      (name,email,password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except:
            return render_template('signup.html', error="Email exists")

    return render_template('signup.html')

# ----------------- LOGIN -----------------
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('eloc.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=?", (email,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['user_name'] = user[1]

            # ✅ ADD THIS LINE
            log_activity(user[0], "Logged in")

            return redirect(url_for('profile'))

        return render_template('login.html', error="Invalid login")

    return render_template('login.html')
# ----------------- PROFILE -----------------
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    import sqlite3
    from datetime import datetime, timedelta

    conn = sqlite3.connect('eloc.db')
    c = conn.cursor()

    # Fetch user activities with timestamp
    c.execute("SELECT activity, timestamp FROM user_activities WHERE user_id=?", (session['user_id'],))
    raw_activities = c.fetchall()  # Each item is (activity_text, timestamp)
    activities = []
    for activity, ts in raw_activities:
        if ts:
            formatted_time = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").strftime("%b %d, %Y %H:%M")
        else:
            formatted_time = "Unknown time"
        activities.append((activity, formatted_time))

    # Fetch purchased kits with timestamp
    c.execute("SELECT kit_level, purchased_at FROM purchases WHERE user_id=?", (session['user_id'],))
    purchases_raw = c.fetchall()  # Each item is (kit_level, purchased_at)

    downloads = []

    # Always include beginner kit (no expiry)
    downloads.append({
        "kit": "beginner",
        "expiry": "No expiry",
        "expired": False
    })

    # Add paid kits with expiry
    for kit_level, purchased_at in purchases_raw:
        if purchased_at:
            purchase_date = datetime.strptime(purchased_at, "%Y-%m-%d %H:%M:%S")
        else:
            purchase_date = datetime.now()  # fallback
        expiry_date = purchase_date + timedelta(days=7)
        is_expired = datetime.now() > expiry_date

        downloads.append({
            "kit": kit_level,
            "expiry": expiry_date.strftime("%b %d, %Y"),
            "expired": is_expired
        })

    conn.close()

    return render_template(
        "profile.html",
        name=session['user_name'],
        activities=activities,
        downloads=downloads,
        profile_pic=session.get('profile_pic')
    )

# ----------------- UPLOAD PROFILE -----------------
@app.route('/upload-profile', methods=['POST'])
def upload_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if 'profile_pic' not in request.files:
        return redirect(url_for('profile'))

    file = request.files['profile_pic']

    if file.filename == '':
        return redirect(url_for('profile'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        # Ensure folder exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        session['profile_pic'] = filename

    return redirect(url_for('profile'))
    
@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({"status": "failed", "message": "Not logged in"}), 401

    data = request.get_json()
    name = data.get('name')
    old_password = data.get('old_password')
    password = data.get('password')

    conn = sqlite3.connect('eloc.db')
    c = conn.cursor()
    success = False
    message = ""

    try:
        # ----------- PASSWORD CHANGE -----------
        if password:
            # 1️⃣ Get current hashed password from DB
            c.execute("SELECT password FROM users WHERE id=?", (session['user_id'],))
            current_hashed = c.fetchone()[0]

            # 2️⃣ Check if old password entered correctly
            if not check_password_hash(current_hashed, old_password):
                return jsonify({"status": "failed", "message": "Current password is incorrect"})

            # 3️⃣ Validate new password rules
            valid, msg = validate_password(password)
            if not valid:
                return jsonify({"status": "failed", "message": msg})

            # 4️⃣ Prevent using the same password
            if check_password_hash(current_hashed, password):
                return jsonify({"status": "failed", "message": "New password cannot be same as old password."})

            # 5️⃣ Hash and update the new password
            hashed_new = generate_password_hash(password)
            c.execute("UPDATE users SET password=? WHERE id=?", (hashed_new, session['user_id']))
            success = True

        # ----------- NAME CHANGE -----------
        if name:
            c.execute("UPDATE users SET name=? WHERE id=?", (name, session['user_id']))
            session['user_name'] = name
            success = True

        conn.commit()
    except Exception as e:
        print(e)
        message = "Something went wrong."
        success = False
    finally:
        conn.close()

    if success:
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "failed", "message": message})
        
# ----------------- PAYMENT -----------------
@app.route('/payment/<level>')
def payment(level):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    prices = {
        "intermediate": 100,
        "professional": 300
    }

    return render_template('payment.html',
                           level=level,
                           price=prices.get(level, 0))

# ----------------- VERIFY PAYMENT -----------------
@app.route('/verify-payment', methods=['POST'])
def verify_payment():
    data = request.json
    tx_id = data.get("transaction_id")
    tx_ref = data.get("tx_ref")
    level = data.get("level")

    url = f"https://api.flutterwave.com/v3/transactions/{tx_id}/verify"
    headers = {"Authorization": f"Bearer {FLW_SECRET_KEY}"}

    res = requests.get(url, headers=headers)
    response = res.json()

    if response["status"] == "success":
        conn = sqlite3.connect('eloc.db')
        c = conn.cursor()

        try:
            c.execute("INSERT INTO purchases (user_id, kit_level, amount, tx_ref) VALUES (?,?,?,?)",
                      (session['user_id'], level, response["data"]["amount"], tx_ref))
            conn.commit()

            # ✅ ADD THIS (SAFE – WILL NOT BREAK ANYTHING)
            if 'user_id' in session:
                log_activity(session['user_id'], f"Purchased {level} kit")

        except:
            pass

        conn.close()

        return jsonify({"status": "success"})

    return jsonify({"status": "failed"})

# ----------------- SUCCESS -----------------
@app.route('/success')
def success():
    return render_template('success.html')

# ----------------- LOGOUT -----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()

        if not email:
            flash("Please enter your email")
            return redirect(url_for('forgot_password'))

        # Check if user exists
        conn = sqlite3.connect('eloc.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email=?", (email,))
        user = cursor.fetchone()

        if user:
            token = secrets.token_urlsafe(16)
            cursor.execute("UPDATE users SET reset_token=? WHERE id=?", (token, user[0]))
            conn.commit()

            reset_link = url_for('reset_password', token=token, _external=True)

            # ✅ MOVE EVERYTHING BELOW INSIDE HERE
            subject = "ELOC Password Reset"
            body = f"Hi,\n\nClick the link below to reset your password:\n{reset_link}\n\nIf you didn't request this, ignore this email."

            send_email(email, subject, body)

            flash(f"Password reset link sent to {email}. Check your inbox.", "success")
        else:
            flash("Email not found", "error")

        conn.close()
        return redirect(url_for('forgot_password'))

    return render_template('forgot.html')
    
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    conn = sqlite3.connect('eloc.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, password FROM users WHERE reset_token=?", (token,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        flash("Invalid or expired token.")
        return redirect(url_for('forgot_password'))

    user_id, current_hashed = user

    if request.method == 'POST':
        password = request.form.get('password', '').strip()

        # Validate password
        def validate_password(pwd):
            if len(pwd) < 8:
                return False, "Password must be at least 8 characters"
            if not re.search(r"[A-Z]", pwd):
                return False, "Password must contain an uppercase letter"
            if not re.search(r"[a-z]", pwd):
                return False, "Password must contain a lowercase letter"
            if not re.search(r"[0-9]", pwd):
                return False, "Password must contain a number"
            if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", pwd):
                return False, "Password must contain a special symbol"
            return True, ""

        valid, msg = validate_password(password)
        if not valid:
            flash(msg)
            return redirect(url_for('reset_password', token=token))

        # Check if password is same as old
        if check_password_hash(current_hashed, password):
            flash("New password cannot be the same as the old password.")
            return redirect(url_for('reset_password', token=token))

        # Update password
        hashed = generate_password_hash(password)
        cursor.execute("UPDATE users SET password=?, reset_token=NULL WHERE id=?", (hashed, user_id))
        conn.commit()
        conn.close()

        flash("Password updated successfully! You can now login.")
        return redirect(url_for('login'))

    conn.close()
    return render_template('reset.html')
    
# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
