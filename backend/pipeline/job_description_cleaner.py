# JobDescriptionCleaner.py

import os
import json
import re
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup
from fastapi import HTTPException  # Added for FastAPI error handling

# 5️⃣ JD Cleaning
class JobDescriptionCleaner:

    @staticmethod
    def clean_text(text):
        if pd.isna(text):
            return ""

        text = str(text)

        # 1️⃣ Remove HTML tags
        text = BeautifulSoup(text, "html.parser").get_text(separator=" ")

        # 2️⃣ Remove non ASCII
        text = text.encode("ascii", "ignore").decode()

        # 3️⃣ Normalize whitespace
        text = re.sub(r"\s+", " ", text)

        # 4️⃣ Remove spacing around punctuation
        text = re.sub(r"\s*([.,;:!?])\s*", r"\1 ", text)

        return text.strip()

    @staticmethod
    def process_file(input_path, output_json_path):
        ext = os.path.splitext(input_path)[1].lower()

        try:
            # Load Data based on extension
            if ext == ".csv":
                try:
                    df = pd.read_csv(input_path, encoding="utf-8")
                except UnicodeDecodeError:
                    df = pd.read_csv(input_path, encoding="latin-1")

            elif ext == ".json":
                try:
                    with open(input_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    df = pd.DataFrame(data)

                except json.JSONDecodeError as e:
                    print("⚠ JSONDecodeError:", e)
                    raise HTTPException(status_code=500, detail="Invalid JSON format")

            else:
                raise HTTPException(status_code=400, detail="Unsupported file type. Use CSV or JSON.")

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load file: {str(e)}")

        # Remove unnecessary unnamed columns
        df = df.drop(columns=[col for col in df.columns if "Unnamed" in col], errors="ignore")

        # Assign JobID if missing
        if "JobID" not in df.columns:
            df["JobID"] = range(1, len(df) + 1)

        # Clean JobTitle
        for col in ["Job Title", "JobTitle", "jobtitle", "job title", "job_title", "Job_Title"]:
            if col in df.columns:
                df["JobTitle"] = df[col].apply(JobDescriptionCleaner.clean_text)
                break
        else:
            print("⚠ Warning: JobTitle column not found.")

        # Clean JobDescription
        for col in ["Job Description", "JobDescription", "Job_Description", "jobdescription",
                    "job description", "job_description"]:
            if col in df.columns:
                df["JobDescription"] = df[col].apply(JobDescriptionCleaner.clean_text)
                break
        else:
            print("⚠ Warning: JobDescription column not found.")

        # Keep only needed columns
        essential_cols = [col for col in ["JobID", "JobTitle", "Category", "JobDescription"]
                          if col in df.columns]
        df = df[essential_cols]

        # Save and Return
        records = df.to_dict(orient="records")

        try:
            with open(output_json_path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=4, ensure_ascii=False)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving output: {str(e)}")

        return records
