import pandas as pd

# Load the .xls file
file_path = "Ekesa CV Details.xls"  # Change path as needed
df = pd.read_excel(file_path, engine='xlrd')

# Define test case fields (as per your specification)
required_fields = [
    "Candidate Name", "Resume Title", "Contact No.", "Alternate Contact Number", "Github Link",
    "LinkedIn Link", "Email", "Residential Address", "Work Exp", "Current Salary",
    "Expectations of Salary", "Official Notice Period", "Serving notice period",
    "On Bench(People who are not in any project)", "Current Location", "Preferred Location",
    "Current Industry", "Domian experties", "Home Town/Native", "Department", "Role",
    "Current Employer", "Previous Employer", "Marital status", "Physically Challenged",
    "Work Authorization", "Designation", "U.G. Course", "P. G. Course", "Post P. G. Course",
    "cgpa", "percentage", "Date of Birth", "Age", "Postal Address", "Last Active",
    "Brief Summary", "Core Skills", "Certifications", "Award", "Lanuages Known", "Gender",
    "Comment 1", "Comment 2", "Comment 3", "Comment 4", "Comment 5"
]

# Strip whitespace from column headers
df.columns = df.columns.str.strip()

# Track results
results = []

# Loop through each row to validate required fields
for index, row in df.iterrows():
    missing = [field for field in required_fields if field not in row or pd.isna(row.get(field))]
    if missing:
        results.append((index + 2, "❌ Failed", missing))  # Excel rows are 1-indexed (+ header)
    else:
        results.append((index + 2, "✅ Passed", []))

# Print results
for row_num, status, missing_fields in results:
    print(f"Row {row_num}: {status}")
    if missing_fields:
        print(f"  Missing Fields: {', '.join(missing_fields)}")



#To operate this install the following Library
#pip install pandas xlrd


#To run the following use the following
#python validate_data.py
