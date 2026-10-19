def build_context(question: str) -> dict:
    q = question.lower()

    if any(keyword in q for keyword in [
        "optirag",
        "screening",
        "ranking",
        "resume",
        "candidate",
        "shortlist",
        "faiss",
        "matching",
        "semantic"
    ]):
        return {
            "type": "optirag",
            "content": (
                "OptiRAG is an AI-driven resume screening system that uses "
                "Retrieval-Augmented Generation, sentence embeddings, and "
                "FAISS similarity search to contextually match resumes with "
                "job descriptions, ensuring fair and explainable hiring."
            )
        }

    return {
        "type": "general",
        "content": ""
    }
