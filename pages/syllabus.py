import streamlit as st
import base64
from utils.db import execute_query
from utils.ai_utils import parse_syllabus_from_text, rate_topic_difficulty
import datetime

def compute_priority(difficulty_score, deadlines, subject):
    """Compute priority score based on difficulty and exam proximity."""
    import datetime
    today = datetime.date.today()
    exam_proximity_weight = 1
    
    for d in deadlines:
        if d.get('subject', '').lower() == subject.lower():
            try:
                ddate = datetime.date.fromisoformat(d['deadline_date'])
                days_left = (ddate - today).days
                if days_left <= 0:
                    exam_proximity_weight = 10
                elif days_left <= 3:
                    exam_proximity_weight = 10
                elif days_left <= 7:
                    exam_proximity_weight = 8
                elif days_left <= 14:
                    exam_proximity_weight = 6
                elif days_left <= 30:
                    exam_proximity_weight = 3
                else:
                    exam_proximity_weight = 1
            except:
                pass
    
    return round((difficulty_score * 0.6) + (exam_proximity_weight * 0.4), 2)

def show():
    user = st.session_state.user
    
    st.markdown("""
    <div class='page-header'>
        <div>
            <h1>📚 Syllabus Manager</h1>
            <p class='subtitle'>Upload your syllabus or add topics manually</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📸 Photo Upload / OCR", "✏️ Manual Entry", "📋 My Topics"])
    
    with tab1:
        st.markdown("### 📸 Upload Syllabus Photo")
        st.markdown("""
        <div class='upload-zone'>
            <div style='font-size:3rem;'>📷</div>
            <p>Upload a photo of your syllabus — AI will extract and structure the topics for you</p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose a syllabus image or PDF",
            type=["png", "jpg", "jpeg", "webp", "pdf"],
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            col1, col2 = st.columns([1, 1])
            with col1:
                if uploaded_file.type.startswith("image"):
                    st.image(uploaded_file, caption="Uploaded Syllabus", use_container_width=True)
            
            with col2:
                st.markdown("#### OCR Extraction")
                
                if "ocr_text" not in st.session_state:
                    st.session_state.ocr_text = ""
                if "parsed_topics" not in st.session_state:
                    st.session_state.parsed_topics = []
                
                if st.button("🔍 Extract Text with AI", use_container_width=True, type="primary"):
                    with st.spinner("Analyzing image with AI Vision..."):
                        try:
                            import anthropic, os
                            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
                            
                            file_bytes = uploaded_file.read()
                            b64 = base64.standard_b64encode(file_bytes).decode("utf-8")
                            media_type = uploaded_file.type if uploaded_file.type.startswith("image") else "image/jpeg"
                            
                            response = client.messages.create(
                                model="claude-sonnet-4-20250514",
                                max_tokens=2000,
                                messages=[{
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "image",
                                            "source": {"type": "base64", "media_type": media_type, "data": b64}
                                        },
                                        {
                                            "type": "text",
                                            "text": "Extract ALL text from this syllabus image. Return the raw text exactly as shown."
                                        }
                                    ]
                                }]
                            )
                            st.session_state.ocr_text = response.content[0].text
                            st.success("Text extracted successfully!")
                        except Exception as e:
                            st.warning(f"AI Vision unavailable. Please paste text manually below. ({str(e)[:50]})")
                            st.session_state.ocr_text = ""
                
                ocr_text = st.text_area(
                    "Extracted Text (edit if needed):",
                    value=st.session_state.get("ocr_text", ""),
                    height=200,
                    placeholder="OCR text will appear here, or paste your syllabus text manually..."
                )
                
                if ocr_text and st.button("🤖 Parse Topics with AI", use_container_width=True):
                    with st.spinner("AI is structuring your topics..."):
                        parsed = parse_syllabus_from_text(ocr_text)
                        st.session_state.parsed_topics = parsed
                        if parsed:
                            st.success(f"Found {len(parsed)} topics!")
                        else:
                            st.warning("Could not parse topics. Try manual entry.")
        
        # Editable parsed topics
        if st.session_state.get("parsed_topics"):
            st.markdown("---")
            st.markdown("### ✏️ Review & Edit Parsed Topics")
            st.caption("Edit any errors before saving to your planner")
            
            deadlines = execute_query("SELECT * FROM deadlines WHERE user_id = ?", (user['id'],), fetchall=True)
            
            edited_topics = []
            for i, t in enumerate(st.session_state.parsed_topics):
                with st.expander(f"📌 {t.get('topic', 'Topic')} — {t.get('subject', 'Subject')}", expanded=i < 3):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        sub = st.text_input("Subject", value=t.get('subject', ''), key=f"sub_{i}")
                    with c2:
                        chap = st.text_input("Chapter", value=t.get('chapter', ''), key=f"chap_{i}")
                    with c3:
                        topic = st.text_input("Topic", value=t.get('topic', ''), key=f"topic_{i}")
                    edited_topics.append({"subject": sub, "chapter": chap, "topic": topic})
            
            if st.button("💾 Save All Topics to Planner", type="primary", use_container_width=True):
                with st.spinner("Saving topics and rating difficulty with AI..."):
                    saved = 0
                    for t in edited_topics:
                        if t['topic'].strip():
                            diff = rate_topic_difficulty(t['topic'], t['subject'])
                            priority = compute_priority(diff['score'], deadlines, t['subject'])
                            execute_query(
                                """INSERT INTO topics (user_id, subject, chapter, topic, difficulty_score, 
                                   difficulty_reason, difficulty_label, priority_score)
                                   VALUES (?,?,?,?,?,?,?,?)""",
                                (user['id'], t['subject'], t['chapter'], t['topic'],
                                 diff['score'], diff['reason'], diff['label'], priority)
                            )
                            saved += 1
                    st.success(f"✅ Saved {saved} topics with AI difficulty ratings!")
                    st.session_state.parsed_topics = []
                    st.rerun()
    
    with tab2:
        st.markdown("### ✏️ Add Topics Manually")
        with st.form("manual_topic_form"):
            c1, c2 = st.columns(2)
            with c1:
                subject = st.text_input("Subject *", placeholder="e.g. Mathematics")
                topic = st.text_input("Topic *", placeholder="e.g. Quadratic Equations")
            with c2:
                chapter = st.text_input("Chapter", placeholder="e.g. Algebra")
                manual_diff = st.slider("Difficulty (1-10)", 1, 10, 5)
            
            submitted = st.form_submit_button("➕ Add Topic", use_container_width=True, type="primary")
            if submitted:
                if subject.strip() and topic.strip():
                    label = "Easy" if manual_diff < 4 else "Medium" if manual_diff < 7 else "Hard" if manual_diff < 9 else "Critical"
                    deadlines = execute_query("SELECT * FROM deadlines WHERE user_id = ?", (user['id'],), fetchall=True)
                    priority = compute_priority(manual_diff, deadlines, subject)
                    execute_query(
                        """INSERT INTO topics (user_id, subject, chapter, topic, difficulty_score,
                           difficulty_label, priority_score) VALUES (?,?,?,?,?,?,?)""",
                        (user['id'], subject, chapter, topic, float(manual_diff), label, priority)
                    )
                    st.success(f"✅ Added: {topic}")
                    st.rerun()
                else:
                    st.error("Subject and Topic are required.")
    
    with tab3:
        st.markdown("### 📋 All Topics")
        
        topics = execute_query(
            "SELECT * FROM topics WHERE user_id = ? ORDER BY priority_score DESC",
            (user['id'],), fetchall=True
        )
        
        if not topics:
            st.info("No topics yet. Upload a syllabus or add topics manually.")
            return
        
        # Filter and sort
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            subjects = ["All"] + list(set(t['subject'] for t in topics))
            filter_sub = st.selectbox("Filter by Subject", subjects)
        with col2:
            filter_status = st.selectbox("Status", ["All", "Not Studied", "Studied"])
        with col3:
            sort_by = st.selectbox("Sort by", ["Priority Score", "Difficulty", "Subject"])
        
        filtered = topics
        if filter_sub != "All":
            filtered = [t for t in filtered if t['subject'] == filter_sub]
        if filter_status == "Not Studied":
            filtered = [t for t in filtered if not t['studied']]
        elif filter_status == "Studied":
            filtered = [t for t in filtered if t['studied']]
        
        if sort_by == "Difficulty":
            filtered = sorted(filtered, key=lambda x: x.get('difficulty_score', 5), reverse=True)
        elif sort_by == "Subject":
            filtered = sorted(filtered, key=lambda x: x.get('subject', ''))
        
        label_colors = {"Easy": "#10b981", "Medium": "#6366f1", "Hard": "#f59e0b", "Critical": "#ef4444"}
        
        for t in filtered:
            color = label_colors.get(t.get('difficulty_label', 'Medium'), '#6366f1')
            checked = st.checkbox(
                f"**{t['topic']}** — {t['subject']} / {t.get('chapter', '')} | "
                f"Priority: {t.get('priority_score', 0):.1f} | "
                f"Difficulty: {t.get('difficulty_score', 5):.1f}/10",
                value=bool(t['studied']),
                key=f"topic_check_{t['id']}"
            )
            if checked != bool(t['studied']):
                execute_query("UPDATE topics SET studied = ? WHERE id = ?", (1 if checked else 0, t['id']))
                st.rerun()
            
            col_a, col_b = st.columns([6, 1])
            with col_b:
                if st.button("🗑️", key=f"del_topic_{t['id']}", help="Delete topic"):
                    execute_query("DELETE FROM topics WHERE id = ?", (t['id'],))
                    st.rerun()
