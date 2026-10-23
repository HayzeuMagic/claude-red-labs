"""
lab2/vuln_app/app_fixed.py — the proposed fix for app.py's SQL injection (CWE-89).

Same app, same routes, same test data. The only change: the query is parameterized
instead of string-built, so user input is always treated as data, never as SQL.

Run:   python app_fixed.py      (binds to 127.0.0.1:5001 only, so you can run both
                                   the vulnerable and fixed versions side by side)
"""
import sqlite3
from pathlib import Path

from flask import Flask, request, jsonify

app = Flask(__name__)
DB_PATH = Path(__file__).parent / "lab_fixed.db"


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
        "Lab 2 FIXED app is running.\n"
        "Try: GET /user?username=alice\n"
    )


@app.route("/user")
def get_user():
    username = request.args.get("username", "")

    # --- FIX: parameterized query. Input is bound as data, never concatenated
    # into the SQL text, so it cannot change the query's structure. ---
    query = "SELECT id, username, email, is_admin FROM users WHERE username = ?"

    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute(query, (username,))
        rows = cur.fetchall()
    except sqlite3.Error:
        # Generic error, no query text or exception detail reflected back
        # (fixes the secondary information-leak finding too).
        return jsonify({"error": "internal error"}), 500
    finally:
        conn.close()

    return jsonify([
        {"id": r[0], "username": r[1], "email": r[2], "is_admin": bool(r[3])}
        for r in rows
    ])


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5001, debug=True)
