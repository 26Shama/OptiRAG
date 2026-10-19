import csv
import re
import os
import spacy

# Load spaCy model once (put at top of your module)
nlp = spacy.load("en_core_web_md")


def generate_resume_mapping_csv(resume_records):
    """
    Clears the CSV first, then writes all ResumeID, Name, Email, Category fresh.
    """

    # ✅ DYNAMIC PATH INTEGRATION (ONLY THIS PART ADDED)
    current_script_path = os.path.abspath(__file__)
    pipeline_dir = os.path.dirname(current_script_path)
    backend_dir = os.path.dirname(pipeline_dir)
    base_output_dir = os.path.join(backend_dir, "hr_outputs")
    output_path = os.path.join(base_output_dir, "resume_email_mapping.csv")
    os.makedirs(base_output_dir, exist_ok=True)

    #print(f"DEBUG: Saving CSV to: {output_path}")
    # ✅ END OF PATH INTEGRATION

    email_pattern = re.compile(r'\b[a-zA-Z0-9+._%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b')
    mapping_rows = []

    for rec in resume_records:
        resume_id = rec.get("ResumeID")
        text = rec.get("OriginalText", "") or rec.get("Text", "")
        category = rec.get("Category", "Unknown")

        if not resume_id:
            print(f"⚠️ Skipping record without ResumeID: {rec}")
            continue
        if not text.strip():
            print(f"⚠️ Skipping empty resume text for ResumeID {resume_id}")
            continue

        email_match = email_pattern.search(text)
        email = email_match.group(0) if email_match else ""
        
        # ✅ Extract name using spaCy NER instead of regex
        doc = nlp(text)
        name = ""
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = ent.text
                break

        mapping_rows.append({
            "ResumeID": resume_id,
            "Name": name,
            "Email": email,
            "Category": category
        })

    if not mapping_rows:
        print("⚠️ No valid resume data to save.")
        return output_path
    
    #for i in range(len(mapping_rows)):
        #print(mapping_rows[i])

    # Determine if header needs to be written
    file_exists = os.path.exists(output_path)
    file_is_empty = not file_exists or os.stat(output_path).st_size == 0

    # Use append mode, but write header only if file is new/empty
    with open(output_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["ResumeID", "Name", "Email", "Category"])
        if file_is_empty:
            writer.writeheader()  # ✅ header only once
        writer.writerows(mapping_rows)

    #print(f"✅ CSV mapping refreshed at: {output_path} (total rows: {len(mapping_rows)})")
    #print("DEBUG: mapping_rows written:", mapping_rows)

    return output_path
