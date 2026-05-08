import streamlit as st
import datetime
import math
from utils.db import execute_query
from utils.ai_utils import predict_performance

def draw_gauge(score_low, score_high, confidence):
    """Draw an SVG semicircle gauge."""
    mid = (score_low + score_high) / 2
    angle = (mid / 100) * 180 - 90  # -90 to 90 degrees
    rad = math.radians(angle)
    
    # Needle endpoint
    cx, cy = 110, 110
    r = 80
    nx = cx + r * math.cos(rad)
    ny = cy + r * math.sin(rad)
    
    # Color by confidence
    conf_colors = {"High": "#10b981", "Medium": "#f59e0b", "Low": "#ef4444"}
    color = conf_colors.get(confidence, "#6366f1")
    
    return f"""
    <svg viewBox='0 0 220 130' width='300' height='180' xmlns='http://www.w3.org/2000/svg'>
        <!-- Track -->
        <path d='M 20 110 A 90 90 0 0 1 200 110' fill='none' stroke='#1e293b' stroke-width='16' stroke-linecap='round'/>
        <!-- Red zone 0-40 -->
        <path d='M 20 110 A 90 90 0 0 1 65 30' fill='none' stroke='#ef444440' stroke-width='16' stroke-linecap='round'/>
        <!-- Yellow zone 40-70 -->
        <path d='M 65 30 A 90 90 0 0 1 155 30' fill='none' stroke='#f59e0b40' stroke-width='16' stroke-linecap='round'/>
        <!-- Green zone 70-100 -->
        <path d='M 155 30 A 90 90 0 0 1 200 110' fill='none' stroke='#10b98140' stroke-width='16' stroke-linecap='round'/>
        <!-- Needle -->
        <line x1='{cx}' y1='{cy}' x2='{nx:.1f}' y2='{ny:.1f}' stroke='{color}' stroke-width='3' stroke-linecap='round'/>
        <circle cx='{cx}' cy='{cy}' r='6' fill='{color}'/>
        <!-- Score text -->
        <text x='110' y='95' text-anchor='middle' font-size='28' font-weight='900' fill='#f1f5f9'>{score_low}-{score_high}%</text>
        <text x='110' y='115' text-anchor='middle' font-size='12' fill='#94a3b8'>{confidence} Confidence</text>
        <!-- Labels -->
        <text x='18' y='128' font-size='9' fill='#ef4444'>0</text>
        <text x='97' y='22' font-size='9' fill='#94a3b8'>50</text>
        <text x='196' y='128' font-size='9' fill='#10b981'>100</text>
    </svg>
    """

