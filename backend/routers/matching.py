from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from ..utils.file_handler import save_temp_file
from ..pipeline.hr_pipeline import optirag_hr_pipeline
from ..core.session_store import active_sessions  #
# ❌ REMOVED: from ..core.deps import require_auth

from ..pipeline.hr_pipeline import optirag_hr_pipeline

router = APIRouter(prefix="/matching", tags=["Matching & Ranking"])

# Temporary storage for rankings → session_id → list of results
session_results = {}


@router.post("/run")
async def best_matches(
    session_id: str = Form(...),   # Form data
    top_n: int = Form(5)           # Default top_n = 5 if not sent
):
    """
    Run screening: use session_id to fetch JD + resumes uploaded in this session,
    then perform matching.
    """
    # Check if session exists
    if session_id not in active_sessions:
        return {"status": "error", "message": "Invalid session_id"}

    session_data = active_sessions[session_id]
    jd_input = session_data.get("jd")
    resume_inputs = session_data.get("resumes", [])
    category = session_data.get("Category", "IT")

    if not jd_input or not resume_inputs:
        return {"status": "error", "message": "JD or resumes not uploaded for this session"}

    # Run your existing OptiRAG pipeline
    results = optirag_hr_pipeline(
        category=category,
        jd_input=jd_input,
        resume_inputs=resume_inputs,
        top_n=top_n
    )

    # Store results for later reference
    session_results[session_id] = results

    return {
        "status": "success",
        "session_id": session_id,
        "results": results
    }

@router.get("/explanation/{candidate_id}")
async def explanation(candidate_id: str, session_id: str = Form(...)):
    """
    Returns WHY the candidate was selected (skills, similarity, experience, etc.)
    """

    if session_id not in session_results:
        raise HTTPException(status_code=400, detail="No ranking has been done for this session")

    candidates = session_results[session_id]

    for candidate in candidates:
        if candidate.get("candidate_id") == candidate_id:
            return {
                "candidate_id": candidate_id,
                "explanation": candidate.get("explanation", "No explanation available")
            }

    raise HTTPException(status_code=404, detail="Candidate not found in the session results")


