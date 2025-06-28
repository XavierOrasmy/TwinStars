import os
import google.generativeai as genai
from dotenv import load_dotenv
import json

def _get_configured_model(model_name='models/gemini-1.5-flash-latest'):
    """Helper function to configure and return a Gemini model."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)

def extract_chart_data_from_text(student_work_text: str) -> list | None:
    """
    Uses AI to read unstructured text and extract structured data for a chart.
    """
    try:
        model = _get_configured_model()
        prompt = f"""
        You are a data extraction specialist. Your task is to read the following text from a student's submitted work (homework, quizzes, exams) and extract structured data points for a progress chart.

        For each distinct assignment or topic you can identify in the text, you must extract the following:
        1. "course": The general subject (e.g., "Calculus", "Algebra", "Spanish").
        2. "topic": The specific topic being tested (e.g., "Derivatives", "Factoring", "Verb Conjugation").
        3. "period": The name of the assignment (e.g., "Homework 1", "Quiz 3", "Mid-term Exam").
        4. "score": An estimated numerical score from 0 to 100 based on the content, instructor notes, and correctness of the answers.

        You MUST return your findings as a JSON string representing a list of objects. Do not include any explanatory text or markdown formatting, only the raw JSON string.

        Example output format:
        [
            {{"course": "Algebra", "topic": "Linear Equations", "period": "Homework 1", "score": 95}},
            {{"course": "Algebra", "topic": "Word Problems", "period": "Quiz 1", "score": 60}}
        ]

        ---
        **Student Work Content to Analyze:**
        {student_work_text}
        ---
        """
        response = model.generate_content(prompt)
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned_response)
    except Exception as e:
        print(f"ERROR in extract_chart_data_from_text: {e}")
        return None

def get_student_analysis(student_work_text: str, target_topics: str) -> str | None:
    """
    Analyzes student work and generates a detailed study plan with study questions.
    """
    try:
        model = _get_configured_model()
        prompt = f"""
        You are an expert educational analyst. Based on the following student work and list of topics, please perform a detailed three-part analysis.

        **Part 1: Analyze Existing Weaknesses**
        Analyze the provided student work to identify every area of underperformance. Then, present a ranked list of these topics from weakest to strongest.

        **Part 2: Predict Future Challenges (Forecasted Problematic Topics)**
        Using the ranked weakness profile from Part 1 and the full list of target topics, predict which upcoming subjects the student is most likely to struggle with. Provide a prioritized list of these future trouble spots.

        **Part 3: Generate a Tailored Study Plan**
        Generate a concise and actionable study plan to address both the current weak areas and the predicted challenges. For each topic in the study plan, you must include the following four items in this order:
        1.  **Key Concepts to Review:** A bulleted list of the most important concepts for that topic.
        2.  **Recommended Practice Exercises:** Suggestions for types of problems or questions to practice.
        3.  **Specific Study Questions:** Generate 2-3 targeted questions that directly test the key concepts for that topic.
        4.  **Resource Links or Summaries:** Provide a relevant, high-quality resource link or a brief summary of the topic.

        Please structure your entire output clearly with the following markdown headings:
        ### 1. Ranked List of Existing Weaknesses
        ### 2. Forecast of Future Trouble Spots
        ### 3. Tailored Study Plan

        ---
        **Provided Student Work Content:**
        {student_work_text}
        ---
        **Provided List of Target Topics:**
        {target_topics}
        ---
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"ERROR in get_student_analysis: {e}")
        return f"An error occurred while contacting the Gemini API: {e}"

def get_chat_response(chat_history: list, latest_question: str, original_analysis: str) -> str:
    """
    Generates a contextual response for the chat feature.
    """
    try:
        model = _get_configured_model()
        chat = model.start_chat(history=chat_history)
        contextual_prompt = f"""
        CONTEXT: You are a helpful tutor. The user has just received the following analysis about their academic performance:
        ---
        {original_analysis}
        ---
        Now, please answer the user's follow-up question based on this context.

        Question: {latest_question}
        """
        response = chat.send_message(contextual_prompt)
        return response.text
    except Exception as e:
        print(f"ERROR in get_chat_response: {e}")
        return f"Sorry, an error occurred while processing your chat message: {e}"