"""
lab2/vuln_app/app.py — intentionally vulnerable local training app for Lab 2.

SQL injection via string-built queries (CWE-89). This file is deliberately broken for
teaching purposes. Do not deploy it anywhere but localhost inside the lab.

Run:   python app.py      (binds to 127.0.0.1:5000 only)
"""
import sqlite3
from pathlib import Path

from flask import Flask, request, jsonify

app = Flask(__name__)
DB_PATH = Path(__file__).parent / "lab.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS users")
    conn.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.executemany(
        "INSERT INTO users (username, email, is_admin) VALUES (?, ?, ?)",
        [
            ("alice", "alice@example.local", 0),
            ("bob", "bob@example.local", 0),
            ("admin", "admin@example.local", 1),
        ],
    )
    conn.commit()
    conn.close()


@app.route("/")
def index():
    return (
        "Lab 2 vulnerable app is running.\n"
        "Try: GET /user?username=alice\n"
    )


@app.route("/user")
def get_user():
    username = request.args.get("username", "")

    # --- VULNERABLE: query built by string formatting, not parameterized. ---
    # A student (or the AI, as a hypothesis to verify) can observe that input
    # is concatenated directly into SQL, enabling classic SQL injection.
    query = "SELECT id, username, email, is_admin FROM users WHERE username = '%s'" % username

    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute(query)
        rows = cur.fetchall()
    except sqlite3.Error as e:
        # Verbose error reflected back — also a finding worth noting (info leak),
        # separate from the injection itself.
        return jsonify({"error": str(e), "query": query}), 500
    finally:
        conn.close()

    return jsonify([
        {"id": r[0], "username": r[1], "email": r[2], "is_admin": bool(r[3])}
        for r in rows
    ])


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)
