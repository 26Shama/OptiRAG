# backend/services/optirag_service.py
import os
import csv
from ..core.config import CSV_EXPORT_DIR

from ..pipeline.text_extraction import extract_text
from ..pipeline.blind_screening import blind_screen
from ..pipeline.resume_parser import parse_resume
from ..pipeline.jd_extractor import extract_jd
from ..pipeline.embedding_generator import EmbeddingGenerator
from ..pipeline.scoring import rank_resumes
from ..pipeline.model_init import initialize_model, DEVICE
from ..pipeline.mapping_generator import generate_resume_mapping_csv


model = initialize_model()
embedding_generator = EmbeddingGenerator(config={"DEVICE": DEVICE})


def run_optirag_pipeline(resume_paths: list, jd_path: str, top_n: int = 5):
    jd_text = extract_jd(jd_path)
    jd_embedding = embedding_generator.generate_embeddings(model, [jd_text])[0]

    candidates = []
    resume_records = []

    for resume in resume_paths:
        original_text = extract_text(resume)
        text = blind_screen(original_text)
        parsed = parse_resume(text)

        emb = embedding_generator.generate_embeddings(model, [text])[0]

        resume_id = parsed.get("ResumeID") or os.path.basename(resume)

        resume_records.append({
            "ResumeID": resume_id,
            "OriginalText": original_text,
            "Category": parsed.get("Category", "Unknown")
        })

        candidates.append({
            "resume_path": resume,
            "parsed_info": parsed,
            "embedding": emb
        })

    # ✅ Create resume → email mapping CSV
    generate_resume_mapping_csv(resume_records)

    results = rank_resumes(jd_embedding, candidates)
    return results[:top_n]


# -------------------------------
# STEP 12 → Generate CSV Report
# -------------------------------
def generate_csv(session_id: str):
    from routers.matching import session_results

    results = session_results.get(session_id)

    if not results:
        raise Exception("No ranking data for this session")

    csv_path = os.path.join(CSV_EXPORT_DIR, f"{session_id}.csv")

    rows = [["Candidate_ID", "Name", "Score", "Status", "Explanation"]]

    for c in results:
        rows.append([
            c.get("candidate_id"),
            c.get("name", "N/A"),
            c.get("score"),
            c.get("status"),
            c.get("explanation", "N/A")
        ])

    with open(csv_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.s(rows)

    return csv_path


# -------------------------------
# STEP 12 → Send Emails
# -------------------------------
def send_candidate_emails(session_id: str, csv_path: str):
    return {"session_id": session_id, "emails_sent": True}


# -------------------------------
# STEP 13 → Continuous Learning
# -------------------------------
def trigger_finetune(session_id: str):
    return {"session_id": session_id, "status": "Fine-tuning started"}
