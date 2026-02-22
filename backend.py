import os
import logging
import google.generativeai as genai
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import re
from difflib import SequenceMatcher

# Configure logging
logging.basicConfig(filename='app.log', level=logging.ERROR)

TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# ------------------- AI Model Setup Function ---------------------------
def get_ai_model():
    """AI Model ko initialize karne ka function"""
    # Agar environment variable nahi hai toh yahan apni API key paste karein
    api_key = os.getenv("GOOGLE_API_KEY") or "YOUR_ACTUAL_API_KEY_HERE"
    
    genai.configure(api_key=api_key)
    
    # Isme safety settings add ki hain taaki Aadhaar ya IDs block na ho
    return genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        safety_settings=[
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
    )

# ------------------- Pdf to Images Conversion ---------------------------
def generate_images(pdf_path: str) -> list:
    try:
        # Poppler path update karein agar error aaye
        images = convert_from_path(pdf_path, poppler_path=r'C:\Users\jhadi\OneDrive\ドキュメント\poppler-25.12.0\Library\bin')
        return images
    except Exception as e:
        logging.error(f"Error generating images from PDF: {e}")
        raise

# --------------------- Text Recognition ----------------------------------
def generate_text(img: Image) -> str:
    try:
        text = pytesseract.image_to_string(img)
        return text
    except Exception as e:
        logging.error(f"Error extracting text from image: {e}")
        raise

# ------------------ AI Model for Keyword Extraction ----------------------
def get_keywords(model_answer: str) -> str:
    try:
        model = get_ai_model() # Model call yahan ho raha hai
        prompt = f"Extract the important keywords for evaluating the student's answer based on the following model answer: {model_answer}. Provide keywords in a single line, separated by commas."
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
        else:
            return "general, content" # Fallback keywords
    except Exception as e:
        logging.error(f"Error extracting keywords: {e}")
        return "important, keywords"

# ------------------ Feedback Generation -----------------------
def get_feedback(studentAnswer, modelAnswer, predictedMarks):
    try:
        model = get_ai_model()
        prompt = f"The student's answer is: {studentAnswer}. The model answer is: {modelAnswer} and the predicted marks out of 10 is: {predictedMarks}. Give me the feedback of the student's answer in short."
        res = model.generate_content(prompt)
        if res and res.text:
            return res.text.strip()
        return "Good attempt."
    except Exception as e:
        return "No feedback available."

# ------------------ Scoring Mechanism ------------------------------------
def marks(student_answer: str, model_answer: str, max_marks: float, keywords: str) -> float:
    if not student_answer.strip():
        return 0 
    
    similarity = SequenceMatcher(None, student_answer.lower(), model_answer.lower()).ratio()
    if similarity >= 0.95:
        return max_marks
    
    student_answer_lower = student_answer.lower()
    keywords_lower = [kw.strip().lower() for kw in keywords.split(",") if kw.strip()]
    
    # Simple keyword check
    found_count = 0
    for kw in keywords_lower:
        if kw in student_answer_lower:
            found_count += 1
            
    if not keywords_lower: return 0
    marks_obtained = (found_count / len(keywords_lower)) * max_marks
    return round(marks_obtained, 2)

# --------------- Segregation Logic -----------------------
def segregate_questions_and_answers(text: str) -> list:
    # Yeh pattern "Answer 1]" ko dhundta hai
    segments = re.split(r'(?i)\bAnswer\s*\d+[a-z]?\]', text)
    answers = [segment.strip() for segment in segments if segment.strip()]
    return answers

# --------------- Main Function to Process ---------------------------
def process_answers(student_pdf: str, actual_answers_pdf: str, max_marks: float = 10) -> tuple:
    model_images = generate_images(actual_answers_pdf)
    model_text = " ".join([generate_text(img) for img in model_images])
    
    student_images = generate_images(student_pdf)
    student_text = " ".join([generate_text(img) for img in student_images])

    model_answers = segregate_questions_and_answers(model_text)
    student_answers = segregate_questions_and_answers(student_text)

    # Agar Aadhaar card scan kar rahe hain toh pattern match nahi hoga
    # Isliye fallback: agar answers list empty hai toh pura text use karein
    if not model_answers: model_answers = [model_text]
    if not student_answers: student_answers = [student_text]

    results = []
    total_marks = 0

    # Dono list ko barabar karne ke liye
    min_len = min(len(model_answers), len(student_answers))

    for i in range(min_len):
        s_ans = student_answers[i]
        m_ans = model_answers[i]
        
        kw = get_keywords(m_ans)
        score = marks(s_ans, m_ans, max_marks, kw)
        feedback = get_feedback(s_ans, m_ans, score)
        
        results.append({
            'question_number': i + 1,
            'student_answer': s_ans[:100] + "...",
            'model_answer': m_ans[:100] + "...",
            'score': score,
            'feedback': feedback
        })
        total_marks += score

    return results, total_marks