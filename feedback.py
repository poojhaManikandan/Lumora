"""
Feedback and Grading Module for AI Learning Buddy.
Handles grading calculations, encouraging messages, and beautiful custom HTML components.
"""

def get_percentage(score, total=5):
    """
    Calculate the percentage score.
    """
    if total <= 0:
        return 0
    return int((score / total) * 100)

def get_encouragement_feedback(score, total=5):
    """
    Get an encouraging message based on the quiz score.
    """
    percentage = get_percentage(score, total)
    
    if percentage == 100:
        return {
            "title": "🏆 Excellent! Perfect Score!",
            "message": "Outstanding work! You have completely mastered this concept at this difficulty. You're ready to tackle a new topic or step up the difficulty!",
            "color": "#4CAF50",
            "emoji": "🌟"
        }
    elif percentage >= 75:
        return {
            "title": "🎉 Good Job!",
            "message": "Great job! You have a solid grasp of this topic. Review the questions you missed to achieve a perfect score next time!",
            "color": "#2196F3",
            "emoji": "👍"
        }
    elif percentage >= 50:
        return {
            "title": "⚡ Decent Effort!",
            "message": "Not bad! You're halfway there. With a bit more review of the concept and examples, you'll master this in no time.",
            "color": "#FF9800",
            "emoji": "✍️"
        }
    else:
        return {
            "title": "📚 Needs More Practice!",
            "message": "Don't discourage yourself! Learning is an ongoing journey. Review the simple explanations, check the real-world examples, and try the quiz again.",
            "color": "#F44336",
            "emoji": "💡"
        }

def get_completion_badge_html(topic, difficulty, score, total=5):
    """
    Returns a custom styled HTML completion badge.
    """
    percentage = get_percentage(score, total)
    badge_colors = {
        100: "linear-gradient(135deg, #FFD700 0%, #FFA500 100%)", # Gold
        80: "linear-gradient(135deg, #C0C0C0 0%, #808080 100%)",  # Silver
        60: "linear-gradient(135deg, #CD7F32 0%, #8B4513 100%)",  # Bronze
    }
    
    # Fallback/Default color for scores below 60%
    badge_color = badge_colors.get(percentage, "linear-gradient(135deg, #6B7280 0%, #374151 100%)")
    text_color = "#FFFFFF"
    
    html = f"""
    <div style="text-align: center; margin: 25px 0;">
        <div style="
            display: inline-block;
            background: {badge_color};
            color: {text_color};
            padding: 20px 40px;
            border-radius: 20px;
            font-family: 'Outfit', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
            border: 2px solid rgba(255, 255, 255, 0.2);
            text-align: center;
        ">
            <span style="font-size: 40px; display: block; margin-bottom: 5px;">🏆</span>
            <span style="font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 2px; opacity: 0.9;">Completion Badge</span>
            <h2 style="margin: 5px 0 10px 0; font-size: 26px; font-weight: 800; color: white;">{topic.upper()}</h2>
            <div style="font-size: 14px; font-weight: 500; opacity: 0.95;">
                Difficulty: <span style="background: rgba(255,255,255,0.25); padding: 2px 8px; border-radius: 12px; font-weight: bold;">{difficulty}</span>
            </div>
            <div style="font-size: 20px; font-weight: 700; margin-top: 10px;">
                Score: {score} / {total} ({percentage}%)
            </div>
        </div>
    </div>
    """
    return html

def get_answer_card_html(question_num, question_text, user_answer, correct_answer, explanation, is_correct):
    """
    Returns custom styled HTML card for reviewing answers.
    """
    border_color = "#2E7D32" if is_correct else "#C62828"
    bg_color = "#E8F5E9" if is_correct else "#FFEBEE"
    status_text = "Correct" if is_correct else "Incorrect"
    status_icon = "🟢" if is_correct else "🔴"
    
    html = f"""
    <div style="
        border-left: 6px solid {border_color};
        background-color: {bg_color};
        padding: 18px;
        border-radius: 8px;
        margin-bottom: 15px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <strong style="font-size: 16px; color: #374151;">Question {question_num}</strong>
            <span style="font-size: 14px; font-weight: 600; color: {border_color};">
                {status_icon} {status_text}
            </span>
        </div>
        <p style="margin: 0 0 12px 0; color: #1F2937; font-size: 15px; line-height: 1.5;">{question_text}</p>
        
        <div style="font-size: 14px; margin-bottom: 8px;">
            <span style="color: #6B7280; font-weight: 500;">Your Answer:</span> 
            <span style="color: #111827; font-weight: bold;">{user_answer or '(No answer provided)'}</span>
        </div>
        
        <div style="font-size: 14px; margin-bottom: 12px;">
            <span style="color: #6B7280; font-weight: 500;">Correct Answer:</span> 
            <span style="color: #111827; font-weight: bold;">{correct_answer}</span>
        </div>
        
        <div style="border-top: 1px solid rgba(0,0,0,0.06); padding-top: 8px; font-size: 13.5px; color: #4B5563; line-height: 1.4;">
            <strong style="color: #374151;">Explanation:</strong> {explanation}
        </div>
    </div>
    """
    return html
