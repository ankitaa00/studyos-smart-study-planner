import sqlite3
import os
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "studyos.db"

def get_connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Users
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            pomodoro_focus INTEGER DEFAULT 25,
            pomodoro_short_break INTEGER DEFAULT 5,
            pomodoro_long_break INTEGER DEFAULT 15,
            notifications_enabled INTEGER DEFAULT 1
        )
    """)
    
    # Topics
    c.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            chapter TEXT,
            topic TEXT NOT NULL,
            difficulty_score REAL DEFAULT 5.0,
            difficulty_reason TEXT,
            difficulty_label TEXT DEFAULT 'Medium',
            priority_score REAL DEFAULT 5.0,
            studied INTEGER DEFAULT 0,
            hours_studied REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Deadlines
    c.execute("""
        CREATE TABLE IF NOT EXISTS deadlines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            deadline_date TEXT NOT NULL,
            type TEXT DEFAULT 'exam',
            coverage_hours REAL DEFAULT 10,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Pomodoro sessions
    c.execute("""
        CREATE TABLE IF NOT EXISTS pomodoro_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            topic TEXT,
            duration_minutes INTEGER,
            session_type TEXT DEFAULT 'focus',
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # Study schedule
    c.execute("""
        CREATE TABLE IF NOT EXISTS study_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            slot_date TEXT NOT NULL,
            start_time TEXT,
            duration_hours REAL DEFAULT 1,
            completed INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    conn.commit()
    conn.close()

def execute_query(query, params=(), fetch=False, fetchall=False):
    conn = get_connection()
    c = conn.cursor()
    c.execute(query, params)
    result = None
    if fetchall:
        result = [dict(row) for row in c.fetchall()]
    elif fetch:
        row = c.fetchone()
        result = dict(row) if row else None
    else:
        conn.commit()
        result = c.lastrowid
    conn.close()
    return result
