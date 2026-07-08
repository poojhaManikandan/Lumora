"""
Main Application Entry Point for Lumora - AI Learning Assistant.
Implements the Streamlit interface, custom styling, state management, and flow control.
"""
import streamlit as st
import utils
import quiz
import feedback
import os

# Set page configuration
st.set_page_config(
    page_title="Lumora – AI Learning Assistant",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Design Aesthetics
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap');

    /* Global styling */
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif !important;
    }
    
    /* Top title style */
    .app-title-container {
        text-align: center;
        margin-bottom: 25px;
        padding: 24px;
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
        border-radius: 16px;
        border: 1px solid #BFDBFE;
    }
    .app-title {
        font-size: 2.8rem;
        font-weight: 800;
        margin: 0;
        background: linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .app-subtitle {
        font-size: 1.1rem;
        color: #1E3A8A;
        margin-top: 5px;
        font-weight: 500;
    }
    
    /* Status indicators styling */
    .stSuccess, .stError, .stInfo, .stWarning {
        border-radius: 12px !important;
    }
    
    /* Standardized margins for content */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize Session States
if "topic_input" not in st.session_state:
    st.session_state.topic_input = ""
if "current_topic" not in st.session_state:
    st.session_state.current_topic = None
if "current_difficulty" not in st.session_state:
    st.session_state.current_difficulty = None
if "explanation_content" not in st.session_state:
    st.session_state.explanation_content = None
if "example_content" not in st.session_state:
    st.session_state.example_content = None
if "summary_content" not in st.session_state:
    st.session_state.summary_content = None
if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = None
if "quiz_history" not in st.session_state:
    st.session_state.quiz_history = []
if "custom_api_key" not in st.session_state:
    st.session_state.custom_api_key = ""

# Sidebar Layout
st.sidebar.markdown("# ✨ Lumora")
st.sidebar.caption("Your personalized AI-powered learning companion.")

# Difficulty Selection
difficulty = st.sidebar.selectbox(
    "🎯 Learning Difficulty",
    options=["Beginner", "Intermediate", "Advanced"],
    help=" Beginner: simple vocabulary & analogies. Intermediate: core concepts. Advanced: technical deep-dives."
)

st.sidebar.divider()

# Start New Topic Button
if st.sidebar.button("✨ Start New Topic", type="primary", use_container_width=True):
    st.session_state.topic_input = ""
    st.session_state.current_topic = None
    st.session_state.current_difficulty = None
    st.session_state.explanation_content = None
    st.session_state.example_content = None
    st.session_state.summary_content = None
    st.session_state.quiz_questions = None
    quiz.reset_quiz_state()
    st.sidebar.success("Session reset! Pick a new topic.")
    st.rerun()

st.sidebar.divider()

# About Expanders
with st.sidebar.expander("ℹ️ About Lumora"):
    st.markdown(
        """
        **Lumora** is an AI-powered learning assistant that adapts any topic to your skill level.
        
        It supports:
        - Conceptual explanations matching your level.
        - Relatable real-world analogies.
        - Interactive quizzes with AI grading for short answers.
        - Score history tracking.
        """
    )

with st.sidebar.expander("📖 Quick Instructions"):
    st.markdown(
        """
        1. **Select difficulty** above.
        2. **Enter a topic** in the main field.
        3. **Select an activity** (Explain, Example, Quiz, or Summary).
        4. Click **🚀 Let's Learn!** to execute.
        5. Complete the quiz to earn your Master Badge!
        """
    )

# Learning Score History in Sidebar
st.sidebar.divider()
st.sidebar.subheader("📊 Quiz Score History")
if st.session_state.quiz_history:
    for idx, record in enumerate(reversed(st.session_state.quiz_history)):
        st.sidebar.markdown(
            f"""
            <div style="
                background-color: #FFFFFF; 
                border-radius: 8px; 
                padding: 10px; 
                margin-bottom: 8px; 
                border-left: 4px solid #3B82F6;
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            ">
                <div style="font-weight: bold; font-size: 13.5px; color: #1F2937;">{record['topic']}</div>
                <div style="font-size: 11px; color: #6B7280;">Difficulty: {record['difficulty']}</div>
                <div style="font-size: 12.5px; font-weight: 600; color: #10B981; margin-top: 2px;">Score: {record['score']} / 5</div>
            </div>
            """,
            unsafe_allow_html=True
        )
else:
    st.sidebar.info("No quizzes completed yet. Your score history will appear here.")

# API Key Configuration in Sidebar
st.sidebar.divider()
env_key = os.getenv("GEMINI_API_KEY")
is_env_key_valid = env_key and env_key != "your_gemini_api_key_here"

# Always display the password field so users can override values at runtime
custom_key = st.sidebar.text_input(
    "🔑 Gemini API Key",
    value=st.session_state.custom_api_key or (env_key if is_env_key_valid else ""),
    type="password",
    help="Pasting a key here will override the .env file variable."
)

if custom_key:
    st.session_state.custom_api_key = custom_key

# Show status
if not utils.get_api_key(st.session_state.custom_api_key):
    st.sidebar.error("⚠️ API Key is required to run the AI features.")
else:
    st.sidebar.success("✅ API Key active!")

# Main Screen Layout
st.markdown(
    """
    <div class="app-title-container">
        <h1 class="app-title">✨ Lumora</h1>
        <div class="app-subtitle">Your AI-powered companion for smarter, deeper learning.</div>
    </div>
    """,
    unsafe_allow_html=True
)

# Main input section container
with st.container(border=True):
    st.markdown("### 🎓 What would you like to learn today?")
    
    # Topic Text Input
    topic_val = st.text_input(
        "Enter a concept, technology, or topic of your choice:",
        value=st.session_state.topic_input,
        placeholder="e.g. Neural Networks, Photosynthesis, Binary Search...",
        help="Type any topic you wish to study."
    )
    st.session_state.topic_input = topic_val



    # Activity Selection & Execution Button
    col_act, col_btn = st.columns([3, 1])
    with col_act:
        activity = st.radio(
            "Select an Activity:",
            options=["Explain Concept", "Real-Life Example", "Generate Quiz", "Tutoring Summary"],
            horizontal=True,
            help="Choose how the AI Buddy should help you master the topic."
        )
    with col_btn:
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        start_btn = st.button("🚀 Let's Learn!", use_container_width=True, type="primary")

# Resolve API Key
active_key = utils.get_api_key(st.session_state.custom_api_key)

# Trigger Action on Start Button
if start_btn:
    # Validation 1: Check empty topic
    if not st.session_state.topic_input.strip():
        st.warning("⚠️ Please specify a learning topic to begin.")
    # Validation 2: Check API key availability
    elif not active_key or active_key == "your_gemini_api_key_here":
        st.error("⚠️ Gemini API key is missing. Please enter it in the sidebar.")
    else:
        # Check if topic or difficulty changed, reset cached session results if so
        if (st.session_state.current_topic != st.session_state.topic_input.strip() or
            st.session_state.current_difficulty != difficulty):
            
            st.session_state.current_topic = st.session_state.topic_input.strip()
            st.session_state.current_difficulty = difficulty
            st.session_state.explanation_content = None
            st.session_state.example_content = None
            st.session_state.summary_content = None
            st.session_state.quiz_questions = None
            quiz.reset_quiz_state()

        # Run selected activity
        try:
            if activity == "Explain Concept":
                with st.spinner(f"Generating explanation for '{st.session_state.current_topic}'..."):
                    st.session_state.explanation_content = utils.get_explanation(
                        st.session_state.current_topic,
                        st.session_state.current_difficulty,
                        active_key
                    )
            elif activity == "Real-Life Example":
                with st.spinner("Creating a practical real-world analogy..."):
                    st.session_state.example_content = utils.get_example(
                        st.session_state.current_topic,
                        st.session_state.current_difficulty,
                        active_key
                    )
            elif activity == "Generate Quiz":
                with st.spinner("Assembling custom quiz questions..."):
                    questions = utils.get_quiz(
                        st.session_state.current_topic,
                        st.session_state.current_difficulty,
                        active_key
                    )
                    quiz.init_quiz_state(questions)
            elif activity == "Tutoring Summary":
                # Ensure they have completed quiz or explanation
                score_to_pass = st.session_state.get("quiz_score", 0) if st.session_state.get("quiz_completed", False) else 0
                with st.spinner("Reviewing your study session data..."):
                    st.session_state.summary_content = utils.get_session_summary(
                        st.session_state.current_topic,
                        st.session_state.current_difficulty,
                        score_to_pass,
                        active_key
                    )
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Display Outputs based on Current Selections
if st.session_state.current_topic:
    st.divider()
    
    # 1. Explanation Panel
    if activity == "Explain Concept" and st.session_state.explanation_content:
        with st.container(border=True):
            st.markdown(f"### 📖 Concept Explanation ({st.session_state.current_difficulty})")
            st.markdown(f"**Topic:** `{st.session_state.current_topic}`")
            st.divider()
            st.markdown(st.session_state.explanation_content)

    # 2. Example Panel
    elif activity == "Real-Life Example" and st.session_state.example_content:
        with st.container(border=True):
            st.markdown(f"### 💡 Real-Life Analogy ({st.session_state.current_difficulty})")
            st.markdown(f"**Topic:** `{st.session_state.current_topic}`")
            st.divider()
            st.markdown(st.session_state.example_content)

    # 3. Quiz Panel
    elif activity == "Generate Quiz" and st.session_state.quiz_questions:
        with st.container(border=True):
            st.markdown(f"### ✍️ Interactive Practice Quiz ({st.session_state.current_difficulty})")
            st.markdown(f"**Topic:** `{st.session_state.current_topic}`")
            st.divider()
            quiz.render_quiz(
                st.session_state.current_topic,
                st.session_state.current_difficulty,
                active_key
            )

    # 4. Summary Panel
    elif activity == "Tutoring Summary" and st.session_state.summary_content:
        with st.container(border=True):
            st.markdown(f"### 📊 Tutoring Session Summary")
            st.markdown(f"**Topic:** `{st.session_state.current_topic}`")
            st.divider()
            st.markdown(st.session_state.summary_content)
            
            # Simple navigation button to reset
            if st.button("🌟 Finish and Pick a New Topic", use_container_width=True):
                st.session_state.topic_input = ""
                st.session_state.current_topic = None
                st.session_state.current_difficulty = None
                st.session_state.explanation_content = None
                st.session_state.example_content = None
                st.session_state.summary_content = None
                st.session_state.quiz_questions = None
                quiz.reset_quiz_state()
                st.rerun()
else:
    # Landing instructions
    st.info("💡 Enter a topic and click **🚀 Let's Learn!** to begin your study session.")
