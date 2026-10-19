from fastapi import APIRouter, UploadFile, File, HTTPException
import os, uuid, shutil
from ..core.config import TEMP_DIR
from ..core.session_store import active_sessions  # import the global dict

# ❌ REMOVED: from ..core.deps import require_auth

resumes_router = APIRouter(prefix="/resumes", tags=["Resumes"])
jd_router = APIRouter(prefix="/jd", tags=["Job Description"])


from fastapi import APIRouter, UploadFile, File, Form
import os
import shutil

CSV_MAPPING_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "hr_outputs",
    "resume_email_mapping.csv"
)

@resumes_router.post("/upload")
async def upload_resumes(session_id: str = Form(...),                  # Accept session_id from client
    files: list[UploadFile] = File(...)           # Accept multiple resumes
):
    # Make sure the session exists
    if session_id not in active_sessions:
        return {"status": "error", "message": "Invalid session_id"}

    session_dir = os.path.join(TEMP_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    resume_paths = []
    for file in files:
        dest = os.path.join(session_dir, file.filename)
        with open(dest, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        resume_paths.append(dest)

    # Update the existing session with resumes
    active_sessions[session_id]["resumes"] = resume_paths

    return {
        "status": "success",
        "message": "Resumes uploaded successfully",
        "resumes_uploaded": [os.path.basename(p) for p in resume_paths]
    }


@jd_router.post("/upload")
async def upload_jd(jd: UploadFile = File(...), JobTitle: str = "", Category: str = ""):
    # 🔥 RESET TEMP STORAGE ON NEW JD UPLOAD
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)

    os.makedirs(TEMP_DIR, exist_ok=True)
    active_sessions.clear()

    # 🔥 RESET EMAIL MAPPING CSV
    os.makedirs(os.path.dirname(CSV_MAPPING_PATH), exist_ok=True)
    if os.path.exists(CSV_MAPPING_PATH):
        open(CSV_MAPPING_PATH, "w").close()

    # ✅ CREATE NEW SESSION
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(TEMP_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    jd_path = os.path.join(session_dir, jd.filename)

    with open(jd_path, "wb") as buffer:
        shutil.copyfileobj(jd.file, buffer)

    # ✅ DEBUG: check file really saved
    print("✅ JD SAVED PATH:", jd_path)
    print("✅ JD FILE EXISTS:", os.path.exists(jd_path))
    print("✅ JD FILE SIZE:", os.path.getsize(jd_path))

    active_sessions[session_id] = {
        "resumes": [],
        "jd": jd_path,
        "JobTitle": JobTitle,
        "Category": Category
    }

    # ✅ DEBUG active session
    print("✅ ACTIVE SESSION STORED:", active_sessions[session_id])

    return {
        "status": "JD uploaded successfully",
        "session_id": session_id,
        "jd_path": jd_path,       # ✅ MUST return
        "file_size": os.path.getsize(jd_path),
        "JobTitle": JobTitle,
        "Category": Category
    }
