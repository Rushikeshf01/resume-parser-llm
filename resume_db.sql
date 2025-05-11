CREATE DATABASE resume_parser_db;
USE resume_parser_db;

CREATE TABLE candidates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255) UNIQUE,
    phone_number VARCHAR(50),
    linkedin_url VARCHAR(255),
    github_url VARCHAR(255),
    address TEXT,
    parsed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resume_filename VARCHAR(255),
    raw_text LONGTEXT,
    llm_enhanced_summary TEXT -- Optional: For LLM-generated summaries
);

CREATE TABLE education (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id INT,
    institution VARCHAR(255),
    degree VARCHAR(255),
    field_of_study VARCHAR(255),
    start_date DATE,
    end_date DATE,
    gpa DECIMAL(3,2),
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
);

CREATE TABLE experience (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id INT,
    company_name VARCHAR(255),
    job_title VARCHAR(255),
    start_date DATE,
    end_date DATE,
    description TEXT,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
);

CREATE TABLE skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id INT,
    skill_name VARCHAR(255),
    -- Optional: skill_level (e.g., beginner, intermediate, expert)
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
);

CREATE TABLE projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id INT,
    project_name VARCHAR(255),
    description TEXT,
    url VARCHAR(255),
    technologies_used TEXT, -- Comma-separated or a separate linked table
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
);

-- You can add more tables as needed, e.g., certifications, awards, etc.