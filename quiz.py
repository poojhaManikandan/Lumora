"""
Quiz Module for AI Learning Buddy.
Manages interactive question-by-question state, rendering inputs, grading answers, and displaying feedback.
"""
import streamlit as st
import utils
import feedback

def init_quiz_state(questions):
    """
    Initialize session state variables for a new quiz session.
    """
    st.session_state.quiz_questions = questions
    st.session_state.quiz_current_index = 0
    st.session_state.quiz_answers = [None] * 5
    st.session_state.quiz_results = [None] * 5
    st.session_state.quiz_submitted = [False] * 5
    st.session_state.quiz_completed = False
    st.session_state.quiz_score = 0
    st.session_state.quiz_active = True

def reset_quiz_state():
    """
    Reset all quiz variables in session state.
    """
    st.session_state.quiz_questions = None
    st.session_state.quiz_current_index = 0
    st.session_state.quiz_answers = [None] * 5
    st.session_state.quiz_results = [None] * 5
    st.session_state.quiz_submitted = [False] * 5
    st.session_state.quiz_completed = False
    st.session_state.quiz_score = 0
    st.session_state.quiz_active = False

def render_quiz(topic, difficulty, api_key=None):
    """
    Main renderer for the interactive quiz.
    """
    if "quiz_questions" not in st.session_state or st.session_state.quiz_questions is None:
        st.warning("No quiz questions loaded. Please generate a quiz first.")
        return

    questions = st.session_state.quiz_questions
    current_index = st.session_state.quiz_current_index

    # --- Case 1: Quiz is Completed ---
    if st.session_state.quiz_completed:
        score = st.session_state.quiz_score
        pct = feedback.get_percentage(score, 5)
        encourage = feedback.get_encouragement_feedback(score, 5)
        
        # Display completion badge and encouragement
        st.markdown(feedback.get_completion_badge_html(topic, difficulty, score, 5), unsafe_allow_html=True)
        
        # Encouraging Banner
        st.info(f"### {encourage['emoji']} {encourage['title']}\n{encourage['message']}")
        
        st.markdown("### 📝 Review Your Answers")
        
        # Display each question card
        for idx, q in enumerate(questions):
            ans = st.session_state.quiz_answers[idx]
            result = st.session_state.quiz_results[idx]
            
            card_html = feedback.get_answer_card_html(
                question_num=idx + 1,
                question_text=q["question_text"],
                user_answer=ans,
                correct_answer=q["correct_answer"],
                explanation=q["explanation"],
                is_correct=result.get("is_correct", False) if result else False
            )
            st.markdown(card_html, unsafe_allow_html=True)
            
        # Summary & Restart Options
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Try Quiz Again", use_container_width=True):
                # Shuffle/re-init quiz with the same questions
                init_quiz_state(questions)
                st.rerun()
        with col2:
            if st.button("✨ Start New Topic", use_container_width=True):
                st.session_state.topic_input = ""
                reset_quiz_state()
                st.rerun()
        return

    # --- Case 2: Quiz is In Progress ---
    q = questions[current_index]
    
    st.subheader(f"Question {current_index + 1} of 5")
    st.progress((current_index) / 5)

    # Render Question Container
    st.markdown(
        f"""
        <div style="
            background-color: #F8FAFC; 
            border: 1px solid #E2E8F0; 
            padding: 20px; 
            border-radius: 12px; 
            margin-bottom: 20px;
        ">
            <span style="
                background-color: #3B82F6; 
                color: white; 
                padding: 4px 10px; 
                border-radius: 8px; 
                font-size: 12px; 
                font-weight: bold; 
                text-transform: uppercase;
                vertical-align: middle;
                margin-right: 8px;
            ">{q['type']}</span>
            <span style="font-size: 18px; font-weight: 600; color: #1E293B; line-height: 1.5;">
                {q['question_text']}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Capture User Input based on type
    user_selection = None
    input_key = f"quiz_q_{current_index}_input"
    
    submitted = st.session_state.quiz_submitted[current_index]
    
    if q["type"] == "MCQ":
        # MCQ layout
        options = q.get("options", [])
        # Prevent default selection from counting as answered if user didn't choose, 
        # but Streamlit st.radio requires selecting something. We can add a placeholder or just default to index=0
        user_selection = st.radio(
            "Choose the correct option:",
            options=options,
            key=input_key,
            disabled=submitted
        )
    elif q["type"] == "True/False":
        user_selection = st.radio(
            "Select True or False:",
            options=["True", "False"],
            key=input_key,
            disabled=submitted
        )
    else:  # Short Answer
        user_selection = st.text_input(
            "Type your answer here:",
            key=input_key,
            placeholder="Type concise answer...",
            disabled=submitted
        )

    # Submission Action
    if not submitted:
        if st.button("📤 Submit Answer", use_container_width=True, type="primary"):
            if q["type"] == "Short Answer" and (not user_selection or not user_selection.strip()):
                st.warning("Please type an answer before submitting.")
                return

            st.session_state.quiz_answers[current_index] = user_selection
            
            # Grade Answer
            with st.spinner("AI Tutor is grading your answer..."):
                if q["type"] == "Short Answer":
                    # Evaluate using LLM helper
                    is_correct, score, feedback_text = utils.evaluate_short_answer(
                        topic=topic,
                        question=q["question_text"],
                        expected_answer=q["correct_answer"],
                        user_answer=user_selection,
                        api_key=api_key
                    )
                    result = {
                        "is_correct": is_correct,
                        "score": score,
                        "feedback": feedback_text
                    }
                else:
                    # MCQ / True/False strict evaluation
                    is_correct = user_selection.strip().lower() == q["correct_answer"].strip().lower()
                    score = 1 if is_correct else 0
                    feedback_text = "Spot on!" if is_correct else f"The correct answer is: {q['correct_answer']}"
                    result = {
                        "is_correct": is_correct,
                        "score": score,
                        "feedback": feedback_text
                    }
                    
            st.session_state.quiz_results[current_index] = result
            st.session_state.quiz_submitted[current_index] = True
            st.session_state.quiz_score += score
            st.rerun()
            
    else:
        # Display Instant Feedback
        result = st.session_state.quiz_results[current_index]
        is_correct = result.get("is_correct", False)
        feedback_text = result.get("feedback", "")
        
        if is_correct:
            st.success(f"🟢 **Correct!** {feedback_text}")
        else:
            st.error(f"🔴 **Incorrect.** Correct Answer: `{q['correct_answer']}`")
            st.info(f"💡 **Explanation:** {q['explanation']}")
            
        # Navigation Button to proceed
        button_label = "Proceed to Next Question ➡️" if current_index < 4 else "📊 Complete Quiz & View Results"
        if st.button(button_label, use_container_width=True):
            if current_index < 4:
                st.session_state.quiz_current_index += 1
            else:
                # Mark completed and save score to history
                st.session_state.quiz_completed = True
                
                # Append score history
                if "quiz_history" not in st.session_state:
                    st.session_state.quiz_history = []
                st.session_state.quiz_history.append({
                    "topic": topic,
                    "difficulty": difficulty,
                    "score": st.session_state.quiz_score
                })
                
            st.rerun()
