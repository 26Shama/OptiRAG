import os
import uuid
import json
import traceback
import pandas as pd
from typing import List, Dict, Any
import numpy as np

# App Initializations
from ..pipeline.model_init import load_finetuned_model, CONFIG
from ..pipeline.nlp_init import initialize_nlp  # optional if needed inside pipeline
from ..pipeline.mapping_generator import generate_resume_mapping_csv
# Import classes you created earlier
from ..pipeline.text_extraction import TextExtraction
from ..pipeline.blind_screening import BlindScreening
from ..pipeline.resume_parser import ResumeParser
from ..pipeline.jd_extractor import JDExtractor
from ..pipeline.job_description_cleaner import JobDescriptionCleaner
from ..pipeline.job_jd_parser import JobJDParser
from ..pipeline.embedding_generator import EmbeddingGenerator

# =====================================================================
# DYNAMIC EMBEDDING PIPELINE
# =====================================================================
class DynamicEmbeddingPipeline:
    def __init__(self, config=CONFIG):
        self.config = config
        self.model = load_finetuned_model()

        # Instantiate classes
        self.extractor = TextExtraction()
        self.blindscreen = BlindScreening()
        self.parser = ResumeParser()
        self.jd_extractor = JDExtractor()
        self.jd_cleaner = JobDescriptionCleaner()
        self.jd_parser = JobJDParser()
        self.embedder = EmbeddingGenerator(config=self.config, logger=None)

    # ---------------------------
    # Resume Processing
    # ---------------------------
    def process_resume_file(self, resume_input, resume_id: str = None, category: str = "Unknown") -> list:
      """
      Process resumes (single or multiple) in various formats: PDF, DOCX, TXT, CSV, JSON, or raw text.

      Args:
        resume_input: Can be
            - str: path to a single file (.pdf, .docx, .txt, .csv, .json) or raw text
            - dict: single resume as JSON
            - list: list of resumes (dicts or file paths)
        resume_id: optional ID for single resume
        category: optional category for single resume

      Returns:
        List of parsed resume dicts ready for embeddings
      """
      parsed_resumes = []
      original_mapping_data = []

      # Normalize input to list
      if isinstance(resume_input, (str, dict)):
        resume_list = [resume_input]
      elif isinstance(resume_input, list):
        resume_list = resume_input
      else:
        print(f"⚠️ Unsupported resume input type: {type(resume_input)}")
        return []

      for idx, item in enumerate(resume_list):
        try:
          # Determine raw text
            if isinstance(item, dict):
              # Resume from JSON
              raw_text = item.get("Text") \
                or item.get("ResumeText") \
                or item.get("content") \
                or item.get("Raw") \
                or ""
              current_resume_id = item.get("ResumeID", str(uuid.uuid4()))
              current_category = item.get("Category", category)
              file_name = item.get("FileName", f"resume_{idx+1}")
            elif isinstance(item, str) and os.path.isfile(item):
              # Resume from file
              file_name = os.path.basename(item)
              current_resume_id = resume_id if resume_id and len(resume_list) == 1 else f"RES_{idx+1}_{str(uuid.uuid4())[:8]}"
              current_category = category
              ext = file_name.lower().split('.')[-1]

              if ext == "pdf":
                raw_text = self.extractor.extract_pdf_text(item)
              elif ext == "docx":
                raw_text = self.extractor.extract_docx_text(item)
              elif ext == "txt":
                with open(item, "r", encoding="utf-8") as f:
                  raw_text = f.read()
              elif ext == "csv":
                df = pd.read_csv(item)
                if "Text" in df.columns:
                  raw_text = "\n".join(df["Text"].astype(str).tolist())
                else:
                  raw_text = "\n".join(df.astype(str).agg(" ".join, axis=1).tolist())
              elif ext == "json":
                with open(item, "r", encoding="utf-8") as f:
                  resumes_json = json.load(f)
                  # Recursively process each resume in JSON
                parsed_resumes.extend(self.process_resume_file(resumes_json, category=category))
                continue
              else:
                # Treat unknown file types as TXT
                with open(item, "r", encoding="utf-8") as f:
                  raw_text = f.read()
            else:
              # raw text string
              raw_text = str(item)
              file_name = f"resume_{idx+1}"
              current_resume_id = resume_id if resume_id else f"RES_{idx+1}"
              current_category = category

            if not raw_text.strip():
              print(f"⚠ Empty text for resume {file_name}")
              continue
            original_mapping_data.append({
              "ResumeID": current_resume_id,
              "OriginalText": raw_text,
              "Category": current_category
            })

            # Clean text
            cleaned_text = self.extractor.enhanced_clean_text(raw_text)

            # BlindScreening
            blind_screened_output = self.blindscreen.process_resume_protected(
                cleaned_text, skills_list=[]
            )
            redacted_text = blind_screened_output["cleaned_text"]
            extracted_skills = blind_screened_output["skills"]
            extracted_degrees = blind_screened_output["education"]

            # NLP Parsing
            parser_input = {
                "ResumeID": current_resume_id,
                "FileName": file_name,
                "Category": current_category,
                "cleaned_text": redacted_text,
                "skills": extracted_skills,
                "education": extracted_degrees,
                "EmailFound": bool(self.extractor.extract_email(raw_text)),
                "PhoneFound": bool(self.extractor.extract_phone(raw_text))
            }
            parsed_data = self.parser.parse_resume(parser_input)
            parsed_data["RedactedText"] = redacted_text
            # DEBUG: Log what's being extracted
            print(f"\n📋 Resume {file_name} parsed data:")
            print(f"  - skills: {parsed_data.get('skills', 'NOT FOUND')}")
            print(f"  - experience: {parsed_data.get('experience', 'NOT FOUND')}")
            print(f"  - education: {parsed_data.get('education', 'NOT FOUND')}")
            print(f"  - certifications: {parsed_data.get('certifications', 'NOT FOUND')}")
            print(f"  - achievements: {parsed_data.get('achievements', 'NOT FOUND')}")
            parsed_resumes.append(parsed_data)
        except Exception as e:
          print(f"⚠️ Failed processing resume {item}: {e}")
          traceback.print_exc()

      generate_resume_mapping_csv(original_mapping_data)
      return parsed_resumes


    # ---------------------------
    # JD Processing
    # ---------------------------
    def process_jd_file(self, jd_input) -> Dict[str, Any]:
      """
      Processes JD(s) and returns structured information and cleaned text for embeddings.
      Args:
        jd_input: Can be
            - str: path to a single file (pdf, docx, txt) or raw JD text
            - list: list of file paths
            - dict/list of dict: structured JSON input for multiple JDs
      Returns:
        Dict containing:
            - 'jd_texts': List of cleaned JD texts for embedding
            - 'processed_jds': List of dicts with parsed info (skills, experience, education)
      """
      try:
        jd_texts = []
        structured_jds = []

        # Helper: load raw text from file
        def load_jd_text(file_path_or_text):
          try:
              if os.path.isfile(file_path_or_text):
                  print("📄 JD file detected:", file_path_or_text)

                  if file_path_or_text.endswith(".pdf"):
                      text = self.jd_extractor.extract_from_pdf(file_path_or_text)

                  elif file_path_or_text.endswith(".docx"):
                      text = self.jd_extractor.extract_from_docx(file_path_or_text)

                  elif file_path_or_text.endswith(".txt"):
                      # ✅ FORCE SAFE FILE READ
                      with open(file_path_or_text, "r", encoding="utf-8", errors="ignore") as f:
                          text = f.read()

                  else:
                      # ✅ FALLBACK SAFE READ
                      with open(file_path_or_text, "r", encoding="utf-8", errors="ignore") as f:
                          text = f.read()

                  print("✅ JD text length:", len(text))
                  return text

              elif isinstance(file_path_or_text, str):
                  print("📝 Raw JD text received")
                  return file_path_or_text

              return ""

          except Exception as e:
              print("❌ JD LOAD ERROR:", e)
              return ""


        # Normalize input into a list
        if isinstance(jd_input, (str, dict)):
          jd_input_list = [jd_input]
        elif isinstance(jd_input, list):
          jd_input_list = jd_input
        else:
          raise ValueError("Unsupported JD input type")

        # Process each JD
        for idx, jd_item in enumerate(jd_input_list):
          # 1️⃣ Extract raw text
          if isinstance(jd_item, dict):
            raw_text = jd_item.get("JobDescription", "") or jd_item.get("JD", "")
            job_title = jd_item.get("JobTitle", f"JD_{idx+1}")
            category = jd_item.get("Category", "N/A")
            job_id = jd_item.get("JobID", f"JD_{idx+1}")
          else:
            raw_text = load_jd_text(jd_item)
            job_title = f"JD_{idx+1}"
            category = "N/A"
            job_id = f"JD_{idx+1}"

          if not raw_text.strip():
            print(f"⚠️ Empty JD text for item {jd_item}")
            continue

          # 2️⃣ Clean text
          cleaned_text = self.jd_cleaner.clean_text(raw_text)

          # 3️⃣ Parse JD properly
          parsed_list = JobJDParser.process_job_dataset(
              jobs=[{
                  "JobID": job_id,
                  "JobTitle": job_title,
                  "Category": category,
                  "JobDescription": cleaned_text
              }],
              dataset_name=f"Single JD {idx+1}"
           )
          parsed_jd = parsed_list[0] if parsed_list else {}

          # Append results
          structured_jds.append(parsed_jd)
          jd_texts.append(parsed_jd.get("JobDescription", cleaned_text))

        return {
            "jd_texts": jd_texts,
            "processed_jds": structured_jds
        }
      except Exception as e:
        print(f"⚠️ Failed processing JD input: {e}")
        traceback.print_exc()
        return {
            "jd_texts": [],
            "processed_jds": []
        }


    # ---------------------------
    # Embedding Generation
    # ---------------------------
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        all_embeds = []
        if not texts:
            return np.array([])

        for i in range(0, len(texts), self.config["BATCH_SIZE"]):
            batch = texts[i:i + self.config["BATCH_SIZE"]]
            emb = self.model.encode(batch, convert_to_numpy=True, show_progress_bar=True, device=self.config.get("DEVICE", "cpu"))
            all_embeds.append(emb)
        return np.vstack(all_embeds)

    # ---------------------------
    # Full Pipeline
    # ---------------------------
    def run_pipeline(self, resume_files: List[str], jd_file) -> Dict:
      print("\n⚙️ Step 8: Processing Resumes...")
      processed_resumes_data = []
      resume_texts_for_embedding = []

      for file in resume_files:
        resume_id = os.path.basename(file)
        parsed_resumes_list = self.process_resume_file(file, resume_id=resume_id, category="Unknown")
        for parsed_resume in parsed_resumes_list:
          processed_resumes_data.append(parsed_resume)
          resume_texts_for_embedding.append(parsed_resume["RedactedText"])

      print(f"✓ {len(processed_resumes_data)} resumes processed successfully.")
      print("\n⚙️ Step 8: Processing JD(s)...")
      jd_output = self.process_jd_file(jd_file)
      jd_texts = jd_output.get("jd_texts", [])
      processed_jds = jd_output.get("processed_jds", [])

      if not jd_texts:
        print("⚠️ Failed to process JD(s).")
        return {}

      print("\n⚙️ Step 8: Generating Embeddings...")
      if resume_texts_for_embedding:
        resume_embeddings = self.generate_embeddings(resume_texts_for_embedding)
      else:
        print("⚠️ No resume texts to embed.")
        resume_embeddings = np.array([])

      jd_embeddings = self.generate_embeddings(jd_texts)  # handles single or multiple JDs

      print("\n✅ STEP 8 COMPLETE — Dynamic embeddings ready for FAISS (Step 9)")

      return {
          "processed_resumes_data": processed_resumes_data,
          "resume_embeddings": resume_embeddings,
          "processed_jds": processed_jds,
          "jd_texts": jd_texts,
          "jd_embeddings": jd_embeddings
      }
      print("🔍 Parsed Resume Output:", parsed_resumes_list)
