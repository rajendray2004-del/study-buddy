import pdfplumber
import google.generativeai as genai
import json

# Step 1: Extract text from PDF
with pdfplumber.open("mynotes.pdf") as pdf:
    full_text = ""
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            full_text += text

# Step 2: Set up connection to Gemini
genai.configure(api_key="PASTE_YOUR_KEY_HERE")
model = genai.GenerativeModel("gemini-3.6-flash")

# Step 3: Ask AI to generate quiz questions in JSON format
prompt = f"""Generate 5 multiple choice quiz questions based on this text.

Return ONLY valid JSON, no other text, in this exact format:
[
  {{
    "question": "...",
    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "correct_answer": "A",
    "topic": "short topic name, e.g. Pipelining or Cache Memory"
  }}
]

Text:
{full_text[:3000]}"""

response = model.generate_content(prompt)

# Step 4: Clean and parse the JSON response
clean_text = response.text.strip()
clean_text = clean_text.replace("```json", "").replace("```", "")

quiz_data = json.loads(clean_text)

# Step 5: Interactive quiz + weak-area tracking
score = 0
weak_topics = []
confidence_log = []

for i, q in enumerate(quiz_data):
    print(f"\nQ{i+1}: {q['question']}")
    for key, value in q['options'].items():
        print(f"  {key}) {value}")
    
        user_answer = input("Your answer (A/B/C/D): ").strip().upper()
    confidence = input("How confident are you? (High/Medium/Low): ").strip().capitalize()
    
    is_correct = (user_answer == q['correct_answer'])
    
    if is_correct:
        print("✅ Correct!")
        score += 1
    else:
        print(f"❌ Wrong. Correct answer: {q['correct_answer']}")
        weak_topics.append(q['topic'])
    
    confidence_log.append({
        "question": q['question'],
        "confidence": confidence,
        "correct": is_correct
    })

print(f"\n=== FINAL SCORE: {score}/{len(quiz_data)} ===")
overconfident = [c for c in confidence_log if c['confidence'] == 'High' and not c['correct']]
underconfident = [c for c in confidence_log if c['confidence'] == 'Low' and c['correct']]

if overconfident:
    print("\n⚠️ OVERCONFIDENT (you were sure, but wrong):")
    for c in overconfident:
        print(f"- {c['question']}")

if underconfident:
    print("\n💡 UNDERCONFIDENT (you doubted yourself, but got it right):")
    for c in underconfident:
        print(f"- {c['question']}")
if weak_topics:
    print("\n=== WEAK AREAS (topics you got wrong) ===")
    for topic in set(weak_topics):
        count = weak_topics.count(topic)
        print(f"- {topic} (missed {count} question{'s' if count > 1 else ''})")
else:
    print("\n🎉 No weak areas — you got everything right!")

import datetime

# Step 6: Save this quiz attempt to history file
history_entry = {
    "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    "score": score,
    "total": len(quiz_data),
    "weak_topics": weak_topics,
    "wrong_questions": [q for q in quiz_data if q['topic'] in weak_topics]
}

# Load existing history (if any)
try:
    with open("quiz_history.json", "r") as f:
        history = json.load(f)
except FileNotFoundError:
    history = []

history.append(history_entry)

# Save updated history
with open("quiz_history.json", "w") as f:
    json.dump(history, f, indent=2)

print("\n📁 Quiz attempt saved to quiz_history.json")