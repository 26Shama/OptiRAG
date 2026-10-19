# fastapi_hr_emailer.py
import os
import csv
import io
import json
import ssl
import time
import traceback
from datetime import datetime
from getpass import getpass
from typing import List, Dict

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from email.message import EmailMessage
import smtplib

# ---------- CONFIG (use hr_outputs folder) ----------
BASE_OUTPUT = "hr_outputs"
HR_CSV_PATH = os.path.join(BASE_OUTPUT, "HR_Resume_Ranking.csv")
EMAIL_MAPPING_CSV_PATH = os.path.join(BASE_OUTPUT, "resume_email_mapping.csv")
HR_APPROVAL_JSON_PATH = os.path.join(BASE_OUTPUT, "selected_candidates.json")
LOG_CSV = "email_send_log.csv"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
PAUSE_BETWEEN_EMAILS_SEC = 2

# ---------- TEMPLATES ----------
TEMPLATES = {
    "shortlisted": {
        "subject": "Congratulations! Your Resume has been Shortlisted",
        "message": """Dear {name},

We are pleased to inform you that your application for the {position} role has been shortlisted!

Our team was impressed with your qualifications and experience. We are currently in the process of scheduling the next rounds and will update you with further details shortly.

Please keep an eye on your email for updates regarding interview schedules and next steps.

Thank you for your patience.

Best regards,
{sender}"""
    },
    "not_shortlisted": {
        "subject": "Update on Your Application for {position}",
        "message": """Dear {name},

Thank you for your interest in the {position} position and for taking the time to apply.

After careful review, we regret to inform you that your resume has not been shortlisted for the next stage of the selection process.

Primary Reason:
{rejection_reason}

We encourage you to apply for future openings that may be a better match for your profile. We wish you the best in your job search.

Best regards,
{sender}"""
    }
}

# ---------- FastAPI app ----------
router = APIRouter()

# ---------------- Utilities ----------------
def load_hr_approval(approval_json_path=HR_APPROVAL_JSON_PATH) -> set:
    try:
        with open(approval_json_path, "r", encoding="utf-8") as f:
            hr_approvals = json.load(f)
        shortlisted_ids = set()
        for candidate in hr_approvals:
            # support both Resume_ID and ResumeID keys
            shortlisted_ids.add(candidate.get("Resume_ID") or candidate.get("ResumeID"))
        return {rid for rid in shortlisted_ids if rid}
    except FileNotFoundError:
        return set()
    except Exception:
        traceback.print_exc()
        return set()

