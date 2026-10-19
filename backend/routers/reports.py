from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
# ❌ REMOVED: from ..core.deps import require_auth
from ..services.optirag_service import generate_csv, send_candidate_emails

router = APIRouter(prefix="/reports", tags=["Reports"])

csv_map = {}

@router.get("/download-csv/{session_id}")
async def download_csv(session_id: str):
    if session_id not in csv_map:
        csv_path = generate_csv(session_id)
        csv_map[session_id] = csv_path

    return FileResponse(csv_map[session_id], media_type="text/csv", filename="optirag_report.csv")


@router.post("/send-email/{session_id}")
async def send_email(session_id: str):
    if session_id not in csv_map:
        raise HTTPException(status_code=404, detail="CSV not generated yet")

    status = send_candidate_emails(session_id, csv_map[session_id])
    return {"message": "Emails sent successfully", "status": status}
