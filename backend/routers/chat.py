from fastapi import APIRouter
from pydantic import BaseModel
from ..services.chatbot_service import process_chat_query

router = APIRouter()


class ChatRequest(BaseModel):
    question: str


@router.post("/query")
def chat_query(payload: ChatRequest):
    return {
        "answer": process_chat_query(payload.question)
    }
