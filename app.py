import streamlit as st
import json
import os
from pathlib import Path
from utils.auth import login_user, register_user, logout_user, get_current_user
from utils.db import init_db

# Page config
st.set_page_config(
    page_title="StudyOS — Smart Study Planner",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize DB
init_db()

# Load CSS
def load_css():
    css_path = Path(__file__).parent / "assets" / "styles.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Session state defaults
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "dashboard"
if "mood" not in st.session_state:
    st.session_state.mood = None
if "mood_checked" not in st.session_state:
    st.session_state.mood_checked = False

def navigate(page):
    st.session_state.page = page
    st.rerun()

def show_auth_page():
    st.markdown("""
    <div style='text-align:center; padding: 3rem 0 1rem 0;'>
        <div style='font-size:3.5rem; margin-bottom:0.5rem;'>🎓</div>
        <h1 style='font-size:2.8rem; font-weight:900; letter-spacing:-1px; margin:0;
                   background: linear-gradient(135deg, #6366f1, #a855f7, #ec4899);
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            StudyOS
        </h1>
        <p style='color:#94a3b8; font-size:1.1rem; margin-top:0.5rem;'>
            Your AI-powered intelligent study companion
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔑 Login", "✨ Register"])
        
        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="you@example.com")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign In →", use_container_width=True)
                if submitted:
                    user = login_user(email, password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.session_state.mood_checked = False
                        st.success("Welcome back! 🎉")
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Please try again.")
        
        with tab2:
            with st.form("register_form"):
                name = st.text_input("Full Name", placeholder="Alex Johnson")
                email = st.text_input("Email", placeholder="you@example.com", key="reg_email")
                password = st.text_input("Password", type="password", key="reg_pass")
                confirm = st.text_input("Confirm Password", type="password")
                submitted = st.form_submit_button("Create Account →", use_container_width=True)
                if submitted:
                    if password != confirm:
                        st.error("Passwords don't match!")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters.")
                    else:
                        success, msg = register_user(name, email, password)
                        if success:
                            st.success("Account created! Please log in.")
                        else:
                            st.error(msg)

def show_sidebar():
    user = st.session_state.user
    
    with st.sidebar:
        st.markdown(f"""
        <div class='sidebar-header'>
            <div class='avatar'>{user['name'][0].upper()}</div>
            <div>
                <div class='user-name'>{user['name']}</div>
                <div class='user-email'>{user['email']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        pages = [
            ("🏠", "Dashboard", "dashboard"),
            ("📚", "Syllabus", "syllabus"),
            ("📅", "Schedule", "schedule"),
            ("⏱️", "Pomodoro", "pomodoro"),
            ("📈", "Performance", "performance"),
            ("⚙️", "Settings", "settings"),
        ]
        
        for icon, label, page_key in pages:
            is_active = st.session_state.page == page_key
            btn_style = "primary" if is_active else "secondary"
            if st.button(f"{icon} {label}", key=f"nav_{page_key}", 
                        use_container_width=True,
                        type=btn_style):
                navigate(page_key)
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            logout_user()
            st.rerun()

def show_mood_checkin():
    if st.session_state.mood_checked:
        return
    
    st.markdown("""
    <div class='mood-banner'>
        <h3>👋 How are you feeling today?</h3>
        <p>We'll adapt your study plan to match your energy level</p>
    </div>
    """, unsafe_allow_html=True)
    
    moods = [
        ("⚡", "Energized", "energized", "Long sessions, challenging topics first"),
        ("🎯", "Focused", "focused", "Balanced sessions, normal order"),
        ("😐", "Neutral", "neutral", "Standard plan"),
        ("😴", "Tired", "tired", "Short sessions, lighter topics"),
        ("😰", "Stressed", "stressed", "Easy topics first, more breaks"),
        ("😟", "Anxious", "anxious", "Frequent breaks, gentle pacing"),
    ]
    
    cols = st.columns(6)
    for i, (emoji, label, key, desc) in enumerate(moods):
        with cols[i]:
            if st.button(f"{emoji}\n{label}", key=f"mood_{key}", use_container_width=True):
                st.session_state.mood = {"key": key, "label": label, "emoji": emoji, "desc": desc}
                st.session_state.mood_checked = True
                st.rerun()

def main():
    if not st.session_state.authenticated:
        show_auth_page()
        return
    
    show_sidebar()
    
    # Mood check-in
    if not st.session_state.mood_checked:
        show_mood_checkin()
        return
    
    # Route to pages
    page = st.session_state.page
    
    if page == "dashboard":
        from pages import dashboard
        dashboard.show()
    elif page == "syllabus":
        from pages import syllabus
        syllabus.show()
    elif page == "schedule":
        from pages import schedule
        schedule.show()
    elif page == "pomodoro":
        from pages import pomodoro
        pomodoro.show()
    elif page == "performance":
        from pages import performance
        performance.show()
    elif page == "settings":
        from pages import settings
        settings.show()

if __name__ == "__main__":
    main()
