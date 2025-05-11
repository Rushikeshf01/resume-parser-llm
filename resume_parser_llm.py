import os
import json
import sys
import pdfplumber
import mysql.connector
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from openai import OpenAI
from google import genai

from dotenv import load_dotenv

load_dotenv()

# ----------------------------------------
# Configuration & Environment Setup
# ----------------------------------------
# Ensure the following environment variables are set:
#   OPENAI_API_KEY: Your OpenAI API key
#   MYSQL_HOST: MySQL host, e.g., "localhost"
#   MYSQL_USER: MySQL username
#   MYSQL_PASSWORD: MySQL password
#   MYSQL_DATABASE: MySQL database name, e.g., "resume_db"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "resume_db")

if not OPENAI_API_KEY:
    raise ValueError("Please set the OPENAI_API_KEY environment variable.")
if not MYSQL_USER or not MYSQL_PASSWORD:
    raise ValueError("Please set MYSQL_USER and MYSQL_PASSWORD environment variables.")

# ----------------------------------------
# MySQL Database Initialization
# ----------------------------------------
def init_db_connection():
    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )
    cursor = conn.cursor()

    cursor.execute("CREATE DATABASE IF NOT EXISTS resume_db;")
    cursor.execute("USE resume_db;")

    # Create table if it doesn't exist
    tables = {
        'candidate': (
            "CREATE TABLE IF NOT EXISTS candidate ("
            "id INT AUTO_INCREMENT PRIMARY KEY,"
            "name VARCHAR(255),"
            "email VARCHAR(255),"
            "phone VARCHAR(50)"
            ");"
        ),
        'skills': (
            "CREATE TABLE IF NOT EXISTS skills ("
            "id INT AUTO_INCREMENT PRIMARY KEY,"
            "candidate_id INT,"
            "skill VARCHAR(100),"
            "FOREIGN KEY (candidate_id) REFERENCES candidate(id) ON DELETE CASCADE"
            ");"
        ),
        'education': (
            "CREATE TABLE IF NOT EXISTS education ("
            "id INT AUTO_INCREMENT PRIMARY KEY,"
            "candidate_id INT,"
            "degree VARCHAR(255),"
            "institution VARCHAR(255),"
            "start_date VARCHAR(50),"
            "end_date VARCHAR(50),"
            "cgpa VARCHAR(20),"
            "percentage VARCHAR(20),"
            "FOREIGN KEY (candidate_id) REFERENCES candidate(id) ON DELETE CASCADE"
            ");"
        ),
        'experience': (
            "CREATE TABLE IF NOT EXISTS experience ("
            "id INT AUTO_INCREMENT PRIMARY KEY,"
            "candidate_id INT,"
            "title VARCHAR(255),"
            "company VARCHAR(255),"
            "start_date VARCHAR(50),"
            "end_date VARCHAR(50),"
            "FOREIGN KEY (candidate_id) REFERENCES candidate(id) ON DELETE CASCADE"
            ");"
        ),
        'projects': (
            "CREATE TABLE IF NOT EXISTS projects ("
            "id INT AUTO_INCREMENT PRIMARY KEY,"
            "candidate_id INT,"
            "title VARCHAR(255),"
            "description TEXT,"
            "github_link VARCHAR(255),"
            "start_date VARCHAR(50),"
            "end_date VARCHAR(50),"
            "FOREIGN KEY (candidate_id) REFERENCES candidate(id) ON DELETE CASCADE"
            ");"
        )
    }

    # Execute creation of each table
    for stmt in tables.values():
        cursor.execute(stmt)

    return conn, cursor

def insert_candidate_data(cursor, candidate):
    """
    Inserts candidate core info and returns the new candidate_id.
    """
    sql = "INSERT INTO candidate (name, email, phone) VALUES (%s, %s, %s)"
    data = (candidate['name'], candidate['email'], candidate['phone'])
    cursor.execute(sql, data)
    return cursor.lastrowid

def insert_skills(cursor, candidate_id, skills):
    """
    Inserts the list of skills for the candidate.
    """
    sql = "INSERT INTO skills (candidate_id, skill) VALUES (%s, %s)"
    for skill in skills:
        cursor.execute(sql, (candidate_id, skill))