def load_email_mapping(mapping_csv_path=EMAIL_MAPPING_CSV_PATH) -> Dict[str, Dict[str,str]]:
    email_mapping = {}
    try:
        with open(mapping_csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                resume_id = (row.get("ResumeID") or "").strip()
                email = (row.get("Email") or "").strip()
                name = (row.get("Name") or "").strip()
                if resume_id and email and "@" in email:
                    email_mapping[resume_id] = {"email": email, "name": name}
    except FileNotFoundError:
        pass
    except Exception:
        traceback.print_exc()
    return email_mapping

def create_resume_mapping(hr_csv_path=HR_CSV_PATH, mapping_csv_path=EMAIL_MAPPING_CSV_PATH) -> Dict[str,str]:
    """
    Map HR file Resume_ID values to mapping CSV ResumeID in order.
    This follows your previous logic of pairing by index.
    """
    resume_mapping = {}
    try:
        hr_resumes = []
        with open(hr_csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # accept Resume_ID or ResumeID
                hr_id = row.get("Resume_ID") or row.get("ResumeID") or row.get("file_name") or ""
                if hr_id:
                    hr_resumes.append(hr_id.strip())

        email_resumes = []
        with open(mapping_csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                email_id = row.get("ResumeID") or row.get("Resume_ID") or ""
                if email_id:
                    email_resumes.append(email_id.strip())

        for i, hr_resume in enumerate(hr_resumes):
            if i < len(email_resumes):
                resume_mapping[hr_resume] = email_resumes[i]

    except FileNotFoundError:
        pass
    except Exception:
        traceback.print_exc()
    return resume_mapping

def process_candidates_list(hr_csv_path=HR_CSV_PATH, mapping_csv_path=EMAIL_MAPPING_CSV_PATH, approval_json=HR_APPROVAL_JSON_PATH) -> List[Dict]:
    """
    Produce structured candidate list from HR CSV + mapping CSV + approvals JSON.
    Each candidate: {name, email, position, status, rejection_reason}
    """
    shortlisted_ids = load_hr_approval(approval_json)
    email_mapping = load_email_mapping(mapping_csv_path)
    resume_mapping = create_resume_mapping(hr_csv_path, mapping_csv_path)

    candidates = []
    try:
        with open(hr_csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                hr_resume_id = (row.get("Resume_ID") or row.get("ResumeID") or row.get("file_name") or "").strip()
                if not hr_resume_id:
                    continue
                email_resume_id = resume_mapping.get(hr_resume_id)
                if not email_resume_id:
                    continue
                candidate_info = email_mapping.get(email_resume_id)
                if not candidate_info:
                    continue

                explanation = (row.get("Explanation") or "").strip()

                if explanation.lower().startswith("Selected"):
                    status = "shortlisted"
                    rejection_reason = ""
                else:
                    status = "not_shortlisted"
                    rejection_reason = explanation or "Other candidates demonstrated stronger alignment"

                candidate = {
                    "name": candidate_info["name"],
                    "email": candidate_info["email"],
                    "status": status,
                    "rejection_reason": rejection_reason,
                    "explanation": explanation
                }

                candidates.append(candidate)
    except FileNotFoundError:
        pass
    except Exception:
        traceback.print_exc()
    return candidates

def log_send(email, name, status, subject, result, error=""):
    header_needed = not os.path.exists(LOG_CSV)
    with open(LOG_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if header_needed:
            writer.writerow(["timestamp", "email", "name", "status", "subject", "result", "error"])
        writer.writerow([datetime.now().isoformat(), email, name, status, subject, result, error])

# ---------------- API Endpoints ----------------

@router.get("/candidates", response_class=JSONResponse)
def get_candidates():
    """
    Returns JSON list of candidates assembled from HR CSV + mapping + approvals.
    """
    candidates = process_candidates_list()
    return {"count": len(candidates), "candidates": candidates}

@router.get("/download-candidates-csv")
def download_candidates_csv():
    """
    Returns a CSV (attachment) with screening results.
    Columns:
    File Name, Name, Email, Score, Rank, Explanation
    """
    candidates = process_candidates_list()

    buffer = io.StringIO()
    writer = csv.writer(buffer)

    # ✅ CSV HEADER (this controls column names)
    writer.writerow([
        "File Name",
        "Name",
        "Email",
        "Score",
        "Rank",
        "Explanation"
    ])

    # ✅ CSV ROWS
    for c in candidates:
        writer.writerow([
            c.get("file_name", ""),
            c.get("Name", ""),
            c.get("Email", ""),
            c.get("score", ""),
            c.get("rank", ""),
            c.get("explanation", "")
        ])

    buffer.seek(0)
    filename = "screened_candidates.csv"

    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@router.post("/send-emails")
def send_emails_endpoint(
    file: UploadFile = File(...),
    sender_email: str = Form(...),
    sender_name: str = Form("HR Team"),
    app_password: str = Form(...),
    pause_seconds: float = Form(PAUSE_BETWEEN_EMAILS_SEC),
    position: str = Form(...)
):
    """
    Accepts a CSV file uploaded by HR containing columns: name,email,status
    Sends emails synchronously and returns a summary JSON.
    """
    # Read uploaded CSV into memory
    try:
        content = file.file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))
        rows = [r for r in reader]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded CSV: {e}")

    if not rows:
        raise HTTPException(status_code=400, detail="Uploaded CSV is empty")

    # Validate rows
    valid_rows = []
    for r in rows:
        name = (r.get("name") or r.get("Name") or "").strip()
        email = (r.get("email") or r.get("Email") or "").strip()
        explanation = (r.get("Explanation") or "").lstrip("\ufeff").strip()

        if explanation.lower().startswith("Selected"):
            status = "shortlisted"
        else:
            status = "not_shortlisted"

        if not name or not email or "@" not in email:
            continue
        valid_rows.append({
            "name": name,
            "email": email,
            "status": status,
            "explanation": explanation
        })


    if not valid_rows:
        raise HTTPException(status_code=400, detail="No valid rows with name and email found in uploaded CSV")

    # Connect to SMTP
    context = ssl.create_default_context()
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls(context=context)
        server.login(sender_email, app_password)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect/login to SMTP server: {e}")

    sent = 0
    failed = 0
    details = []

    for i, candidate in enumerate(valid_rows, 1):
        try:
            template = TEMPLATES.get(candidate["status"], TEMPLATES["not_shortlisted"])
            subject = template["subject"].format(name=candidate["name"], position=position)
            message = template["message"].format(
                name=candidate["name"],
                position=position,
                rejection_reason="",
                sender=sender_name
            )
            # if not_shortlisted we include a reason in message (reuse logic)
            if candidate["status"] == "not_shortlisted":
                message = template["message"].format(
                    name=candidate["name"],
                    position=position,
                    rejection_reason=candidate.get("explanation", ""),
                    sender=sender_name
                )


            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = f"{sender_name} <{sender_email}>"
            msg["To"] = candidate["email"]
            msg.set_content(message)

            server.send_message(msg)
            sent += 1
            log_send(candidate["email"], candidate["name"], candidate["status"], subject, "SENT")
            details.append({"email": candidate["email"], "result": "SENT"})
        except Exception as e:
            failed += 1
            err = str(e)
            log_send(candidate["email"], candidate["name"], candidate["status"], subject, "FAILED", err)
            details.append({"email": candidate["email"], "result": "FAILED", "error": err})
        time.sleep(pause_seconds)

    server.quit()
    return {"sent": sent, "failed": failed, "details": details}

# ---------- simple health check ----------
@router.get("/health")
def health():
    return {"status": "ok", "hr_csv_exists": os.path.exists(HR_CSV_PATH), "mapping_csv_exists": os.path.exists(EMAIL_MAPPING_CSV_PATH)}
