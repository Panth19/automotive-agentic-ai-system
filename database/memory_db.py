"""
SQLite Memory Database for conversation history
"""
import sqlite3
import json
from datetime import datetime

DB_PATH = "memory.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        user_message TEXT,
        intent TEXT,
        tools_called TEXT,
        response TEXT,
        safety_blocked INTEGER DEFAULT 0,
        safety_reason TEXT
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        vehicle_state TEXT
    )''')
    conn.commit()
    conn.close()

def create_session(session_id, vehicle_state):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO sessions (session_id, created_at, vehicle_state) VALUES (?, ?, ?)",
        (session_id, datetime.now().isoformat(), json.dumps(vehicle_state)))
    conn.commit()
    conn.close()

def save_conversation(session_id, user_message, intent, tools_called, response, safety_blocked, safety_reason):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO conversations 
        (session_id, timestamp, user_message, intent, tools_called, response, safety_blocked, safety_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
        (session_id, datetime.now().isoformat(), user_message, intent, 
         json.dumps(tools_called), response, 1 if safety_blocked else 0, safety_reason))
    conn.commit()
    conn.close()

def get_conversation_history(session_id, limit=20):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''SELECT user_message, intent, tools_called, response, safety_blocked, safety_reason, timestamp
        FROM conversations WHERE session_id = ? ORDER BY id DESC LIMIT ?''', (session_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [{"user_message": r[0], "intent": r[1], "tools_called": json.loads(r[2]) if r[2] else [],
             "response": r[3], "safety_blocked": bool(r[4]), "safety_reason": r[5], "timestamp": r[6]} 
            for r in reversed(rows)]

init_db()
