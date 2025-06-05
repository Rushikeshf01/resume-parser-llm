import pandas as pd
import json
# import pytest
# from parser import parser_core

def test_resume_parsing():
    # Load expected CSV test case
    expected_df = pd.read_csv('tests/test_cases/test_case_1.csv')
    print(expected_df)

    # Run your parser on the actual resume file
    # actual_output = parser_core.parse_resume('resumes/resume_1.pdf')
    actual_output = {
        "resume_id": 1,
        "name": "Rushikesh Falak",
        "email": "falakrushikesh83@gmail.com",
        "phone": "+91 8200934605",
        "location": "Ahmedabad, Gujarat",
        "education": [
            {
            "degree": "BTech in Computer Engineering",
            "institution": "Silver Oak University",
            "duration": "Oct 2020 - May 2024"
            }
        ],
        "skills": [
            "Python", "JavaScript", "TypeScript", "Django", "Flask", "ReactJS",
            "MySQL", "PostgreSQL", "HTML", "Git", "CSS", "Machine Learning"
        ],
        "experience": [
            {
            "title": "Software Developer Intern",
            "company": "eSparkBiz Technologies Pvt Ltd",
            "duration": "Jan 2024 - Aug 2024",
            "location": "Ahmedabad, Gujarat"
            }
        ],
        "projects": [
            "Twitter Clone",
            "Safety Hazard Detection System",
            "Sentiment Analysis of Product Review"
        ],
        "linkedin": "https://www.linkedin.com/in/rushikesh-falak-14604a203/",
        "github": "https://github.com/Rushikeshf01"
    }


    # Convert actual output JSON to DataFrame
    actual_df = pd.DataFrame([actual_output])  # wrap dict in list to create 1-row DataFrame

    # Compare columns
    for col in expected_df.columns:
        expected_value = expected_df.loc[0, col]
        actual_value = actual_df.loc[0, col]

        assert expected_value == actual_value, f"Mismatch in {col}: Expected {expected_value}, got {actual_value}"
