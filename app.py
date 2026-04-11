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

# ----------------- ADD COLUMNS SAFELY -----------------
conn = sqlite3.connect('eloc.db')
c = conn.cursor()

try:
    c.execute("ALTER TABLE purchases ADD COLUMN purchased_at TEXT")
except:
    pass

try:
    c.execute("ALTER TABLE users ADD COLUMN reset_token TEXT")
except:
    pass

try:
    c.execute("ALTER TABLE user_activities ADD COLUMN timestamp TEXT")
except:
    pass

conn.commit()
conn.close()

# ----------------- HELPERS -----------------
def log_activity(user_id, text):
    conn = sqlite3.connect('eloc.db')
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute(
        "INSERT INTO user_activities (user_id, activity, timestamp) VALUES (?, ?, ?)",
        (user_id, text, now)
    )

    conn.commit()
    conn.close()

def has_purchased(user_id, level):
    conn = sqlite3.connect('eloc.db')
    c = conn.cursor()
    c.execute("SELECT * FROM purchases WHERE user_id=? AND kit_level=?", (user_id, level))
    result = c.fetchone()
    conn.close()
    return result is not None

# ----------------- HOME -----------------
@app.route('/')
def home():
    return render_template('index.html')

# ----------------- KIT -----------------
@app.route('/kit/<level>')
def kit(level):
    kits = {
        "beginner": {"title":"Beginner Kit","price":0,"items":["HTML Ebook","Videos","Project"]},
        "intermediate": {"title":"Intermediate Kit","price":30,"items":["Responsive Design","Templates"]},
        "professional": {"title":"Professional Kit","price":50,"items":["Client Projects","Freelancing Guide"]}
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
        purchased=purchased
    )

# ----------------- VERIFY PAYMENT (FIXED) -----------------
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

    if response.get("status") == "success":
        conn = sqlite3.connect('eloc.db')
        c = conn.cursor()

        try:
            # prevent duplicates
            c.execute("SELECT id FROM purchases WHERE tx_ref=?", (tx_ref,))
            exists = c.fetchone()

            if not exists:
                c.execute(
                    "INSERT INTO purchases (user_id, kit_level, amount, tx_ref, purchased_at) VALUES (?,?,?,?,?)",
                    (
                        session.get('user_id', 0),
                        level,
                        response["data"]["amount"],
                        tx_ref,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    )
                )
                conn.commit()

            log_activity(session['user_id'], f"Purchased {level} kit")

        except Exception as e:
            print("DB error:", e)

        conn.close()
        return jsonify({"status": "success"})

    return jsonify({"status": "failed"})

# ----------------- CALLBACK (FIXED SAFETY) -----------------
@app.route('/payment-callback')
def payment_callback():
    tx_id = request.args.get('transaction_id')
    tx_ref = request.args.get('tx_ref')
    level = request.args.get('level')

    if not tx_id:
        return redirect(url_for('home'))

    url = f"https://api.flutterwave.com/v3/transactions/{tx_id}/verify"
    headers = {"Authorization": f"Bearer {FLW_SECRET_KEY}"}

    res = requests.get(url, headers=headers)
    response = res.json()

    if response.get("status") == "success":
        try:
            conn = sqlite3.connect('eloc.db')
            c = conn.cursor()

            c.execute("SELECT id FROM purchases WHERE tx_ref=?", (tx_ref,))
            exists = c.fetchone()

            if not exists:
                c.execute(
                    "INSERT INTO purchases (user_id, kit_level, amount, tx_ref, purchased_at) VALUES (?,?,?,?,?)",
                    (
                        session.get('user_id', 0),
                        level,
                        response["data"]["amount"],
                        tx_ref,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    )
                )
                conn.commit()

            conn.close()

        except Exception as e:
            print("Callback error:", e)

        return redirect(url_for('success'))

    return redirect(url_for('home'))

# ----------------- SUCCESS -----------------
@app.route('/success')
def success():
    return render_template("success.html")

# ----------------- DOWNLOAD -----------------
@app.route('/download/<level>/<filename>')
def download(level, filename):
    if level != "beginner":
        if 'user_id' not in session or not has_purchased(session['user_id'], level):
            return "Access denied", 403

    log_activity(session['user_id'], f"Downloaded {level} kit")

    return send_from_directory(f'kits/{level}', filename, as_attachment=True)

# ----------------- RUN -----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
