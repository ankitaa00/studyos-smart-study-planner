# 🎓 StudyOS — AI-Powered Smart Study Planner

A full-featured, intelligent study planner built with Python and Streamlit. Powered by Claude AI.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔐 Auth | Register/login with bcrypt-hashed passwords, persistent sessions |
| 📸 Syllabus OCR | Upload a photo → Claude Vision extracts and structures topics |
| 😊 Mood Detection | Daily mood check-in adapts session length, topic order, breaks |
| 📅 Deadline Management | Add exams/assignments, auto-schedule study slots, countdown cards |
| ⚖️ Topic Weighting | AI rates difficulty 1-10, computes Priority Score per topic |
| ⏱️ Pomodoro Timer | SVG countdown ring, configurable durations, session logging |
| 📈 Performance Prediction | AI predicts exam score range, confidence, weakest areas |

---

## 🚀 Quick Start

### 1. Clone / Open in VS Code

```bash
# Open the folder in VS Code
code smart_study_planner/
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up your API key

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your Anthropic API key
# Get yours free at: https://console.anthropic.com/
```

Your `.env` file should look like:
```
ANTHROPIC_API_KEY=sk-ant-...
```

### 5. Run the app

```bash
streamlit run app.py
```

The app will open at **http://localhost:8501**

---

## 📁 Project Structure

```
smart_study_planner/
├── app.py                  # Main entry point, routing, auth shell
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── README.md               # This file
│
├── pages/                  # One file per page
│   ├── dashboard.py        # Home dashboard with stats & today's plan
│   ├── syllabus.py         # OCR upload + topic management
│   ├── schedule.py         # Deadlines + auto-generated calendar
│   ├── pomodoro.py         # Full Pomodoro timer with session history
│   ├── performance.py      # AI predictions + analytics
│   └── settings.py         # Pomodoro config, notifications, account
│
├── utils/                  # Shared utilities
│   ├── db.py               # SQLite database layer
│   ├── auth.py             # bcrypt auth, session management
│   └── ai_utils.py         # Claude API calls (OCR, difficulty, prediction)
│
├── assets/
│   └── styles.css          # Complete dark-theme design system
│
└── data/
    └── studyos.db          # SQLite database (auto-created on first run)
```

---

## 🔑 API Key Notes

The app works **without an API key** with graceful fallbacks:
- Topic difficulty uses randomized scores
- Syllabus parsing uses simple line-by-line extraction
- Performance prediction uses a formula-based calculation

With an `ANTHROPIC_API_KEY`:
- Claude Vision reads your syllabus photos
- Claude rates each topic's academic difficulty
- Claude predicts your exam performance with reasoning

---

## 🗄️ Database

Uses SQLite (no setup required). Tables:

- `users` — accounts, settings (hashed passwords)
- `topics` — syllabus topics with difficulty + priority scores
- `deadlines` — exam/assignment deadlines
- `pomodoro_sessions` — completed study sessions
- `study_slots` — auto-generated study schedule

---

## 🎨 Design

- **Dark theme** with indigo/purple accent palette
- **Space Grotesk** + **JetBrains Mono** fonts
- SVG Pomodoro ring, score gauge, progress bars
- Mood-adaptive session configurations
- Fully responsive layout

---

## 📋 All 7 Core Features

1. ✅ **Authentication** — Register, login, logout, delete account, change password
2. ✅ **Syllabus OCR** — Photo upload → Claude Vision → editable topic list → saved with AI difficulty ratings
3. ✅ **Mood Detection** — 6 mood options, adapts session length/order/breaks, shows reasoning
4. ✅ **Deadline Management** — Add deadlines, countdown cards, auto-schedule study slots, notification UI
5. ✅ **Topic Difficulty Weighting** — AI rates 1-10, Priority = (difficulty×0.6) + (proximity×0.4), sortable with badges
6. ✅ **Pomodoro Timer** — SVG ring, Start/Pause/Skip/Reset, session counter, mood-adapted durations, history log
7. ✅ **Performance Prediction** — Score gauge (arc), confidence level, weakest areas, AI recommendations, streak tracker

---

## 🛠️ Tech Stack

- **Frontend/Backend**: Streamlit (Python)
- **Database**: SQLite via Python `sqlite3`
- **Auth**: bcrypt password hashing
- **AI**: Anthropic Claude (claude-sonnet-4-20250514)
- **Fonts**: Google Fonts (Space Grotesk, JetBrains Mono)
