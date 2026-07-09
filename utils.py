"""
Utility Module for Lumora - AI Learning Assistant.
Handles environment variables, Gemini API configuration, calls, and error handling.
NO blocking time.sleep() — Streamlit Cloud compatible.
"""
import os
import json
import logging
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import RequestOptions
import prompts

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(override=True)


def get_api_key(custom_key=None):
    """
    Retrieve the Gemini API key.
    Priority: custom sidebar key > .env GEMINI_API_KEY
    """
    key = custom_key.strip() if custom_key and custom_key.strip() else os.getenv("GEMINI_API_KEY")
    if key:
        key = key.strip("'\" \t\n\r")
    return key


def call_gemini(prompt, api_key=None, is_json=False):
    """
    Call the Gemini API with a model fallback chain.
    Raises clear, user-friendly errors immediately — no blocking sleeps.
    """
    key = get_api_key(api_key)
    if not key or key == "your_gemini_api_key_here":
        raise ValueError(
            "API Key is missing. Please enter your Gemini API key in the sidebar."
        )

    genai.configure(api_key=key)

    # Model fallback chain — newest to oldest
    model_chain = [
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.0-pro",
        "gemini-pro",
    ]

    last_error = None
    for attempt_model in model_chain:
        try:
            generation_config = {}
            if is_json and attempt_model not in ("gemini-pro", "gemini-1.0-pro"):
                generation_config["response_mime_type"] = "application/json"

            model = genai.GenerativeModel(attempt_model)
            response = model.generate_content(
                prompt,
                generation_config=generation_config,
                request_options=RequestOptions(timeout=30)
            )

            if not response or not response.text:
                raise Exception("Empty response from Gemini API.")

            return response.text

        except Exception as e:
            err = str(e)

            # ── Model not found → try next model ──────────────────────────────
            if "404" in err or "not found" in err.lower() or "unsupported" in err.lower():
                logger.warning(f"Model '{attempt_model}' unavailable, trying next...")
                last_error = e
                continue

            # ── Auth / key invalid ────────────────────────────────────────────
            if any(x in err for x in ["401", "API_KEY_INVALID", "API key not valid",
                                       "ACCESS_TOKEN_TYPE_UNSUPPORTED"]):
                raise Exception(
                    "❌ Invalid API Key.\n\n"
                    "Your Gemini API key was rejected. Please:\n"
                    "1. Go to aistudio.google.com/apikey\n"
                    "2. Create a new API key\n"
                    "3. Paste it in the sidebar 🔑 field"
                )

            # ── Rate limit (429) ──────────────────────────────────────────────
            if "429" in err or "quota" in err.lower() or "resource_exhausted" in err.lower():
                raise Exception(
                    "⏱️ API quota limit reached.\n\n"
                    "This happens when too many requests are made too quickly, "
                    "or the daily free limit (1,500 req/day) is reached.\n\n"
                    "✅ Fix:\n"
                    "• Wait 1–2 minutes, then try again\n"
                    "• Or use a fresh API key from aistudio.google.com/apikey"
                )

            # ── Network error ─────────────────────────────────────────────────
            if "connection" in err.lower() or "host" in err.lower() or "timeout" in err.lower():
                raise Exception(
                    "🌐 Network error. Please check your internet connection and try again."
                )

            # ── Any other error ───────────────────────────────────────────────
            raise Exception(f"Gemini API error: {err}")

    raise Exception(
        "All Gemini models are currently unavailable.\n"
        "Please try again in a moment or run:\n"
        "pip install --upgrade google-generativeai"
    )


def clean_json_string(raw_string):
    """Strip markdown code fences from raw Gemini JSON output."""
    text = raw_string.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def get_explanation(topic, difficulty, api_key=None):
    """Generate a concept explanation adapted to the selected difficulty."""
    prompt = prompts.EXPLAIN_PROMPT.format(topic=topic, difficulty=difficulty)
    return call_gemini(prompt, api_key=api_key)


def get_example(topic, difficulty, api_key=None):
    """Generate a real-world analogy for the topic adapted to difficulty."""
    prompt = prompts.EXAMPLE_PROMPT.format(topic=topic, difficulty=difficulty)
    return call_gemini(prompt, api_key=api_key)


def get_quiz(topic, difficulty, api_key=None):
    """Generate 5 quiz questions. Returns a parsed list of question dicts."""
    prompt = prompts.QUIZ_PROMPT.format(topic=topic, difficulty=difficulty)
    raw_json = call_gemini(prompt, api_key=api_key, is_json=True)
    cleaned = clean_json_string(raw_json)
    try:
        data = json.loads(cleaned)
        if "questions" not in data or not isinstance(data["questions"], list):
            raise ValueError("Unexpected quiz format.")
        return data["questions"]
    except json.JSONDecodeError as je:
        logger.error(f"JSON parse error: {je} — raw: {raw_json[:300]}")
        raise Exception("Could not parse the quiz response. Please try again.")


def evaluate_short_answer(topic, question, expected_answer, user_answer, api_key=None):
    """
    Use Gemini to grade a short-answer response.
    Returns: (is_correct: bool, score: int, feedback: str)
    """
    if not user_answer or not user_answer.strip():
        return False, 0, "No answer was provided."

    prompt = prompts.EVALUATE_PROMPT.format(
        topic=topic,
        question=question,
        expected_answer=expected_answer,
        user_answer=user_answer
    )
    raw_json = call_gemini(prompt, api_key=api_key, is_json=True)
    cleaned = clean_json_string(raw_json)
    try:
        data = json.loads(cleaned)
        return (
            data.get("is_correct", False),
            data.get("score", 0),
            data.get("feedback", "No feedback provided.")
        )
    except json.JSONDecodeError:
        is_match = expected_answer.lower().strip() in user_answer.lower().strip()
        return is_match, (1 if is_match else 0), "Graded by keyword matching."


def get_session_summary(topic, difficulty, score, api_key=None):
    """Generate a personalized session recap and next-steps summary."""
    percentage = int((score / 5) * 100)
    prompt = prompts.SUMMARY_PROMPT.format(
        topic=topic,
        difficulty=difficulty,
        score=score,
        percentage=percentage
    )
    return call_gemini(prompt, api_key=api_key)
