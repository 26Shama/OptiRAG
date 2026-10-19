from fastapi import APIRouter
# ❌ REMOVED: from ..core.deps import require_auth
from ..services.optirag_service import trigger_finetune

router = APIRouter(prefix="/train", tags=["Continuous Learning"])

@router.post("/fine-tune-session")
async def fine_tune_session(session_id: str):
    result = trigger_finetune(session_id)
    return {"status": "Fine tuning started", "details": result}
