# lib/analytics.py
import sqlite3
import time
import json
import threading

# Creates analytics.db in your project directory.
# It's a file-based DB (no server). Perfect for simple event counts/queries.
_conn = sqlite3.connect("analytics.db", check_same_thread=False)
_conn.execute("""
CREATE TABLE IF NOT EXISTS events(
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  props TEXT NOT NULL,
  ts INTEGER NOT NULL
)""")
_conn.commit()

_lock = threading.Lock()

def track(name: str, props: dict | None = None):
    """
    Record a simple event (name + props + timestamp).
    We'll use this to measure value, e.g., 'company_clicked', 'targets_exported'.
    """
    with _lock:
        _conn.execute(
            "INSERT INTO events(name, props, ts) VALUES(?,?,?)",
            (name, json.dumps(props or {}), int(time.time() * 1000))
        )
        _conn.commit()
