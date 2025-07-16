import sqlite3
from datetime import datetime
from utils.config import DB_PATH

def get_connection(db_path=DB_PATH):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME NOT NULL
        )
    """)
    conn.commit()
    return conn

def save_message(conn, sender, message):
    c = conn.cursor()
    c.execute("INSERT INTO chats (sender, message, timestamp) VALUES (?, ?, ?)",
              (sender, message, datetime.utcnow()))
    conn.commit()

def get_history(conn, limit=100):
    c = conn.cursor()
    c.execute("SELECT sender, message, timestamp FROM chats ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()[::-1]
    return rows
