import streamlit as st
import time
import datetime
from utils.db import execute_query

def show():
    user = st.session_state.user
    mood = st.session_state.mood
    
    st.markdown("""
    <div class='page-header'>
        <div>
            <h1>⏱️ Pomodoro Timer</h1>
            <p class='subtitle'>Deep focus sessions with smart breaks</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Mood-adapted defaults
    mood_session_lengths = {
        "energized": 45, "focused": 30, "neutral": 25,
        "tired": 15, "stressed": 20, "anxious": 15
    }
    mood_break_lengths = {
        "energized": 5, "focused": 5, "neutral": 5,
        "tired": 10, "stressed": 8, "anxious": 10
    }
    
    default_focus = mood_session_lengths.get(mood["key"] if mood else "neutral", 25)
    default_break = mood_break_lengths.get(mood["key"] if mood else "neutral", 5)
    
    # Session state
    if "pomo_running" not in st.session_state:
        st.session_state.pomo_running = False
    if "pomo_phase" not in st.session_state:
        st.session_state.pomo_phase = "focus"  # focus / short_break / long_break
    if "pomo_count" not in st.session_state:
        st.session_state.pomo_count = 0
    if "pomo_end_time" not in st.session_state:
        st.session_state.pomo_end_time = None
    if "pomo_topic" not in st.session_state:
        st.session_state.pomo_topic = ""
    if "pomo_focus_mins" not in st.session_state:
        st.session_state.pomo_focus_mins = default_focus
    if "pomo_short_break" not in st.session_state:
        st.session_state.pomo_short_break = default_break
    if "pomo_long_break" not in st.session_state:
        st.session_state.pomo_long_break = 15
    
    # Get topics for selection
    topics = execute_query(
        "SELECT * FROM topics WHERE user_id = ? AND studied = 0 ORDER BY priority_score DESC",
        (user['id'],), fetchall=True
    )
    topic_names = [t['topic'] for t in topics] if topics else []
    
    col_timer, col_history = st.columns([1.2, 1])
    
    with col_timer:
        st.markdown("#### 🎯 Current Session")
        
        # Topic selector
        if topic_names:
            topic_choice = st.selectbox(
                "Studying:",
                ["Select a topic..."] + topic_names,
                index=0 if not st.session_state.pomo_topic else 
                      (["Select a topic..."] + topic_names).index(st.session_state.pomo_topic) 
                      if st.session_state.pomo_topic in topic_names else 0
            )
            if topic_choice != "Select a topic...":
                st.session_state.pomo_topic = topic_choice
        else:
            custom_topic = st.text_input("What are you studying?", value=st.session_state.pomo_topic)
            st.session_state.pomo_topic = custom_topic
        
        # Timer display
        phase = st.session_state.pomo_phase
        phase_labels = {"focus": "🎯 Focus Time", "short_break": "☕ Short Break", "long_break": "🌿 Long Break"}
        phase_colors = {"focus": "#6366f1", "short_break": "#10b981", "long_break": "#14b8a6"}
        
        phase_durations = {
            "focus": st.session_state.pomo_focus_mins,
            "short_break": st.session_state.pomo_short_break,
            "long_break": st.session_state.pomo_long_break
        }
        
        total_seconds = phase_durations[phase] * 60
        
        # Calculate remaining time
        if st.session_state.pomo_running and st.session_state.pomo_end_time:
            remaining = max(0, (st.session_state.pomo_end_time - datetime.datetime.now()).total_seconds())
            if remaining <= 0:
                # Session complete
                st.session_state.pomo_running = False
                if phase == "focus":
                    # Log completed session
                    execute_query(
                        "INSERT INTO pomodoro_sessions (user_id, topic, duration_minutes, session_type) VALUES (?,?,?,?)",
                        (user['id'], st.session_state.pomo_topic, st.session_state.pomo_focus_mins, 'focus')
                    )
                    st.session_state.pomo_count += 1
                    # Transition to break
                    if st.session_state.pomo_count % 4 == 0:
                        st.session_state.pomo_phase = "long_break"
                    else:
                        st.session_state.pomo_phase = "short_break"
                else:
                    st.session_state.pomo_phase = "focus"
                st.session_state.pomo_end_time = None
                st.rerun()
        else:
            remaining = float(total_seconds)
        
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        pct = (remaining / total_seconds) if total_seconds > 0 else 0
        circumference = 2 * 3.14159 * 90  # radius=90
        stroke_dashoffset = circumference * (1 - pct)
        color = phase_colors[phase]
        
        st.markdown(f"""
        <div style='display:flex; flex-direction:column; align-items:center; padding:2rem 0;'>
            <div class='phase-label' style='color:{color};'>{phase_labels[phase]}</div>
            <div style='position:relative; margin:1.5rem 0;'>
                <svg width='220' height='220' viewBox='0 0 220 220'>
                    <circle cx='110' cy='110' r='90' fill='none' stroke='#1e293b' stroke-width='12'/>
                    <circle cx='110' cy='110' r='90' fill='none' stroke='{color}' stroke-width='12'
                        stroke-dasharray='{circumference:.1f}' stroke-dashoffset='{stroke_dashoffset:.1f}'
                        stroke-linecap='round' transform='rotate(-90 110 110)'
                        style='transition: stroke-dashoffset 1s linear;'/>
                    <text x='110' y='100' text-anchor='middle' font-size='38' font-weight='900' fill='#f1f5f9' font-family='monospace'>
                        {mins:02d}:{secs:02d}
                    </text>
                    <text x='110' y='130' text-anchor='middle' font-size='13' fill='#94a3b8'>
                        {'RUNNING' if st.session_state.pomo_running else 'READY'}
                    </text>
                    <text x='110' y='152' text-anchor='middle' font-size='12' fill='{color}'>
                        {f'Pomodoro {st.session_state.pomo_count % 4 + 1} of 4'}
                    </text>
                </svg>
            </div>
            <div style='display:flex; gap:0.5rem; margin-bottom:1rem;'>
                {''.join([f'<div style="width:12px;height:12px;border-radius:50%;background:{"#6366f1" if i < st.session_state.pomo_count % 4 else "#1e293b"};border:2px solid #6366f1;"></div>' for i in range(4)])}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Controls
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if not st.session_state.pomo_running:
                if st.button("▶ Start", use_container_width=True, type="primary"):
                    st.session_state.pomo_running = True
                    st.session_state.pomo_end_time = datetime.datetime.now() + datetime.timedelta(seconds=remaining)
                    st.rerun()
            else:
                if st.button("⏸ Pause", use_container_width=True):
                    st.session_state.pomo_running = False
                    st.session_state.pomo_end_time = None
                    st.rerun()
        with c2:
            if st.button("⏭ Skip", use_container_width=True):
                if phase == "focus":
                    st.session_state.pomo_count += 1
                    if st.session_state.pomo_count % 4 == 0:
                        st.session_state.pomo_phase = "long_break"
                    else:
                        st.session_state.pomo_phase = "short_break"
                else:
                    st.session_state.pomo_phase = "focus"
                st.session_state.pomo_running = False
                st.session_state.pomo_end_time = None
                st.rerun()
        with c3:
            if st.button("↺ Reset", use_container_width=True):
                st.session_state.pomo_running = False
                st.session_state.pomo_end_time = None
                st.rerun()
        with c4:
            if st.button("🔄 New", use_container_width=True):
                st.session_state.pomo_running = False
                st.session_state.pomo_phase = "focus"
                st.session_state.pomo_count = 0
                st.session_state.pomo_end_time = None
                st.rerun()
        
        # Auto-refresh when running
        if st.session_state.pomo_running:
            time.sleep(1)
            st.rerun()
        
        # Settings
        st.markdown("---")
        st.markdown("#### ⚙️ Timer Settings")
        
        if mood:
            st.info(f"{mood['emoji']} Mood-adapted: {default_focus}min focus, {default_break}min break")
        
        with st.expander("Customize durations"):
            st.session_state.pomo_focus_mins = st.slider("Focus duration (min)", 5, 60, st.session_state.pomo_focus_mins)
            st.session_state.pomo_short_break = st.slider("Short break (min)", 1, 20, st.session_state.pomo_short_break)
            st.session_state.pomo_long_break = st.slider("Long break (min)", 5, 30, st.session_state.pomo_long_break)
    
    with col_history:
        st.markdown("#### 📊 Session History")
        
        # Today's sessions
        today_sessions = execute_query(
            """SELECT * FROM pomodoro_sessions WHERE user_id = ? AND date(completed_at) = date('now')
               ORDER BY completed_at DESC""",
            (user['id'],), fetchall=True
        )
        
        all_sessions = execute_query(
            """SELECT * FROM pomodoro_sessions WHERE user_id = ?
               ORDER BY completed_at DESC LIMIT 20""",
            (user['id'],), fetchall=True
        )
        
        today_mins = sum(s.get('duration_minutes', 0) for s in today_sessions)
        total_sessions_count = execute_query(
            "SELECT COUNT(*) as cnt FROM pomodoro_sessions WHERE user_id = ?",
            (user['id'],), fetch=True
        )
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div class='mini-stat'>
                <div class='mini-stat-value'>{today_mins}m</div>
                <div class='mini-stat-label'>Today</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class='mini-stat'>
                <div class='mini-stat-value'>{total_sessions_count['cnt'] if total_sessions_count else 0}</div>
                <div class='mini-stat-label'>Total Sessions</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("**Today's Sessions:**" if today_sessions else "No sessions today yet.")
        
        for s in today_sessions:
            try:
                completed_at = datetime.datetime.fromisoformat(s['completed_at'])
                time_str = completed_at.strftime('%I:%M %p')
            except:
                time_str = "—"
            
            st.markdown(f"""
            <div class='session-item'>
                <div class='session-icon'>🍅</div>
                <div>
                    <div class='session-topic'>{s.get('topic', 'General Study') or 'General Study'}</div>
                    <div class='session-meta'>{s.get('duration_minutes', 0)} min · {time_str}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if len(all_sessions) > len(today_sessions):
            with st.expander(f"All sessions ({len(all_sessions)} total)"):
                for s in all_sessions:
                    try:
                        completed_at = datetime.datetime.fromisoformat(s['completed_at'])
                        date_str = completed_at.strftime('%b %d, %I:%M %p')
                    except:
                        date_str = "—"
                    st.markdown(f"🍅 **{s.get('topic', 'Study') or 'Study'}** — {s.get('duration_minutes', 0)}m — {date_str}")
