import streamlit as st
import datetime
from utils.db import execute_query

def generate_study_slots(user_id, deadlines):
    """Auto-generate study slots based on deadlines."""
    today = datetime.date.today()
    slots = []
    
    for d in deadlines:
        try:
            deadline_date = datetime.date.fromisoformat(d['deadline_date'])
            days_left = (deadline_date - today).days
            if days_left <= 0:
                continue
            
            coverage_hours = d.get('coverage_hours', 10)
            daily_hours = min(coverage_hours / max(days_left, 1), 3)  # max 3h/day
            
            for day_offset in range(min(days_left, 14)):
                slot_date = today + datetime.timedelta(days=day_offset)
                slots.append({
                    'subject': d['subject'],
                    'slot_date': slot_date.isoformat(),
                    'duration_hours': round(daily_hours, 1)
                })
        except:
            pass
    
    return slots

def show():
    user = st.session_state.user
    
    st.markdown("""
    <div class='page-header'>
        <div>
            <h1>📅 Study Schedule</h1>
            <p class='subtitle'>Manage exam deadlines and view your auto-generated study plan</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🎯 Deadlines", "📆 Study Calendar"])
    
    with tab1:
        st.markdown("### ➕ Add Exam / Assignment")
        with st.form("deadline_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                subject = st.text_input("Subject *", placeholder="e.g. Mathematics")
            with c2:
                deadline_type = st.selectbox("Type", ["exam", "assignment", "quiz"])
            with c3:
                coverage_hours = st.number_input("Study Hours Needed", min_value=1, max_value=100, value=10)
            
            deadline_date = st.date_input(
                "Deadline Date",
                min_value=datetime.date.today(),
                value=datetime.date.today() + datetime.timedelta(days=7)
            )
            
            submitted = st.form_submit_button("📌 Add Deadline", use_container_width=True, type="primary")
            if submitted:
                if subject.strip():
                    execute_query(
                        "INSERT INTO deadlines (user_id, subject, deadline_date, type, coverage_hours) VALUES (?,?,?,?,?)",
                        (user['id'], subject, deadline_date.isoformat(), deadline_type, coverage_hours)
                    )
                    st.success(f"✅ Added deadline: {subject} on {deadline_date}")
                    st.rerun()
                else:
                    st.error("Subject is required.")
        
        st.markdown("---")
        st.markdown("### 📋 Your Deadlines")
        
        deadlines = execute_query(
            "SELECT * FROM deadlines WHERE user_id = ? ORDER BY deadline_date ASC",
            (user['id'],), fetchall=True
        )
        
        if not deadlines:
            st.info("No deadlines added yet. Add your exams above to get started!")
            return
        
        today = datetime.date.today()
        type_icons = {"exam": "📝", "assignment": "📋", "quiz": "❓"}
        
        for d in deadlines:
            try:
                ddate = datetime.date.fromisoformat(d['deadline_date'])
                days_left = (ddate - today).days
                
                if days_left < 0:
                    color = "#64748b"
                    status = "Past"
                elif days_left == 0:
                    color = "#ef4444"
                    status = "🚨 TODAY!"
                elif days_left <= 3:
                    color = "#ef4444"
                    status = f"🔴 {days_left} days left"
                elif days_left <= 7:
                    color = "#f59e0b"
                    status = f"🟡 {days_left} days left"
                else:
                    color = "#10b981"
                    status = f"🟢 {days_left} days left"
                
                col1, col2 = st.columns([4, 1])
                with col1:
                    icon = type_icons.get(d['type'], "📅")
                    st.markdown(f"""
                    <div class='deadline-card-large' style='border-left: 5px solid {color};'>
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <div>
                                <div class='dl-title'>{icon} {d['subject']}</div>
                                <div class='dl-meta'>{d['type'].capitalize()} · {ddate.strftime('%B %d, %Y')} · {d.get('coverage_hours', 10)} hours needed</div>
                            </div>
                            <div class='dl-countdown' style='color:{color};'>{status}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button("🗑️ Remove", key=f"del_dl_{d['id']}", use_container_width=True):
                        execute_query("DELETE FROM deadlines WHERE id = ?", (d['id'],))
                        st.rerun()
                
                # Notification hints
                if 0 < days_left <= 7:
                    st.info(f"⏰ Notification: '{d['subject']} exam is in {days_left} day(s) — review now!'")
                    
            except Exception as e:
                pass
    
    with tab2:
        st.markdown("### 📆 Auto-Generated Study Schedule")
        
        deadlines = execute_query(
            "SELECT * FROM deadlines WHERE user_id = ? ORDER BY deadline_date ASC",
            (user['id'],), fetchall=True
        )
        
        if not deadlines:
            st.info("Add deadlines first to generate your study schedule.")
            return
        
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("#### Week Navigator")
            week_offset = st.number_input("Week offset", min_value=0, max_value=4, value=0, label_visibility="collapsed")
            if st.button("◀ Previous"):
                week_offset = max(0, week_offset - 1)
            if st.button("Next ▶"):
                week_offset = min(4, week_offset + 1)
        
        today = datetime.date.today()
        week_start = today + datetime.timedelta(days=week_offset * 7)
        week_start = week_start - datetime.timedelta(days=week_start.weekday())
        
        subject_colors = {}
        colors = ["#6366f1", "#10b981", "#f59e0b", "#ec4899", "#14b8a6", "#f97316", "#8b5cf6"]
        for i, d in enumerate(deadlines):
            subject_colors[d['subject']] = colors[i % len(colors)]
        
        with col2:
            st.markdown(f"#### Week of {week_start.strftime('%B %d, %Y')}")
            
            cols = st.columns(7)
            day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            
            slots = generate_study_slots(user['id'], deadlines)
            
            for i, (col, day_name) in enumerate(zip(cols, day_names)):
                day_date = week_start + datetime.timedelta(days=i)
                is_today = day_date == today
                
                day_slots = [s for s in slots if s['slot_date'] == day_date.isoformat()]
                
                with col:
                    header_style = "background: linear-gradient(135deg, #6366f1, #a855f7); color:white; border-radius:8px; padding:4px 8px;" if is_today else ""
                    st.markdown(f"""
                    <div style='{header_style} text-align:center; font-weight:bold; margin-bottom:8px;'>
                        {day_name}<br><small>{day_date.strftime('%d')}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if day_slots:
                        for slot in day_slots[:3]:
                            color = subject_colors.get(slot['subject'], '#6366f1')
                            st.markdown(f"""
                            <div style='background:{color}20; border-left:3px solid {color}; 
                                        padding:4px 8px; margin:4px 0; border-radius:4px;
                                        font-size:0.75rem; color:{color};'>
                                <strong>{slot['subject'][:12]}</strong><br>
                                {slot['duration_hours']}h
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='color:#94a3b8; font-size:0.75rem; text-align:center;'>—</div>", unsafe_allow_html=True)
        
        # Legend
        st.markdown("---")
        st.markdown("**Subject Legend:**")
        legend_cols = st.columns(len(deadlines) if deadlines else 1)
        for i, d in enumerate(deadlines):
            color = subject_colors.get(d['subject'], '#6366f1')
            with legend_cols[i % len(legend_cols)]:
                st.markdown(f"""
                <div style='display:flex; align-items:center; gap:8px;'>
                    <div style='width:12px; height:12px; background:{color}; border-radius:50%;'></div>
                    <span style='font-size:0.85rem;'>{d['subject']}</span>
                </div>
                """, unsafe_allow_html=True)
