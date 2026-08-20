import streamlit as st
import pdfplumber
import google.generativeai as genai
import json
import datetime

st.title("📚 AI Study Buddy")

mode = st.radio("Choose mode:", ["New Quiz", "Review Weak Questions"], horizontal=True)

if mode == "Review Weak Questions":
    try:
        with open("quiz_history.json", "r") as f:
            history = json.load(f)
        all_wrong = []
        for attempt in history:
            all_wrong.extend(attempt['wrong_questions'])
        seen = set()
        review_questions = []
        for q in all_wrong:
            if q['question'] not in seen:
                review_questions.append(q)
                seen.add(q['question'])

        if not review_questions:
            st.success("🎉 No weak questions to review!")
        else:
            st.subheader(f"Reviewing {len(review_questions)} question(s)")
            review_score = 0
            for i, q in enumerate(review_questions):
                st.write(f"**Q{i+1}: {q['question']}**")
                options = [f"{k}) {v}" for k, v in q['options'].items()]
                choice = st.radio("Select:", options, key=f"rev{i}", index=None)
                if choice and choice[0] == q['correct_answer']:
                    review_score += 1
                st.divider()
            if st.button("Submit Review"):
                st.success(f"Review Score: {review_score}/{len(review_questions)}")
    except FileNotFoundError:
        st.info("No quiz history yet. Take a quiz first!")

    st.stop()

# ---------- NEW QUIZ MODE ----------

uploaded_file = st.file_uploader("Upload your notes (PDF, Word, or Text)", type=["pdf", "docx", "txt"])
num_questions = st.number_input("How many questions?", min_value=1, max_value=100, value=5, step=1)

if uploaded_file is not None:
    if "quiz_data" not in st.session_state:
        full_text = ""

        if uploaded_file.name.endswith(".pdf"):
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text

        elif uploaded_file.name.endswith(".docx"):
            import docx
            doc = docx.Document(uploaded_file)
            for para in doc.paragraphs:
                full_text += para.text + "\n"

        elif uploaded_file.name.endswith(".txt"):
            full_text = uploaded_file.read().decode("utf-8")

        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel("gemini-3.6-flash")

        prompt = f"""Generate {num_questions} multiple choice quiz questions based on this text.
Return ONLY valid JSON, no other text, in this exact format:
[
  {{
    "question": "...",
    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "correct_answer": "A",
    "topic": "short topic name"
  }}
]
Text:
{full_text[:3000]}"""

        with st.spinner("Generating quiz..."):
            response = model.generate_content(prompt)
            clean_text = response.text.strip().replace("```json", "").replace("```", "")
            st.session_state.quiz_data = json.loads(clean_text)
            st.session_state.answers = {}
            st.session_state.confidence = {}

    quiz_data = st.session_state.quiz_data

    for i, q in enumerate(quiz_data):
        st.subheader(f"Q{i+1}: {q['question']}")
        options = [f"{k}) {v}" for k, v in q['options'].items()]
        choice = st.radio("Select answer:", options, key=f"q{i}", index=None)
        confidence = st.select_slider(
            "How confident are you?",
            options=["Low", "Medium", "High"],
            key=f"conf{i}"
        )
        if choice:
            st.session_state.answers[i] = choice[0]
            st.session_state.confidence[i] = confidence
        st.divider()

    if st.button("Submit Quiz"):
        score = 0
        weak_topics = []
        overconfident = []
        underconfident = []
        confidences = st.session_state.get("confidence", {})

        for i, q in enumerate(quiz_data):
            user_ans = st.session_state.answers.get(i)
            conf = confidences.get(i, "Medium")
            is_correct = (user_ans == q['correct_answer'])

            if is_correct:
                score += 1
            else:
                weak_topics.append(q['topic'])

            if conf == "High" and not is_correct:
                overconfident.append(q['question'])
            if conf == "Low" and is_correct:
                underconfident.append(q['question'])

        st.success(f"Your Score: {score}/{len(quiz_data)}")

        if weak_topics:
            st.warning("Weak areas: " + ", ".join(set(weak_topics)))
        else:
            st.balloons()

        if overconfident:
            st.error("⚠️ Overconfident (sure, but wrong):")
            for q in overconfident:
                st.write(f"- {q}")

        if underconfident:
            st.info("💡 Underconfident (unsure, but correct):")
            for q in underconfident:
                st.write(f"- {q}")

        history_entry = {
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "score": score,
            "total": len(quiz_data),
            "weak_topics": weak_topics,
            "wrong_questions": [q for q in quiz_data if q['topic'] in weak_topics]
        }
        try:
            with open("quiz_history.json", "r") as f:
                history = json.load(f)
        except FileNotFoundError:
            history = []
        history.append(history_entry)
        with open("quiz_history.json", "w") as f:
            json.dump(history, f, indent=2)