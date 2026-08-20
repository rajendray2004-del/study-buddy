import json

# Load quiz history
with open("quiz_history.json", "r") as f:
    history = json.load(f)

# Collect all wrong questions from all past attempts
all_wrong_questions = []
for attempt in history:
    all_wrong_questions.extend(attempt['wrong_questions'])

# Remove duplicate questions (same question asked wrong multiple times)
seen_questions = set()
unique_wrong_questions = []
for q in all_wrong_questions:
    if q['question'] not in seen_questions:
        unique_wrong_questions.append(q)
        seen_questions.add(q['question'])

if not unique_wrong_questions:
    print("🎉 No weak questions to review! You're doing great.")
else:
    print(f"📚 Reviewing {len(unique_wrong_questions)} question(s) you previously got wrong:\n")
    
    score = 0
    for i, q in enumerate(unique_wrong_questions):
        print(f"\nQ{i+1}: {q['question']}")
        for key, value in q['options'].items():
            print(f"  {key}) {value}")
        
        user_answer = input("Your answer (A/B/C/D): ").strip().upper()
        
        if user_answer == q['correct_answer']:
            print("✅ Correct! Great, you've improved on this one.")
            score += 1
        else:
            print(f"❌ Still wrong. Correct answer: {q['correct_answer']}")
    
    print(f"\n=== REVIEW SCORE: {score}/{len(unique_wrong_questions)} ===")