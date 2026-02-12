import os
import time
import sqlite3
import requests
import threading
from io import BytesIO
from datetime import datetime
from flask import Flask, request, send_file, render_template_string, jsonify
from flask_cors import CORS
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)
CORS(app)

# ===== RENDER CLOUD CONFIG =====
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
UNSPLASH_KEY = os.getenv("UNSPLASH_KEY")
MODEL_ID = "google/gemini-2.0-flash-001"

# IMPORTANT: Point this to Render's persistent disk path
# On Render Dashboard, you will mount a disk to /var/data
DB_PATH = "/var/data/sass_master.db" if os.path.exists("/var/data") else "local_data.db"
FREE_LIMIT = 10

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True) if "/" in DB_PATH else None
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS users (ip TEXT PRIMARY KEY, count INTEGER)')
        conn.execute('CREATE TABLE IF NOT EXISTS chat_history (id INTEGER PRIMARY KEY, ip TEXT, role TEXT, content TEXT, ts DATETIME)')
        conn.execute('CREATE TABLE IF NOT EXISTS scout_logs (id INTEGER PRIMARY KEY, report TEXT, ts DATETIME)')
init_db()

# ===== THE AUTONOMOUS SCOUT =====
def autonomous_scout():
    print("Agent: Scout is online and searching...")
    while True:
        try:
            prompt = "Act as a 2026 market analyst. Find one trending AI or tech business niche. Briefly explain: Niche, Why, and Revenue Model."
            res = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
                json={"model": MODEL_ID, "messages": [{"role": "user", "content": prompt}]}
            )
            report = res.json()['choices'][0]['message']['content']
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute('INSERT INTO scout_logs (report, ts) VALUES (?, ?)', (report, datetime.now()))
            print(f"Scout Success: {datetime.now()}")
        except Exception as e:
            print(f"Scout Error: {e}")
        time.sleep(300) # Every 5 minutes

# Start agent in background
threading.Thread(target=autonomous_scout, daemon=True).start()

# ... [Keep your existing Routes: /, /chat, /generate, /scout_data] ...

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
