import os
import json
import pdfplumber
import mysql.connector
import sys
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

# Configuration & Environment Setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "resume_db")

if not GEMINI_API_KEY:
    raise ValueError("Please set the GEMINI_API_KEY environment variable.")
if not MYSQL_USER or not MYSQL_PASSWORD:
    raise ValueError("Please set MYSQL_USER and MYSQL_PASSWORD environment variables.")

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-pro")

# MySQL Database Initialization
def init_db_connection():
    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS candidates (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            email VARCHAR(255),
            phone VARCHAR(50),
            skills TEXT,
            education TEXT,
            experience TEXT,
            raw_json JSON,
            parsed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    return conn, cursor

# PDF Text Extraction
def extract_text_from_pdf(file_path: str) -> str:
    text = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            txt = page.extract_text()
            if txt:
                text.append(txt)
    return "\n".join(text)

# Resume Parsing Logic
def parse_resume_with_gemini(text: str) -> dict:
    prompt = f"""
You are an expert resume parser. Extract the following details from this resume text:
- Full Name
- Email
- Phone Number
- Skills (list)
- Education (list)
- Work Experience (list of objects with title, company, start_date, end_date)

Return the output as a JSON object with keys: name, email, phone, skills, education, experience.

Resume Text:
{text}
"""

    try:
        response = model.generate_content(prompt)
        data = json.loads(response.text)
        return data
    except Exception as e:
        print(f"Error parsing resume: {e}", file=sys.stderr)
        sys.exit(1)

# Database Save Logic
def save_candidate_data(cursor, conn, data: dict):
    sql = (
        "INSERT INTO candidates "
        "(name, email, phone, skills, education, experience, raw_json) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)"
    )
    vals = (
        data.get("name"),
        data.get("email"),
        data.get("phone"),
        json.dumps(data.get("skills", [])),
        json.dumps(data.get("education", [])),
        json.dumps(data.get("experience", [])),
        json.dumps(data),
    )
    cursor.execute(sql, vals)
    conn.commit()
    print(f"Inserted candidate: {data.get('name')} (ID: {cursor.lastrowid})")

# Main Execution
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Resume Parser with Gemini + MySQL")
    parser.add_argument("file", help="Path to the PDF resume file")
    args = parser.parse_args()

    conn, cursor = init_db_connection()

    print("Extracting text from PDF...")
    resume_text = extract_text_from_pdf(args.file)

    print("Parsing resume with Gemini...")
    parsed_data = parse_resume_with_gemini(resume_text)

    print("Saving data to MySQL...")
    save_candidate_data(cursor, conn, parsed_data)

    cursor.close()
    conn.close()
    print("Done.")
