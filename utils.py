"""
Utility Module for AI Learning Buddy.
Handles environment variables, Gemini API configuration, calls, and error handling.
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

# Load environment variables from .env file (override system variables)
load_dotenv(override=True)

def get_api_key(custom_key=None):
    """
    Retrieve the Gemini API key.
    Order of preference:
    1. Custom key provided in the UI
    2. Environment variable GEMINI_API_KEY
    """
    key = None
    if custom_key and custom_key.strip():
        key = custom_key.strip()
    else:
        key = os.getenv("GEMINI_API_KEY")

    if key:
        # Strip surrounding quotes and whitespace
        key = key.strip("'\" \t\n\r")
    return key

def call_gemini(prompt, api_key=None, is_json=False):
    """
    Central wrapper to call Gemini API with error handling and model fallback.
    Tries a chain of model names from newest to oldest until one succeeds.
    """
    key = get_api_key(api_key)
    if not key or key == "your_gemini_api_key_here":
        raise ValueError(
            "API Key is missing. Please set the GEMINI_API_KEY in your .env file "
            "or enter it in the application sidebar."
        )

    # Configure the genai client
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
            # JSON mime type is only supported in newer models; skip for legacy ones
            if is_json and attempt_model not in ("gemini-pro", "gemini-1.0-pro"):
                generation_config["response_mime_type"] = "application/json"

            model = genai.GenerativeModel(attempt_model)
            response = model.generate_content(
                prompt,
                generation_config=generation_config,
                request_options=RequestOptions(timeout=30)
            )

            if not response or not response.text:
                raise Exception("Received an empty response from the Gemini API.")

            if attempt_model != "gemini-2.0-flash":
                logger.info(f"Used fallback model: {attempt_model}")
            return response.text

        except Exception as e:
            err = str(e)
            # Only continue the chain for 404 / model-not-found errors
            if "404" in err or "not found" in err.lower() or "unsupported" in err.lower():
                logger.warning(f"Model '{attempt_model}' unavailable. Trying next...")
                last_error = e
                continue

            # For auth, quota, network errors — raise immediately with friendly messages
            logger.error(f"Gemini API Error: {err}")
            if "API_KEY_INVALID" in err or "API key not valid" in err:
                raise Exception("Invalid API Key. Please verify the Gemini API key entered.")
            elif "quota" in err.lower() or "429" in err:
                raise Exception("API rate limit exceeded. Please wait a moment and try again.")
            elif "connection" in err.lower() or "host" in err.lower():
                raise Exception("Network connection failed. Please check your internet connection.")
            else:
                raise Exception(f"Gemini API error occurred: {err}")

    # All models in the chain were unavailable
    raise Exception(
        "All available Gemini models failed. Your google-generativeai library may be outdated.\n"
        "Please run:  python -m pip install --upgrade google-generativeai\n\n"
        f"Last error: {last_error}"
    )

def clean_json_string(raw_string):
    """
    Cleans markdown code block boundaries (like ```json ... ```) from a raw string
    to ensure it can be safely loaded by json.loads.
    """
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
    """
    Generates a concept explanation for the topic adapted to difficulty.
    """
    prompt = prompts.EXPLAIN_PROMPT.format(topic=topic, difficulty=difficulty)
    return call_gemini(prompt, api_key=api_key)

def get_example(topic, difficulty, api_key=None):
    """
    Generates a practical real-world example of the topic adapted to difficulty.
    """
    prompt = prompts.EXAMPLE_PROMPT.format(topic=topic, difficulty=difficulty)
    return call_gemini(prompt, api_key=api_key)

def get_quiz(topic, difficulty, api_key=None):
    """
    Generates exactly 5 quiz questions. Returns a parsed JSON list.
    """
    prompt = prompts.QUIZ_PROMPT.format(topic=topic, difficulty=difficulty)
    raw_json = call_gemini(prompt, api_key=api_key, is_json=True)
    cleaned_json = clean_json_string(raw_json)

    try:
        data = json.loads(cleaned_json)
        if "questions" not in data or not isinstance(data["questions"], list):
            raise ValueError("Invalid quiz format returned by API.")
        return data["questions"]
    except json.JSONDecodeError as je:
        logger.error(f"JSON Parse Error: {je}. Raw output was: {raw_json}")
        raise Exception("Failed to parse the generated quiz. Please try generating it again.")

def evaluate_short_answer(topic, question, expected_answer, user_answer, api_key=None):
    """
    Calls Gemini to check if a short answer response is correct.
    Returns: (is_correct, score, feedback)
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
    cleaned_json = clean_json_string(raw_json)

    try:
        data = json.loads(cleaned_json)
        return (
            data.get("is_correct", False),
            data.get("score", 0),
            data.get("feedback", "No feedback provided.")
        )
    except json.JSONDecodeError:
        # Fallback to simple string matching if parsing fails
        is_match = expected_answer.lower().strip() in user_answer.lower().strip()
        score = 1 if is_match else 0
        return is_match, score, "Evaluated using strict matching fallback."

def get_session_summary(topic, difficulty, score, api_key=None):
    """
    Generates a personalized progress recap and tutoring summary.
    """
    percentage = int((score / 5) * 100)
    prompt = prompts.SUMMARY_PROMPT.format(
        topic=topic,
        difficulty=difficulty,
        score=score,
        percentage=percentage
    )
    return call_gemini(prompt, api_key=api_key)