def show():
    user = st.session_state.user
    
    st.markdown("""
    <div class='page-header'>
        <div>
            <h1>📈 Performance Prediction</h1>
            <p class='subtitle'>AI-powered exam score prediction based on your study data</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    topics = execute_query("SELECT * FROM topics WHERE user_id = ?", (user['id'],), fetchall=True)
    sessions = execute_query("SELECT * FROM pomodoro_sessions WHERE user_id = ?", (user['id'],), fetchall=True)
    deadlines = execute_query("SELECT * FROM deadlines WHERE user_id = ?", (user['id'],), fetchall=True)
    
    if not topics:
        st.info("📚 Add topics in the Syllabus section to get performance predictions!")
        if st.button("Go to Syllabus →"):
            st.session_state.page = "syllabus"
            st.rerun()
        return
    
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.markdown("### 🎯 Prediction")
        
        if st.button("🔮 Generate / Update Prediction", type="primary", use_container_width=True):
            with st.spinner("AI is analyzing your study data..."):
                prediction = predict_performance(topics, sessions, deadlines)
                st.session_state.prediction = prediction
        
        prediction = st.session_state.get("prediction")
        
        if not prediction:
            # Auto-compute on first visit
            prediction = predict_performance(topics, sessions, deadlines)
            st.session_state.prediction = prediction
        
        # Score gauge
        gauge_svg = draw_gauge(
            prediction.get('score_low', 60),
            prediction.get('score_high', 75),
            prediction.get('confidence', 'Medium')
        )
        st.markdown(f"""
        <div style='display:flex; flex-direction:column; align-items:center; 
                    background:#0f172a; border-radius:16px; padding:1.5rem; margin-bottom:1rem;'>
            {gauge_svg}
        </div>
        """, unsafe_allow_html=True)
        
        conf = prediction.get('confidence', 'Medium')
        conf_colors = {"High": "#10b981", "Medium": "#f59e0b", "Low": "#ef4444"}
        conf_color = conf_colors.get(conf, "#6366f1")
        
        st.markdown(f"""
        <div style='background:#0f172a; border-radius:12px; padding:1rem; margin-bottom:1rem;'>
            <div style='color:#94a3b8; font-size:0.85rem;'>Confidence Level</div>
            <div style='color:{conf_color}; font-size:1.2rem; font-weight:700;'>● {conf}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Recommendation
        rec = prediction.get('recommendation', '')
        if rec:
            st.markdown(f"""
            <div class='ai-tip-card'>
                <span class='ai-badge'>🤖 AI Recommendation</span>
                <p style='margin-top:0.5rem;'>{rec}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Weakest areas
        weak = prediction.get('weakest_areas', [])
        if weak:
            st.markdown("**⚠️ Focus Areas:**")
            for area in weak[:3]:
                st.markdown(f"""
                <div style='background:#ef444415; border:1px solid #ef444440; border-radius:8px; 
                            padding:0.5rem 1rem; margin:0.3rem 0; color:#fca5a5; font-size:0.9rem;'>
                    ⚡ {area}
                </div>
                """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 📊 Study Analytics")
        
        # Progress stats
        total = len(topics)
        studied = sum(1 for t in topics if t.get('studied'))
        pct = (studied / total * 100) if total else 0
        total_hours = sum(s.get('duration_minutes', 0) for s in sessions) / 60
        
        # Stats cards
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            st.markdown(f"""<div class='stat-card'>
                <div class='stat-icon'>📖</div>
                <div class='stat-value'>{studied}/{total}</div>
                <div class='stat-label'>Topics Studied</div>
                <div class='stat-bar'><div class='stat-fill' style='width:{pct:.0f}%'></div></div>
                <div style='color:#94a3b8; font-size:0.8rem;'>{pct:.0f}% complete</div>
            </div>""", unsafe_allow_html=True)
        with r1c2:
            st.markdown(f"""<div class='stat-card'>
                <div class='stat-icon'>⏰</div>
                <div class='stat-value'>{total_hours:.1f}h</div>
                <div class='stat-label'>Hours Logged</div>
            </div>""", unsafe_allow_html=True)
        
        # Subject breakdown
        st.markdown("#### 📚 Coverage by Subject")
        subjects = {}
        for t in topics:
            sub = t.get('subject', 'Unknown')
            if sub not in subjects:
                subjects[sub] = {'total': 0, 'studied': 0}
            subjects[sub]['total'] += 1
            if t.get('studied'):
                subjects[sub]['studied'] += 1
        
        colors = ["#6366f1", "#10b981", "#f59e0b", "#ec4899", "#14b8a6"]
        for i, (sub, data) in enumerate(subjects.items()):
            pct_sub = (data['studied'] / data['total'] * 100) if data['total'] else 0
            color = colors[i % len(colors)]
            st.markdown(f"""
            <div style='margin-bottom:0.8rem;'>
                <div style='display:flex; justify-content:space-between; margin-bottom:4px;'>
                    <span style='font-size:0.9rem; color:#e2e8f0;'>{sub}</span>
                    <span style='font-size:0.9rem; color:{color};'>{data['studied']}/{data['total']} ({pct_sub:.0f}%)</span>
                </div>
                <div style='background:#1e293b; border-radius:99px; height:8px;'>
                    <div style='background:{color}; width:{pct_sub}%; height:100%; border-radius:99px; 
                                transition:width 0.5s ease;'></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Difficulty distribution
        st.markdown("#### ⚡ Topic Difficulty Distribution")
        diff_counts = {"Easy": 0, "Medium": 0, "Hard": 0, "Critical": 0}
        for t in topics:
            lbl = t.get('difficulty_label', 'Medium')
            if lbl in diff_counts:
                diff_counts[lbl] += 1
        
        diff_colors = {"Easy": "#10b981", "Medium": "#6366f1", "Hard": "#f59e0b", "Critical": "#ef4444"}
        d1, d2, d3, d4 = st.columns(4)
        for col, (label, count) in zip([d1, d2, d3, d4], diff_counts.items()):
            color = diff_colors[label]
            with col:
                st.markdown(f"""
                <div style='background:{color}15; border:1px solid {color}40; border-radius:10px; 
                            padding:0.75rem; text-align:center;'>
                    <div style='color:{color}; font-size:1.4rem; font-weight:900;'>{count}</div>
                    <div style='color:#94a3b8; font-size:0.75rem;'>{label}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Session streak
        st.markdown("#### 🔥 Study Streak")
        today = datetime.date.today()
        streak = 0
        for i in range(30):
            check_date = today - datetime.timedelta(days=i)
            day_sessions = execute_query(
                "SELECT COUNT(*) as cnt FROM pomodoro_sessions WHERE user_id = ? AND date(completed_at) = ?",
                (user['id'], check_date.isoformat()), fetch=True
            )
            if day_sessions and day_sessions['cnt'] > 0:
                streak += 1
            else:
                break
        
        streak_emoji = "🔥" * min(streak, 5) if streak > 0 else "💤"
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #f97316, #ef4444); border-radius:12px; 
                    padding:1rem; text-align:center; margin-top:0.5rem;'>
            <div style='font-size:2rem;'>{streak_emoji}</div>
            <div style='color:white; font-size:1.5rem; font-weight:900;'>{streak} Day Streak</div>
            <div style='color:#fed7aa; font-size:0.85rem;'>Keep it going!</div>
        </div>
        """, unsafe_allow_html=True)
