import re
import streamlit as st
import pandas as pd

# ---------------------------------------------------------
# EMAIL VALIDATION
# ---------------------------------------------------------
def is_valid_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))


# ---------------------------------------------------------
# PASSWORD VALIDATION
# ---------------------------------------------------------
def is_strong_password(password: str) -> bool:
    """
    Password must contain:
    - At least 6 characters
    - One digit
    - One letter
    """
    if len(password) < 6:
        return False
    if not re.search(r"[A-Za-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    return True


# ---------------------------------------------------------
# FILE TYPE VALIDATION
# ---------------------------------------------------------
def validate_file_type(file, allowed_extensions):
    """Validate uploaded file extension."""
    if file is None:
        return False
    
    filename = file.name.lower()
    return any(filename.endswith(ext) for ext in allowed_extensions)


# ---------------------------------------------------------
# CSV COLUMN VALIDATION
# ---------------------------------------------------------
def validate_csv_columns(df: pd.DataFrame, required_columns: list):
    """Check if required columns exist in uploaded CSV."""
    missing = [col for col in required_columns if col not in df.columns]
    return missing  # return list of missing cols (empty if OK)


# ---------------------------------------------------------
# JD FILE VALIDATION
# ---------------------------------------------------------
def validate_jd_file(file):
    """Allow PDF, DOCX, TXT for Job Description."""
    return validate_file_type(file, ["pdf", "docx", "txt"])


# ---------------------------------------------------------
# RESUME FILE VALIDATION
# ---------------------------------------------------------
def validate_resume_file(file):
    """Allow only PDF or DOCX for resumes."""
    return validate_file_type(file, ["pdf", "docx"])


# ---------------------------------------------------------
# SAFE TEXT VALIDATION (No empty input)
# ---------------------------------------------------------
def is_non_empty(text: str):
    return text is not None and text.strip() != ""


# ---------------------------------------------------------
# SHOW VALIDATION ERRORS IN STREAMLIT
# ---------------------------------------------------------
def show_error(message: str):
    st.error(message)
