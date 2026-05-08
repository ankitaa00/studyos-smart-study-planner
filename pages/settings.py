import streamlit as st
from utils.db import execute_query
from utils.auth import update_user_settings, delete_account, hash_password, verify_password

def show():
    user = st.session_state.user
    
    st.markdown("""
    <div class='page-header'>
        <div>
            <h1>⚙️ Settings</h1>
            <p class='subtitle'>Customize your study experience</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["⏱️ Pomodoro", "🔔 Notifications", "👤 Account"])
    
    with tab1:
        st.markdown("### ⏱️ Pomodoro Configuration")
        
        current_user = execute_query("SELECT * FROM users WHERE id = ?", (user['id'],), fetch=True)
        
        with st.form("pomodoro_settings"):
            c1, c2, c3 = st.columns(3)
            with c1:
                focus = st.number_input(
                    "Focus Duration (min)", min_value=5, max_value=90,
                    value=current_user.get('pomodoro_focus', 25) if current_user else 25
                )
            with c2:
                short_break = st.number_input(
                    "Short Break (min)", min_value=1, max_value=30,
                    value=current_user.get('pomodoro_short_break', 5) if current_user else 5
                )
            with c3:
                long_break = st.number_input(
                    "Long Break (min)", min_value=5, max_value=60,
                    value=current_user.get('pomodoro_long_break', 15) if current_user else 15
                )
            
            if st.form_submit_button("💾 Save Timer Settings", use_container_width=True, type="primary"):
                update_user_settings(
                    user['id'],
                    pomodoro_focus=focus,
                    pomodoro_short_break=short_break,
                    pomodoro_long_break=long_break
                )
                st.session_state.pomo_focus_mins = focus
                st.session_state.pomo_short_break = short_break
                st.session_state.pomo_long_break = long_break
                st.success("✅ Timer settings saved!")
        
        st.markdown("---")
        st.markdown("### 🌙 Reset Mood")
        if st.button("Re-check Today's Mood", use_container_width=True):
            st.session_state.mood_checked = False
            st.session_state.mood = None
            st.session_state.page = "dashboard"
            st.rerun()
    
    with tab2:
        st.markdown("### 🔔 Notification Preferences")
        
        st.markdown("""
        <div class='info-card'>
            <strong>📱 Desktop Notifications</strong><br>
            StudyOS can send browser notifications to remind you of upcoming study sessions and exams.
            Enable notifications in your browser when prompted.
        </div>
        """, unsafe_allow_html=True)
        
        current_user = execute_query("SELECT * FROM users WHERE id = ?", (user['id'],), fetch=True)
        notif_enabled = bool(current_user.get('notifications_enabled', 1)) if current_user else True
        
        with st.form("notif_settings"):
            enable_notifs = st.checkbox(
                "Enable desktop notifications",
                value=notif_enabled
            )
            
            st.markdown("**Notification triggers:**")
            c1, c2 = st.columns(2)
            with c1:
                st.checkbox("7 days before exam", value=True)
                st.checkbox("1 day before exam", value=True)
            with c2:
                st.checkbox("At scheduled study slot", value=True)
                st.checkbox("Pomodoro session end", value=True)
            
            if st.form_submit_button("💾 Save Notification Settings", use_container_width=True, type="primary"):
                update_user_settings(user['id'], notifications_enabled=1 if enable_notifs else 0)
                st.success("✅ Notification settings saved!")
        
        # Browser notification JS
        st.markdown("""
        <div style='margin-top:1rem;'>
        <button onclick="
            if ('Notification' in window) {
                Notification.requestPermission().then(p => {
                    if (p === 'granted') {
                        new Notification('StudyOS', {body: 'Notifications enabled! You will be reminded of your study sessions.'});
                    }
                });
            }
        " style='background:linear-gradient(135deg, #6366f1, #a855f7); color:white; border:none; 
                  padding:0.75rem 1.5rem; border-radius:8px; cursor:pointer; font-size:0.9rem;'>
            🔔 Enable Browser Notifications
        </button>
        </div>
        """, unsafe_allow_html=True)
    
    with tab3:
        st.markdown("### 👤 Account Management")
        
        # Profile info
        st.markdown(f"""
        <div class='info-card'>
            <div style='font-size:2rem; font-weight:900; margin-bottom:0.5rem;'>
                {user['name'][0].upper()}
            </div>
            <div><strong>{user['name']}</strong></div>
            <div style='color:#94a3b8;'>{user['email']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Change password
        st.markdown("#### 🔒 Change Password")
        with st.form("change_password"):
            current_pw = st.text_input("Current Password", type="password")
            new_pw = st.text_input("New Password", type="password")
            confirm_pw = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("🔒 Update Password", use_container_width=True):
                if not verify_password(current_pw, user['password_hash']):
                    st.error("Current password is incorrect.")
                elif new_pw != confirm_pw:
                    st.error("New passwords don't match.")
                elif len(new_pw) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    new_hash = hash_password(new_pw)
                    execute_query("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user['id']))
                    st.success("✅ Password updated successfully!")
        
        # Clear data
        st.markdown("---")
        st.markdown("#### 🧹 Data Management")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear All Topics", use_container_width=True):
                execute_query("DELETE FROM topics WHERE user_id = ?", (user['id'],))
                st.success("All topics cleared.")
                st.rerun()
        with col2:
            if st.button("🗑️ Clear Session History", use_container_width=True):
                execute_query("DELETE FROM pomodoro_sessions WHERE user_id = ?", (user['id'],))
                st.success("Session history cleared.")
                st.rerun()
        
        # Delete account
        st.markdown("---")
        st.markdown("#### ⚠️ Danger Zone")
        st.warning("Deleting your account is permanent and cannot be undone.")
        
        with st.form("delete_account"):
            confirm_delete = st.text_input(
                f'Type your email to confirm: **{user["email"]}**',
                placeholder=user['email']
            )
            if st.form_submit_button("🚫 Delete My Account", use_container_width=True):
                if confirm_delete == user['email']:
                    delete_account(user['id'])
                    from utils.auth import logout_user
                    logout_user()
                    st.success("Account deleted.")
                    st.rerun()
                else:
                    st.error("Email confirmation doesn't match.")
