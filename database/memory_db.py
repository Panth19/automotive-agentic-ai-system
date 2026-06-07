"""
SQLite Memory Database for conversation history
"""
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = "memory.db"

def init_db():
    """Initialize the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            user_message TEXT,
            intent TEXT,
            tools_called TEXT,
            response TEXT,
            safety_blocked INTEGER DEFAULT 0,
            safety_reason TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            vehicle_state TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def create_session(session_id: str, vehicle_state: dict):
    """Create a new session"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT OR IGNORE INTO sessions (session_id, created_at, vehicle_state) VALUES (?, ?, ?)",
        (session_id, datetime.now().isoformat(), json.dumps(vehicle_state))
    )
    
    conn.commit()
    conn.close()

def save_conversation(session_id: str, user_message: str, intent: str = None, 
                      tools_called: List[str] = None, response: str = None,
                      safety_blocked: bool = False, safety_reason: str = None):
    """Save a conversation turn"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO conversations 
        (session_id, timestamp, user_message, intent, tools_called, response, safety_blocked, safety_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        session_id,
        datetime.now().isoformat(),
        user_message,
        intent,
        json.dumps(tools_called) if tools_called else None,
        response,
        1 if safety_blocked else 0,
        safety_reason
    ))
    
    conn.commit()
    conn.close()

def get_conversation_history(session_id: str, limit: int = 20) -> List[Dict]:
    """Get recent conversation history for a session"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT user_message, intent, tools_called, response, safety_blocked, safety_reason, timestamp
        FROM conversations 
        WHERE session_id = ?
        ORDER BY id DESC
        LIMIT ?
    ''', (session_id, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for row in reversed(rows):
        history.append({
            "user_message": row[0],
            "intent": row[1],
            "tools_called": json.loads(row[2]) if row[2] else [],
            "response": row[3],
            "safety_blocked": bool(row[4]),
            "safety_reason": row[5],
            "timestamp": row[6]
        })
    
    return history

# Initialize on import
init_db()