def insert_education(cursor, candidate_id, education_list):
    """
    Inserts education records for the candidate.
    """
    sql = ("INSERT INTO education (candidate_id, degree, institution, start_date, end_date, cgpa, percentage) "
           "VALUES (%s, %s, %s, %s, %s, %s, %s)")
    for edu in education_list:
        cursor.execute(sql, (
            candidate_id,
            edu.get('degree'),
            edu.get('institution'),
            edu.get('start_date'),
            edu.get('end_date'),
            edu.get('cgpa'),
            edu.get('percentage')
        ))
    
def insert_experience(cursor, candidate_id, experience_list):
    """
    Inserts professional experience records for the candidate.
    """
    sql = ("INSERT INTO experience (candidate_id, title, company, start_date, end_date) "
           "VALUES (%s, %s, %s, %s, %s)")
    for exp in experience_list:
        cursor.execute(sql, (
            candidate_id,
            exp.get('title'),
            exp.get('company'),
            exp.get('start_date'),
            exp.get('end_date')
        ))

def insert_projects(cursor, candidate_id, project_list):
    print(project_list)
    sql = ("INSERT INTO projects (candidate_id, title, description, github_link, start_date, end_date) "
           "VALUES (%s, %s, %s, %s, %s, %s)")
    for proj in project_list:
        cursor.execute(sql, (
            candidate_id,
            proj.get('title'),
            proj.get('description'),
            proj.get('github_link'),
            proj.get('start_date'),
            proj.get('end_date')
        ))
    print("projects inserted----------------------")


# ----------------------------------------
# PDF Text Extraction
# ----------------------------------------
def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text content from a PDF file.
    """
    text = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
    return "\n".join(text)

# ----------------------------------------
# LangChain LLM Setup
# ----------------------------------------
# def setup_llm_chain():
#     """
#     Configure the LangChain LLMChain for resume parsing.
#     """
#     llm = ChatOpenAI(
#         model_name="gpt-3.5-turbo",
#         temperature=0,
#         openai_api_key=OPENAI_API_KEY
#     )

    #     prompt = PromptTemplate(
    #         input_variables=["resume_text"],
    #         template="""
    # You are an expert resume parser. Extract the following details from this resume text:
    # - Full Name
    # - Email
    # - Phone Number
    # - Skills (list)
    # - Education (list)
    # - Work Experience (list of objects with title, company, start_date, end_date)

    # Return the output as a JSON object with keys: name, email, phone, skills, education, experience.

    # Resume Text:
    # {resume_text}
    # """
    #     )


    # prompt = ChatPromptTemplate.from_template("""
    #             You are an expert resume parser. Extract the following details from this resume text:
    #             - Full Name
    #             - Email
    #             - Phone Number
    #             - Skills (list)
    #             - Education (list)
    #             - Work Experience (list of objects with title, company, start_date, end_date)

    #             Return the output as a JSON object with keys: name, email, phone, skills, education, experience.

    #             Resume Text:
    #             {resume_text}
    #             """
    #         )

    # parser = JsonOutputParser()

    # chain = prompt | llm | parser
    # # return LLMChain(llm=llm, prompt=prompt)
    # return chain

# ----------------------------------------
# Resume Parsing Logic
# ----------------------------------------
# def parse_resume_with_llm(chain, text: str) -> dict:
#     """
#     Parse resume text via LLMChain and return the parsed JSON as a dict.
#     """
    # try:
    #     result = chain.invoke({"resume_text": text})
    #     return result
    # except Exception as e:
    #     print(
    #         f"Error during LLM parsing: {e}. Check your API key, model name, and network.",
    #         file=sys.stderr,
    #     )
    #     sys.exit(1)
    # try:
    #     parsed = json.loads(response)
    # except json.JSONDecodeError:
    #     # In case LLM returns text and JSON, try to extract JSON substring
    #     start = response.find('{')
    #     end = response.rfind('}')
    #     if start != -1 and end != -1:
    #         parsed = json.loads(response[start:end+1])
    #     else:
    #         raise ValueError("Failed to parse JSON from LLM response")
    # return parsed


