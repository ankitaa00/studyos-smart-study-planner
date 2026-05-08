import os
import json
import re
import streamlit as st
from anthropic import Anthropic

def get_client():
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None
    return Anthropic(api_key=api_key)

def rate_topic_difficulty(topic: str, subject: str = "") -> dict:
    """Rate the academic difficulty of a topic using Claude."""
    client = get_client()
    if not client:
        # Fallback: generate reasonable mock scores
        import random
        score = round(random.uniform(3, 8), 1)
        label = "Easy" if score < 4 else "Medium" if score < 6 else "Hard" if score < 8 else "Critical"
        return {"score": score, "reason": "AI rating unavailable (no API key)", "label": label}
    
    try:
        prompt = f"""Rate the academic difficulty of the topic "{topic}" {f'in {subject}' if subject else ''} on a scale of 1-10.

Respond ONLY with valid JSON in this exact format:
{{"score": 7.5, "reason": "Brief reason in one sentence", "label": "Hard"}}

Label must be one of: Easy (1-3), Medium (4-6), Hard (7-8), Critical (9-10)"""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        # Extract JSON
        match = re.search(r'\{.*?\}', text, re.DOTALL)
        if match:
            data = json.loads(match.group())
            score = float(data.get("score", 5))
            label = data.get("label", "Medium")
            # Ensure label matches score
            if score < 4: label = "Easy"
            elif score < 7: label = "Medium"
            elif score < 9: label = "Hard"
            else: label = "Critical"
            return {"score": score, "reason": data.get("reason", ""), "label": label}
    except Exception as e:
        pass
    
    return {"score": 5.0, "reason": "Could not rate difficulty.", "label": "Medium"}

def parse_syllabus_from_text(text: str) -> list:
    """Parse extracted OCR text into structured topics using Claude."""
    client = get_client()
    if not client:
        # Fallback: simple line-based parsing
        topics = []
        lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 3]
        for line in lines[:20]:
            topics.append({"subject": "General", "chapter": "Chapter 1", "topic": line})
        return topics
    
    try:
        prompt = f"""Parse this syllabus text and extract structured topics.

Syllabus text:
{text}

Return ONLY a JSON array. Each item must have: subject, chapter, topic.
Example: [{{"subject": "Mathematics", "chapter": "Algebra", "topic": "Quadratic Equations"}}]

Extract as many topics as you can find. If subject/chapter are unclear, infer from context."""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        text_resp = response.content[0].text.strip()
        match = re.search(r'\[.*\]', text_resp, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    
    return []

def predict_performance(topics: list, sessions: list, deadlines: list) -> dict:
    """Predict exam performance using Claude."""
    client = get_client()
    
    total_topics = len(topics)
    studied_topics = sum(1 for t in topics if t.get('studied'))
    avg_difficulty = sum(t.get('difficulty_score', 5) for t in topics) / max(total_topics, 1)
    total_hours = sum(s.get('duration_minutes', 0) for s in sessions) / 60
    completion_rate = (studied_topics / max(total_topics, 1)) * 100
    
    # Find nearest deadline
    import datetime
    days_until_exam = 30
    if deadlines:
        today = datetime.date.today()
        for d in deadlines:
            try:
                deadline_date = datetime.date.fromisoformat(d['deadline_date'])
                diff = (deadline_date - today).days
                if 0 < diff < days_until_exam:
                    days_until_exam = diff
            except:
                pass
    
    if not client:
        # Fallback prediction
        base_score = 40 + (completion_rate * 0.35) + (total_hours * 1.5) - (avg_difficulty * 2)
        base_score = max(30, min(98, base_score))
        return {
            "score_low": int(base_score - 7),
            "score_high": int(base_score + 7),
            "confidence": "Medium",
            "weakest_areas": [t['topic'] for t in sorted(topics, key=lambda x: x.get('difficulty_score', 5), reverse=True)[:3]],
            "recommendation": f"Study {max(0, int((100-completion_rate)/10))} more hours to improve your score by ~8%.",
            "extra_hours_needed": max(0, int((100 - completion_rate) / 10))
        }
    
    try:
        prompt = f"""You are an academic performance predictor. Given this student's data, predict their exam performance.

Data:
- Total topics: {total_topics}
- Topics studied: {studied_topics} ({completion_rate:.0f}% coverage)
- Total study hours logged: {total_hours:.1f}
- Average topic difficulty (1-10): {avg_difficulty:.1f}
- Days until exam: {days_until_exam}
- Weakest topics: {[t['topic'] for t in sorted(topics, key=lambda x: x.get('difficulty_score', 5), reverse=True)[:3]]}

Return ONLY valid JSON:
{{
  "score_low": 65,
  "score_high": 75,
  "confidence": "Medium",
  "weakest_areas": ["topic1", "topic2"],
  "recommendation": "If you study 5 more hours, prediction rises to 80-85%.",
  "extra_hours_needed": 5
}}"""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        text_resp = response.content[0].text.strip()
        match = re.search(r'\{.*\}', text_resp, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    
    return {
        "score_low": 60, "score_high": 75, "confidence": "Low",
        "weakest_areas": [], "recommendation": "Keep studying consistently.",
        "extra_hours_needed": 5
    }

def get_ai_study_tips(mood_key: str, topics: list) -> str:
    """Get personalized AI study tips based on mood and topics."""
    client = get_client()
    if not client:
        tips = {
            "energized": "🔥 You're in peak mode! Tackle your hardest topics first.",
            "focused": "🎯 Great focus! Work through topics systematically.",
            "neutral": "📚 Steady pace today. Mix difficult and easy topics.",
            "tired": "😴 Take it easy. Short 15-min sessions with breaks.",
            "stressed": "🌿 Breathe. Start with topics you already know well.",
            "anxious": "💙 You've got this. Small steps, frequent breaks."
        }
        return tips.get(mood_key, "📚 Study well today!")
    
    try:
        top_topics = [t['topic'] for t in topics[:5]]
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{"role": "user", "content": f"Give a 2-sentence motivational study tip for a student feeling {mood_key} who needs to study: {top_topics}. Be encouraging and specific."}]
        )
        return response.content[0].text.strip()
    except:
        return "📚 Stay consistent and trust the process!"
