import os
import shutil
from fastapi import UploadFile
from typing import Union, List
import tempfile
import traceback
import numpy as np
import pandas as pd
import csv
import json

from ..pipeline.dynamic_pipeline import DynamicEmbeddingPipeline
from ..pipeline.scoring import (
    validate_inputs,
    faiss_retrieve,
    compute_skill_overlap,
    compute_exp_match,
    compute_hybrid_score,
    deepseek_highlight,
    template_rejection,
    deepseek_explanation,
    llm_generate_rejection,
    integrate_with_step8,
    deepseek_profile_summary_llm,
    parse_jd_with_step8
)

def optirag_hr_pipeline(category: str,
    jd_input: Union[str, UploadFile],
    resume_inputs: List[Union[str, UploadFile]],
    top_n: int = 10
    ):
    try:
        step8 = DynamicEmbeddingPipeline()

        # ---------- Helper: Save UploadFile safely ----------
        def save_uploadfile_tmp(upload_file):
            suffix = os.path.splitext(upload_file.filename)[-1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                upload_file.file.seek(0)      # ✅ VERY IMPORTANT
                shutil.copyfileobj(upload_file.file, tmp)
                upload_file.file.seek(0)      # ✅ reset again
                return tmp.name

        # ---------- Step 1: JD Processing ----------
        if not isinstance(jd_input, str) or not os.path.exists(jd_input):
            raise ValueError("Invalid JD file path")

        print("✅ JD file path:", jd_input)

        jd_output = step8.process_jd_file(jd_input)

        jd_texts = jd_output.get("jd_texts", [])
        processed_jds = jd_output.get("processed_jds", [])

        if not jd_texts:
            raise ValueError("Failed to process JD")

        # ---------- Step 2: Resume Processing ----------
        processed_resumes = []
        resume_texts = []

        for r in resume_inputs:
            if isinstance(r, UploadFile):
                resume_path = save_uploadfile_tmp(r)
                parsed_list = step8.process_resume_file(resume_path)
            else:
                parsed_list = step8.process_resume_file(r)

            for pr in parsed_list:
                txt = pr.get("RedactedText", "")
                if len(txt.strip()) > 50:
                    processed_resumes.append(pr)
                    resume_texts.append(txt)

        if not processed_resumes:
            raise ValueError("No valid resumes processed")

        # Step 3 Embeddings
        resume_embeddings = step8.generate_embeddings(resume_texts)
        jd_embeddings = step8.generate_embeddings(jd_texts)
        jd_emb = jd_embeddings[0:1]

        step8_out = {
            "processed_resumes_data": processed_resumes,
            "resume_embeddings": resume_embeddings,
            "processed_jds": processed_jds,
            "jd_texts": jd_texts,
            "jd_embeddings": jd_embeddings
        }

        resume_list = integrate_with_step8(step8_out, category)
        jd_data = parse_jd_with_step8(step8_out)

        # Step 4 FAISS
        _, top_indices = faiss_retrieve(jd_emb, resume_embeddings, min(top_n, len(resume_list)))
        top_set = set(top_indices)

        # Step 5 Scoring + Explanation
        current_script_path = os.path.abspath(__file__)          # This script's path
        backend_dir = os.path.dirname(os.path.dirname(current_script_path))  # Go up to 'backend'
        mapping_file = os.path.join(backend_dir, "hr_outputs", "resume_email_mapping.csv")

        resume_mapping = {}
        if os.path.exists(mapping_file):
            with open(mapping_file, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    resume_mapping[row["ResumeID"]] = {
                        "Name": row["Name"],
                        "Email": row["Email"]
                    }

        results = []
        for idx, r in enumerate(resume_list):
            parsed = r["parsed"]
            # Debug: Check what's in parsed data
            print(f"\n🔍 Candidate {idx} parsed data:")
            for key, value in parsed.items():
                print(f"  {key}: {value}")
            score = compute_hybrid_score(
                jd_emb[0],
                resume_embeddings[idx],
                compute_skill_overlap(jd_data["skills"], parsed["skills"]),
                compute_exp_match(jd_data["experience"], parsed["experience"])
            )
            
            # Get the explanation text properly
            if idx in top_set:
                # Get the LLM response
                llm_response = deepseek_profile_summary_llm(
                    parsed_resume=parsed,
                    jd_data=jd_data
                )
                
                # Extract just the summary text from the JSON
                explanation_text = str(llm_response)  # Default to string
                try:
                    # Try to parse as JSON
                    if isinstance(llm_response, str):
                        response_data = json.loads(llm_response)
                    else:
                        response_data = llm_response
                    
                    # Extract summary from the structure
                    if "results" in response_data and response_data["results"]:
                        explanation_text = response_data["results"][0]["summary"]
                    elif "summary" in response_data:
                        explanation_text = response_data["summary"]
                except:
                    # If parsing fails, keep as string
                    pass
                explanation_text=f"Selected: {explanation_text}"
                explanation_text = f"Selected: {explanation_text}"
            else:
                # For rejected candidates, use rejection reason
                explanation_text = llm_generate_rejection(
                    jd_data["skills"],
                    parsed["skills"],
                    jd_data["experience"],
                    parsed["experience"]
                )
            
            result = {
                "file_name": os.path.basename(r["id"]),
                "score": round(score, 4),
                "rank": 0,
                "explanation": explanation_text
            }

            results.append(result)

        # Rank sorted
        results = sorted(results, key=lambda x: x["score"], reverse=True)
        for i, r in enumerate(results):
            r["rank"] = i + 1

        for r in results:
            resume_id = r["file_name"].split(".")[0]  # strip extension to get ResumeID
            if resume_id in resume_mapping:
                r["Name"] = resume_mapping[resume_id]["Name"]
                r["Email"] = resume_mapping[resume_id]["Email"]
            else:
                r["Name"] = ""
                r["Email"] = ""

        return {"results": results}

    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}
