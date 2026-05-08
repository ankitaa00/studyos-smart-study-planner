import streamlit as st
import datetime
from utils.db import execute_query
from utils.ai_utils import get_ai_study_tips

def show():
    user = st.session_state.user
    mood = st.session_state.mood
    
    # Header
    hour = datetime.datetime.now().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"
    
    st.markdown(f"""
    <div class='page-header'>
        <div>
            <h1>{greeting}, {user['name'].split()[0]}! 👋</h1>
            <p class='subtitle'>
                {f"Feeling {mood['emoji']} {mood['label']} today — {mood['desc']}" if mood else "Let's make today count!"}
            </p>
        </div>
        <div class='date-badge'>{datetime.date.today().strftime('%A, %B %d')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Mood adaptation note
    if mood:
        mood_configs = {
            "energized": {"color": "#10b981", "sessions": "45 min", "note": "Long power sessions scheduled — you can handle it!"},
            "focused": {"color": "#6366f1", "sessions": "30 min", "note": "Balanced sessions for sustained deep work."},
            "neutral": {"color": "#94a3b8", "sessions": "25 min", "note": "Standard Pomodoro schedule applied."},
            "tired": {"color": "#f59e0b", "sessions": "15 min", "note": "Short, manageable sessions. Rest is part of studying!"},
            "stressed": {"color": "#f97316", "sessions": "20 min", "note": "Starting with familiar topics to build confidence."},
            "anxious": {"color": "#ec4899", "sessions": "15 min", "note": "Frequent breaks scheduled. Take it one topic at a time."},
        }
        cfg = mood_configs.get(mood["key"], mood_configs["neutral"])
        st.markdown(f"""
        <div class='mood-adaptation-card' style='border-left: 4px solid {cfg["color"]};'>
            <strong>{mood['emoji']} Mood Adaptation Active</strong> — 
            {cfg['note']} Session length set to <strong>{cfg['sessions']}</strong>.
        </div>
        """, unsafe_allow_html=True)
    
    # Stats row
    topics = execute_query("SELECT * FROM topics WHERE user_id = ?", (user['id'],), fetchall=True)
    deadlines = execute_query("SELECT * FROM deadlines WHERE user_id = ?", (user['id'],), fetchall=True)
    sessions = execute_query(
        "SELECT * FROM pomodoro_sessions WHERE user_id = ? AND date(completed_at) = date('now')",
        (user['id'],), fetchall=True
    )
    total_sessions = execute_query(
        "SELECT COUNT(*) as cnt FROM pomodoro_sessions WHERE user_id = ?",
        (user['id'],), fetch=True
    )
    
    studied = sum(1 for t in topics if t.get('studied'))
    total = len(topics)
    pct = int((studied / total * 100)) if total else 0
    today_mins = sum(s.get('duration_minutes', 0) for s in sessions)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class='stat-card'>
            <div class='stat-icon'>📚</div>
            <div class='stat-value'>{studied}/{total}</div>
            <div class='stat-label'>Topics Covered</div>
            <div class='stat-bar'><div class='stat-fill' style='width:{pct}%'></div></div>
        </div>""", unsafe_allow_html=True)
    
    with c2:
        st.markdown(f"""<div class='stat-card'>
            <div class='stat-icon'>⏱️</div>
            <div class='stat-value'>{today_mins}m</div>
            <div class='stat-label'>Studied Today</div>
        </div>""", unsafe_allow_html=True)
    
    with c3:
        st.markdown(f"""<div class='stat-card'>
            <div class='stat-icon'>🍅</div>
            <div class='stat-value'>{total_sessions['cnt'] if total_sessions else 0}</div>
            <div class='stat-label'>Total Pomodoros</div>
        </div>""", unsafe_allow_html=True)
    
    with c4:
        st.markdown(f"""<div class='stat-card'>
            <div class='stat-icon'>📅</div>
            <div class='stat-value'>{len(deadlines)}</div>
            <div class='stat-label'>Upcoming Exams</div>
        </div>""", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_left, col_right = st.columns([1.4, 1])
    
    with col_left:
        # Today's study plan
        st.markdown("### 📋 Today's Study Plan")
        
        if mood:
            mood_configs = {
                "energized": 45, "focused": 30, "neutral": 25,
                "tired": 15, "stressed": 20, "anxious": 15
            }
            session_len = mood_configs.get(mood["key"], 25)
        else:
            session_len = 25
        
        # Priority topics
        priority_topics = execute_query(
            "SELECT * FROM topics WHERE user_id = ? AND studied = 0 ORDER BY priority_score DESC LIMIT 6",
            (user['id'],), fetchall=True
        )
        
        if priority_topics:
            now = datetime.datetime.now()
            start_hour = max(now.hour + 1, 9)
            
            for i, topic in enumerate(priority_topics[:4]):
                slot_time = datetime.time(hour=(start_hour + i) % 24, minute=0)
                label_colors = {"Easy": "#10b981", "Medium": "#6366f1", "Hard": "#f59e0b", "Critical": "#ef4444"}
                color = label_colors.get(topic.get('difficulty_label', 'Medium'), '#6366f1')
                
                st.markdown(f"""
                <div class='schedule-item'>
                    <div class='time-col'>{slot_time.strftime('%I:%M %p')}</div>
                    <div class='schedule-content'>
                        <div class='schedule-topic'>{topic['topic']}</div>
                        <div class='schedule-meta'>{topic['subject']} · {session_len} min 
                            <span class='badge' style='background:{color}20; color:{color};'>
                                {topic.get('difficulty_label','Medium')}
                            </span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("🎉 No pending topics! Add topics in the Syllabus section.")
        
        # AI tip
        if topics:
            tip = get_ai_study_tips(mood["key"] if mood else "neutral", topics)
            st.markdown(f"""
            <div class='ai-tip-card'>
                <span class='ai-badge'>✨ AI Tip</span>
                <p>{tip}</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col_right:
        # Deadline countdown cards
        st.markdown("### 🎯 Exam Countdown")
        
        if deadlines:
            today = datetime.date.today()
            sorted_deadlines = sorted(deadlines, key=lambda d: d['deadline_date'])
            
            for deadline in sorted_deadlines[:4]:
                try:
                    ddate = datetime.date.fromisoformat(deadline['deadline_date'])
                    days_left = (ddate - today).days
                    
                    if days_left < 0:
                        urgency_color = "#64748b"
                        urgency = "Past"
                    elif days_left == 0:
                        urgency_color = "#ef4444"
                        urgency = "TODAY"
                    elif days_left <= 3:
                        urgency_color = "#ef4444"
                        urgency = f"{days_left}d"
                    elif days_left <= 7:
                        urgency_color = "#f59e0b"
                        urgency = f"{days_left}d"
                    else:
                        urgency_color = "#10b981"
                        urgency = f"{days_left}d"
                    
                    type_icons = {"exam": "📝", "assignment": "📋", "quiz": "❓"}
                    icon = type_icons.get(deadline['type'], "📅")
                    
                    st.markdown(f"""
                    <div class='deadline-card' style='border-left: 4px solid {urgency_color};'>
                        <div class='deadline-header'>
                            <span>{icon} {deadline['subject']}</span>
                            <span class='countdown' style='color:{urgency_color};'>{urgency}</span>
                        </div>
                        <div class='deadline-meta'>{deadline['type'].capitalize()} · {ddate.strftime('%b %d, %Y')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                except:
                    pass
        else:
            st.info("No deadlines yet. Add them in Schedule →")
            if st.button("➕ Add Deadline", use_container_width=True):
                st.session_state.page = "schedule"
                st.rerun()