# ----------------------------------------
# Database Save Logic
# ----------------------------------------

def save_candidate_data(cursor, conn, json_payload):
    """
    Save the parsed resume data into the MySQL database.
    """
    candidate = json.loads(json_payload)
    print("parsed data into python dict", candidate, type(candidate))
    try:

        # Insert into candidate table
        candidate_id = insert_candidate_data(cursor, candidate)

        # Insert related tables
        insert_skills(cursor, candidate_id, candidate.get('skills', []))
        insert_education(cursor, candidate_id, candidate.get('education', []))
        insert_experience(cursor, candidate_id, candidate.get('experience', []))
        insert_projects(cursor, candidate_id, candidate.get('projects', []))

        # Commit all inserts
        conn.commit()
        print("All data inserted successfully.")

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()
    print(f"Inserted candidate: {candidate.get('name')} (ID: {cursor.lastrowid})")

# ----------------------------------------
# Main Execution
# ----------------------------------------
if __name__ == "__main__":
    try:
        import argparse

        parser = argparse.ArgumentParser(description="Resume Parser with LangChain + MySQL")
        parser.add_argument("file", help="Path to the PDF resume file")
        args = parser.parse_args()

        # Initialize DB
        conn, cursor = init_db_connection()
        # Set up LLM chain
        # chain = setup_llm_chain()

        # Extract and parse resume
        print("Extracting text from PDF...")
        resume_text = extract_text_from_pdf(args.file)
        print(resume_text)

        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=f"""
                    You are an expert resume parser. Extract the following details from this resume text:
                    - Full Name
                    - Email
                    - Phone Number
                    - Skills (list)
                    - Education (list)
                    - Work Experience (list of objects with title, company, start_date, end_date)
                    - Porjects(list of objects with title, description, github_link, start_date, end_date)

                    Return the output keys: name, email, phone, location, skills, education, experience, projects.
                    in just ''' '''
                    Resume Text:
                    {resume_text}
                    """,
            config={
                "response_mime_type": "application/json",
                # "response_schema": list[Recipe],
            },
        )
        # print(response.text)
        parsed_json_data = response.text
        print("Parsing resume with LLM...")
        print("parsed data", parsed_json_data, type(parsed_json_data))
        # print("parsed data into python dict", json.loads(parsed_json_data), type(parsed_json_data))
        # parsed_data = parse_resume_with_llm(chain, resume_text)

        print("Saving data to MySQL...")
        # parsed_json_data = '''
        # {
        # "name": "RUSHIKESH FALAK",
        # "email": "falakrushikesh83@gmail.com",
        # "phone": "+918200934605",
        # "skills": [
        #     "Python",
        #     "JavaScript",
        #     "TypeScript",
        #     "Django",
        #     "Flask",
        #     "ReactJS",
        #     "MySQL",
        #     "PostgreSQL",
        #     "HTML",
        #     "Git",
        #     "CSS",
        #     "MachineLearning"
        # ],
        # "education": [
        #     {
        #     "degree": "BTech in Computer Engineering",
        #     "institution": "SilverOakUniversity,Ahmedabad",
        #     "start_date": "Oct2020",
        #     "end_date": "May2024",
        #     "cgpa": "9.36"
        #     },
        #     {
        #     "degree": "Class XII",
        #     "institution": "VivekanandaHigherSecondarySchool",
        #     "start_date": "April2020",
        #     "end_date": null,
        #     "percentage": "85%"
        #     },
        #     {
        #     "degree": "Class X",
        #     "institution": "SaraswatiVidyaMandir,Ahmedabad",
        #     "start_date": "April2018",
        #     "end_date": null,
        #     "percentage": "81%"
        #     }
        # ],
        # "experience": [
        #     {
        #     "title": "Software Developer Intern",
        #     "company": "eSparkBizTechnologiesPvtLtd.",
        #     "start_date": "Jan2024",
        #     "end_date": "Aug2024"
        #     }
        # ]
        # }
        # '''
       
        save_candidate_data(cursor, conn, parsed_json_data)

        # Clean up

        cursor.close()
        conn.close()
        print("Done.")

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        
    
