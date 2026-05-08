import hashlib
import os
import streamlit as st
from utils.db import execute_query

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with a random salt."""
    salt = os.urandom(32).hex()
    pw_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{pw_hash}"

def verify_password(password: str, stored: str) -> bool:
    """Verify password against stored hash."""
    try:
        salt, pw_hash = stored.split(":", 1)
        check = hashlib.sha256((salt + password).encode()).hexdigest()
        return check == pw_hash
    except Exception:
        return False

def register_user(name: str, email: str, password: str):
    existing = execute_query(
        "SELECT id FROM users WHERE email = ?", (email,), fetch=True
    )
    if existing:
        return False, "An account with this email already exists."
    
    hashed = hash_password(password)
    execute_query(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        (name, email, hashed)
    )
    return True, "Account created successfully."

def login_user(email: str, password: str):
    user = execute_query(
        "SELECT * FROM users WHERE email = ?", (email,), fetch=True
    )
    if not user:
        return None
    if verify_password(password, user["password_hash"]):
        return user
    return None

def logout_user():
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.mood = None
    st.session_state.mood_checked = False
    st.session_state.page = "dashboard"

def get_current_user():
    return st.session_state.get("user")

def update_user_settings(user_id: int, **kwargs):
    if not kwargs:
        return
    sets = ", ".join([f"{k} = ?" for k in kwargs])
    vals = list(kwargs.values()) + [user_id]
    execute_query(f"UPDATE users SET {sets} WHERE id = ?", vals)

def delete_account(user_id: int):
    execute_query("DELETE FROM pomodoro_sessions WHERE user_id = ?", (user_id,))
    execute_query("DELETE FROM topics WHERE user_id = ?", (user_id,))
    execute_query("DELETE FROM deadlines WHERE user_id = ?", (user_id,))
    execute_query("DELETE FROM study_slots WHERE user_id = ?", (user_id,))
    execute_query("DELETE FROM users WHERE id = ?", (user_id,))
