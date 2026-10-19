import os
from dotenv import load_dotenv

# BASE DIRECTORY → backend/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load .env variables
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

# MongoDB credentials (loaded from .env)
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")

if not MONGO_URI:
    raise Exception("❌ MONGO_URI missing in .env")
if not MONGO_DB_NAME:
    raise Exception("❌ MONGO_DB_NAME missing in .env")

# TEMP STORAGE PATH → backend/temp/
TEMP_DIR = os.path.join(BASE_DIR, "temp")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Subfolders inside temp/
RESUME_UPLOAD_DIR = os.path.join(TEMP_DIR, "resumes")
JD_UPLOAD_DIR = os.path.join(TEMP_DIR, "jds")
PROCESSED_DIR = os.path.join(TEMP_DIR, "processed")
CSV_EXPORT_DIR = os.path.join(TEMP_DIR, "csv_reports")

# Model + VectorDB inside backend/
MODEL_DIR = os.path.join(BASE_DIR, "models")
VECTOR_DB_DIR = os.path.join(BASE_DIR, "vector_db")

# Ensure folders exist
for folder in [
    TEMP_DIR,
    RESUME_UPLOAD_DIR,
    JD_UPLOAD_DIR,
    PROCESSED_DIR,
    CSV_EXPORT_DIR,
    MODEL_DIR,
    VECTOR_DB_DIR
]:
    os.makedirs(folder, exist_ok=True)


# -------------------------
# ❌ JWT Authentication REMOVED
# -------------------------


# Email configs (if required)
EMAIL_SENDER = "your-email@example.com"
EMAIL_PASSWORD = "your-app-password"


# App metadata
APP_NAME = "OptiRAG Backend"
VERSION = "1.0.0"
