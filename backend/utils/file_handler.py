# backend/utils/file_handler.py
import os, uuid, shutil
from ..core.config import RESUME_UPLOAD_DIR, JD_UPLOAD_DIR

def _ensure_folder(path: str):
    os.makedirs(path, exist_ok=True)

def save_temp_file(upload_file, folder_name: str) -> str:
    """
    upload_file: fastapi.UploadFile
    folder_name: either "resumes" or "jds"
    returns saved file path
    """
    if folder_name == "resumes":
        base = RESUME_UPLOAD_DIR
    elif folder_name == "jds":
        base = JD_UPLOAD_DIR
    else:
        base = os.path.join(os.path.dirname(RESUME_UPLOAD_DIR), folder_name)

    _ensure_folder(base)
    unique_name = f"{uuid.uuid4().hex}_{upload_file.filename}"
    dest_path = os.path.join(base, unique_name)

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return dest_path
