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
import re
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "replace_with_strong_secret"

EMAIL_ADDRESS = "elearningonecreativity@gmail.com"
EMAIL_PASSWORD = "bzbgfuhsuldinffr"

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
        password TEXT,
        reset_token TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        kit_level TEXT,
        amount INTEGER,
        tx_ref TEXT UNIQUE,
        purchased_at TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS user_activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        activity TEXT,
        timestamp TEXT
    )""")

    conn.commit()
    conn.close()

init_db()

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
    except Exception as e:
        print(e)

# ----------------- ROUTES -----------------
@app.route('/')
def home():
    return render_template('index.html')

# ----------------- PROFILE -----------------
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('eloc.db')
    c = conn.cursor()

    # Activities
    c.execute("SELECT activity, timestamp FROM user_activities WHERE user_id=?", (session['user_id'],))
    raw_activities = c.fetchall()

    activities = []
    for activity, ts in raw_activities:
        if ts:
            formatted_time = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").strftime("%b %d, %Y %H:%M")
        else:
            formatted_time = "Unknown time"
        activities.append((activity, formatted_time))

    # Purchases
    c.execute("SELECT kit_level, purchased_at FROM purchases WHERE user_id=?", (session['user_id'],))
    purchases_raw = c.fetchall()

    downloads = []

    # Always include beginner
    downloads.append({
        "kit": "beginner",
        "expiry": "No expiry",
        "expired": False
    })

    for row in purchases_raw:
        kit_level = row[0]
        purchased_at = row[1]

        if purchased_at:
            purchase_date = datetime.strptime(purchased_at, "%Y-%m-%d %H:%M:%S")
        else:
            purchase_date = datetime.now()

        expiry_date = purchase_date + timedelta(days=7)

        downloads.append({
            "kit": kit_level,
            "expiry": expiry_date.strftime("%b %d, %Y"),
            "expired": datetime.now() > expiry_date
        })

    conn.close()

    return render_template(
        "profile.html",
        name=session['user_name'],
        activities=activities,
        downloads=downloads,
        profile_pic=session.get('profile_pic')
    )

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
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # ✅ FIXED INSERT (added purchased_at)
            c.execute("""
                INSERT INTO purchases (user_id, kit_level, amount, tx_ref, purchased_at)
                VALUES (?, ?, ?, ?, ?)
            """, (session['user_id'], level, response["data"]["amount"], tx_ref, now))

            conn.commit()

            log_activity(session['user_id'], f"Purchased {level} kit")

        except Exception as e:
            print(e)

        conn.close()

        return jsonify({"status": "success"})

    return jsonify({"status": "failed"})
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
