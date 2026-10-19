from .context_builder import build_context
from ..utils.gemini_client import generate_answer


def process_chat_query(question: str) -> str:
    """
    Chatbot orchestrator:
    - Builds context
    - Uses Gemini for response generation
    """
    context_data = build_context(question)
    context_text = context_data.get("content", "")

    return generate_answer(
        context=context_text,
        question=question
    )
