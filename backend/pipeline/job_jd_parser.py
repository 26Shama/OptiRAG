import re
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Union
from fastapi import HTTPException  # FastAPI compatible error handling

from tqdm import tqdm
import spacy
from spacy.matcher import PhraseMatcher


from ..pipeline.nlp_init import nlp, skill_matcher
from ..pipeline.blind_screening import FINANCE_CERTS

try:
    nlp = spacy.load("en_core_web_sm")
except:
    print("⚠️ SpaCy model missing. Download it using:")
    print("python -m spacy download en_core_web_sm")
    nlp = None

try:
    skill_matcher = PhraseMatcher(nlp.vocab, attr="LOWER") if nlp else None
except Exception as e:
    print("⚠️ Failed to initialize skill matcher:", e)
    skill_matcher = None


text2num = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
}
text2num = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
}

# 6️⃣ JD Parsing
class JobJDParser:

    @staticmethod
    def normalize_textual_numbers(text):
        for word, num in text2num.items():
            text = re.sub(fr"\b{word}\b(?=\s*(?:years|year|yrs|yr))", str(num), text, flags=re.IGNORECASE)
        return text

    @staticmethod
    def normalize_hyphens(text):
        return re.sub(r"([A-Za-z])\-([A-Za-z])", r"\1 \2", text)

    @staticmethod
    def infer_experience_from_title(title):
        title = title.lower()
        if any(x in title for x in ["junior", "fresher", "entry"]):
            return [0, 1, 2]
        elif any(x in title for x in ["mid", "intermediate"]):
            return [3, 4, 5]
        elif any(x in title for x in ["senior", "lead", "manager"]):
            return [5, 6, 7, 8, 9, 10]
        elif any(x in title for x in ["principal", "director", "head", "vp", "chief"]):
            return [8, 9, 10, 11, 12, 13, 14, 15]
        return []

    @staticmethod
    def infer_from_context(jd_text):
        text = jd_text.lower()
        if "extensive experience" in text:
            return [7, 8, 9, 10]
        elif "solid experience" in text:
            return [5, 6, 7]
        elif "some experience" in text:
            return [1, 2]
        return []

    @staticmethod
    def remove_non_experience_context(text):
        """ULTIMATE CLEANING: Remove ALL non-experience numbers"""
        # Remove salary ranges (like "8L - 12L / yr")
        text = re.sub(r"\b\d+\s*[lLkK]\s*-\s*\d+\s*[lLkK]\s*/\s*(?:year|yr)", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"\b\d+\s*-\s*\d+\s*[lLkK]\b", " ", text)
        text = re.sub(r"\b\d+\s*[lLkK]\s*/\s*(?:year|yr)", " ", text, flags=re.IGNORECASE)

        # Remove standalone LPA/lakhs
        text = re.sub(r"\b\d+\s*(?:lpa|lakhs?)\b", " ", text, flags=re.IGNORECASE)

        # Remove salary mentions with numbers
        text = re.sub(
            r"(salary|ctc|package|annual|per\s*year|per\s*month|lpa|lakhs|up to|esop)\s*[:\-]*\s*[\d,\.]+(?:\s*(?:per\s*(?:year|month))?)?",
            " ",
            text,
            flags=re.IGNORECASE
        )

        # Remove years like 2004, 2020, etc. (likely dates)
        text = re.sub(r"\b(19|20)\d{2}\b", " ", text)
        # Remove any standalone 3+ digit numbers that aren't in experience context
        text = re.sub(r"\b\d{3,}\b", " ", text)
        # Remove other non-experience numbers
        text = re.sub(r"Vacancies:.*?\d+", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"Job Location:.*?\d+", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"Schedule:.*?\d+", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"Age:.*?\d+", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"Work:.*?\d+(?:am|pm)", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"Since\s*\d{4}", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"/\s*yr\b", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"/\s*year\b", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"\b\d{1,3}\s*[,\.]\s*\d{3}\b", " ", text)
        text = re.sub(r"\b\d{1,3}\s*[,\.]\s*\d{3}\s*[-–]\s*\d{1,3}\s*[,\.]\s*\d{3}\b", " ", text)
        text = re.sub(r"(per\s+month|per\s+annum|monthly|annually)", " ", text, flags=re.IGNORECASE)
        text = re.sub(r"(₹|Rs\.?|USD|INR|\$)\s*\d+[,\d]*(\.\d+)?", " ", text, flags=re.IGNORECASE)

        return text

    @staticmethod
    def extract_experience_fixed(text):
        """ULTIMATE FIX: Pure regex-based extraction - NO SPACY FOR NUMBERS"""
        experience_numbers = []

        # 🔥 FIX: Apply normalization BEFORE cleaning
        normalized_text = JobJDParser.normalize_textual_numbers(text)
        normalized_text = JobJDParser.normalize_hyphens(normalized_text)
        cleaned_text = JobJDParser.remove_non_experience_context(normalized_text)

        # STRICT experience patterns - ONLY regex, no spaCy
        experience_patterns = [
     # ==========================================
    # PRIORITY 1: EXPLICIT RANGES
    # ==========================================
    r'(\d{1,2})\s*(?:-|to|–)\s*(\d{1,2})\s*(?:years?|yrs?)(?:\s+(?:of\s+)?experience)?',

    r'between\s+(\d{1,2})\s+and\s+(\d{1,2})\s*(?:years?|yrs?)',

    # ==========================================
    # PRIORITY 2: SINGLE NUMBERS WITH CONTEXT
    # ==========================================
    r'(\d{1,2})\s*(?:\+)?\s*(?:years?|yrs?)(?:\s+(?:of\s+)?experience)?',

    r'(\d{1,2})\s*(?:years?|yrs?)\s+experience',

    r'(\d{1,2})\s*(?:years?|yrs?)\s+(?:in|with|of)',

    # ==========================================
    # PRIORITY 3: CONTEXTUAL KEYWORDS
    # ==========================================
    r'(?:minimum|at least|atleast|required|need|must\s+have)\s+(?:of\s+)?(\d{1,2})\s*(?:years?|yrs?)',

    r'(?:minimum|at least)\s+of\s+(\d{1,2})\s*(?:years?|yrs?)',

    # ==========================================
    # PRIORITY 4: EXPERIENCE PREFIX
    # ==========================================
    r'experience\s*[:|-]?\s*(\d{1,2})\s*(?:years?|yrs?)',

    r'total\s+(?:work\s+)?experience\s*[:|-]?\s*(\d{1,2})\s*(?:years?|yrs?)',

    r'(\d{1,2})\s*(?:years?|yrs?)\s+total(?:\s+(?:work\s+)?experience)?',

    # ==========================================
    # PRIORITY 5: REQUIREMENT KEYWORDS
    # ==========================================
    r'(\d{1,2})\s*(?:years?|yrs?)\s*(?:preferred|required|must)',

    # ==========================================
    # PRIORITY 6: FALLBACK (SIMPLE)
    # ==========================================
    r'\b(\d{1,2})\s*(?:years?|yrs?)\b',
]

        for pattern in experience_patterns:
            matches = re.finditer(pattern, cleaned_text, re.IGNORECASE)
            for match in matches:
                # Handle range patterns (2 numbers)
                if len(match.groups()) >= 2 and match.group(1) and match.group(2):
                    try:
                        num1, num2 = int(match.group(1)), int(match.group(2))
                        if 1 <= num1 <= 20 and 1 <= num2 <= 20 and num1 <= num2:
                            # Add all numbers in the range
                            experience_numbers.extend(list(range(num1, num2 + 1)))
                    except ValueError:
                        continue

                # Handle single number patterns
                else:
                    for group_num in range(1, len(match.groups()) + 1):
                        num_str = match.group(group_num)
                        if num_str and num_str.isdigit():
                            try:
                                num = int(num_str)
                                if 1 <= num <= 20:
                                    experience_numbers.append(num)
                            except ValueError:
                                continue

        # Additional simple pattern for basic "X years" if nothing found
        if not experience_numbers:
            basic_matches = re.finditer(r'\b(\d{1,2})\s*(?:years?|yrs?)\b', cleaned_text, re.IGNORECASE)
            for match in basic_matches:
                num_str = match.group(1)
                if num_str and num_str.isdigit():
                    num = int(num_str)
                    if 1 <= num <= 20:
                        experience_numbers.append(num)

        return list(set(experience_numbers))

    @staticmethod
    def extract_only_single_double_digit_numbers(numbers_list):
        """ULTIMATE FILTER: Only keep 1-2 digit numbers (0-99)"""
        cleaned = []
        for num in numbers_list:
            if isinstance(num, str):
                if num.isdigit():
                    num = int(num)
                else:
                    continue

            num_str = str(num)
            if len(num_str) <= 2:
                cleaned.append(num)

        return cleaned

    @staticmethod
    def is_valid_degree_ultimate(degree_text, full_text, position):
        """ULTIMATE VALIDATION: Block ALL false positives"""
        lower_degree = degree_text.lower().strip()

        absolute_blocked = [
            'be', 'ba', 'ma', 'me', 'b.', 'm.', 'b', 'm', 'a', 'e', 'c', 'd'
        ]

        if lower_degree in absolute_blocked:
            return False

        allowed_short_degrees = [
            'mba', 'mca', 'phd', 'bsc', 'msc', 'btech', 'mtech',
            'bcom', 'mcom', 'bca', 'dba', 'cfa', 'cpa', 'ca', 'cma',
            'frm', 'cfp', 'acc', 'cim', 'ibc', 'pgd', 'dm', 'dtech'
        ]

        if len(degree_text) <= 3 and lower_degree not in allowed_short_degrees:
            return False

        return True

    @staticmethod
    def extract_degrees_with_spans(text):
        """ULTIMATE FIX: Extract degrees without ANY false positives"""
        if not text.strip():
            return ["No Education Mentioned"], []

        all_degree_matches = []

        degree_patterns = [
            # ============================
    # ✅ UNDERGRADUATE DEGREES
    # ============================
    # Bachelor of Science family
    r'\bB\s*\.?\s*S\s*\.?\s*C\s*\.?\b',
    r'\bB\s*C\s*S\b',
    r'\bB\s*S\s*C\b',
    r'\bBachelor(?:\'?s)?\s+of\s+Science\b',

    # Bachelor of Arts family
    r'\bB\s*\.?\s*A\s*\.?\b',
    r'\bB\s*A\b',
    r'\bBachelor(?:\'?s)?\s+of\s+Arts\b',

    # Bachelor of Commerce family
    r'\bB\s*\.?\s*C\s*\.?\s*O\s*\.?\s*M\s*\.?\b',
    r'\bB\s*C\s*O\s*M\b',
    r'\bBachelor(?:\'?s)?\s+of\s+Commerce\b',

    # Bachelor of Business Administration
    r'\bB\s*\.?\s*B\s*\.?\s*A\s*\.?\b',
    r'\bB\s*B\s*A\b',
    r'\bBachelor(?:\'?s)?\s+of\s+Business\s+Administration\b',

    # Bachelor of Engineering
    r'\bB\s*\.?\s*E\s*\.?\b',
    r'\bB\s*E\b',
    r'\bBachelor(?:\'?s)?\s+of\s+Engineering\b',

    # Bachelor of Technology
    r'\bB\s*\.?\s*T\s*\.?\s*E\s*\.?\s*C\s*\.?\s*H\s*\.?\b',
    r'\bB\s*T\s*E\s*C\s*H\b',
    r'\bBachelor(?:\'?s)?\s+of\s+Technology\b',

    # Bachelor of Computer Applications
    r'\bB\s*\.?\s*C\s*\.?\s*A\s*\.?\b',
    r'\bB\s*C\s*A\b',
    r'\bBachelor(?:\'?s)?\s+of\s+Computer\s+Applications\b',

    # Bachelor of Design
    r'\bB\s*\.?\s*D\s*\.?\s*E\s*\.?\s*S\s*\.?\b',
    r'\bB\s*D\s*E\s*S\b',
    r'\bBachelor(?:\'?s)?\s+of\s+Design\b',

    # Bachelor of Architecture
    r'\bB\s*\.?\s*A\s*\.?\s*R\s*\.?\s*C\s*\.?\s*H\s*\.?\b',
    r'\bB\s*A\s*R\s*C\s*H\b',
    r'\bBachelor(?:\'?s)?\s+of\s+Architecture\b',

    # Bachelor of Economics / Finance
    r'\bB\s*\.?\s*E\s*\.?\s*C\s*\.?\b',
    r'\bB\s*E\s*C\b',
    r'\bBachelor(?:\'?s)?\s+of\s+(?:Economics|Finance)\b',

    # Generic "Bachelor in ..."
    r'\bBachelor(?:\'?s)?\s+(?:Degree\s+)?in\s+[A-Za-z\s]+',

    # ============================
    # ✅ POSTGRADUATE DEGREES
    # ============================

    # Master of Science
    r'\bM\s*\.?\s*S\s*\.?\s*C\s*\.?\b',
    r'\bM\s*S\s*C\b',
    r'\bMaster(?:\'?s)?\s+of\s+Science\b',

    # Master of Arts
    r'\bM\s*\.?\s*A\s*\.?\b',
    r'\bM\s*A\b',
    r'\bMaster(?:\'?s)?\s+of\s+Arts\b',

    # Master of Commerce
    r'\bM\s*\.?\s*C\s*\.?\s*O\s*\.?\s*M\s*\.?\b',
    r'\bM\s*C\s*O\s*M\b',
    r'\bMaster(?:\'?s)?\s+of\s+Commerce\b',

    # Master of Business Administration (MBA)
    r'\bM\s*\.?\s*B\s*\.?\s*A\s*\.?\b',
    r'\bM\s*B\s*A\b',
    r'\bMaster(?:\'?s)?\s+of\s+Business\s+Administration\b',

    # Master of Finance
    r'\bM\s*\.?\s*F\s*\.?\s*I\s*\.?\s*N\s*\.?\b',
    r'\bM\s*F\s*I\s*N\b',
    r'\bMaster(?:\'?s)?\s+of\s+Finance\b',

    # Master of Economics
    r'\bM\s*\.?\s*E\s*\.?\s*C\s*\.?\b',
    r'\bM\s*E\s*C\b',
    r'\bMaster(?:\'?s)?\s+of\s+Economics\b',

    # Master of Accountancy / Accounting
    r'\bM\s*\.?\s*A\s*\.?\s*C\s*\.?\s*C\s*\.?\b',
    r'\bM\s*A\s*C\s*C\b',
    r'\bMaster(?:\'?s)?\s+of\s+(?:Accountancy|Accounting)\b',

    # Master of Technology / Engineering / Design
    r'\bM\s*\.?\s*T\s*\.?\s*E\s*\.?\s*C\s*\.?\s*H\s*\.?\b',
    r'\bM\s*T\s*E\s*C\s*H\b',
    r'\bMaster(?:\'?s)?\s+of\s+(?:Technology|Engineering|Design)\b',

    # Master in Generic Form
    r'\bMaster(?:\'?s)?\s+(?:Degree\s+)?in\s+[A-Za-z\s]+',

    # ============================
    # ✅ DOCTORATE DEGREES
    # ============================
    r'\bP\s*\.?\s*H\s*\.?\s*D\s*\.?\b',
    r'\bPhD\b',
    r'\bDoctor(?:ate)?\b',
    r'\bDoctor\s+of\s+(?:Philosophy|Business\s+Administration|Economics|Technology)\b',
    r'\bD\s*\.?\s*B\s*\.?\s*A\s*\.?\b',
    r'\bD\s*\.?\s*E\s*\.?\s*C\s*\.?\s*O\s*\.?\s*N\s*\.?\b',
    r'\bD\s*\.?\s*T\s*\.?\s*E\s*\.?\s*C\s*\.?\s*H\s*\.?\b',

    # Post Graduate Diploma (PGD / PGDM)
    r'\bP\s*G\s*D\s*M\b',
    r'\bP\s*G\s*D\b',
    r'\bP\s*G\s+Diploma\b',
    r'\bPost\s+Graduate\s+Diploma\b',

    # ============================
    # ✅ FINANCE & PROFESSIONAL CERTIFICATIONS
    # ============================
    r'\bC\s*F\s*A\b',    # Chartered Financial Analyst
    r'\bC\s*P\s*A\b',    # Certified Public Accountant
    r'\bC\s*A\b',        # Chartered Accountant
    r'\bC\s*M\s*A\b',    # Certified Management Accountant
    r'\bF\s*R\s*M\b',    # Financial Risk Manager
    r'\bC\s*F\s*P\b',    # Certified Financial Planner
    r'\bA\s*C\s*C\s*A\b',# ACCA
    r'\bC\s*I\s*M\s*A\b',# Chartered Institute of Management Accountants
    r'\bI\s*C\s*W\s*A\s*I\b', # Institute of Cost & Works Accountants of India
    r'\bC\s*I\s*M\b',    # Chartered Institute of Marketing
    r'\bI\s*B\s*C\b',    # Insolvency & Bankruptcy Code (rare but seen)
    r'\bA\s*C\s*A\b',    # Associate Chartered Accountant

    # ============================
    # ✅ OTHER / MISC DEGREES
    # ============================
    r'\bL\s*\.?\s*L\s*\.?\s*B\s*\.?\b',  # Bachelor of Laws
    r'\bL\s*\.?\s*L\s*\.?\s*M\s*\.?\b',  # Master of Laws
    r'\bM\s*\.?\s*P\s*\.?\s*H\s*\.?\b',  # Master of Public Health
    r'\bM\s*\.?\s*S\s*\.?\s*W\s*\.?\b',  # Master of Social Work
    r'\bB\s*\.?\s*E\s*\.?\s*d\s*\.?\b',  # Bachelor of Education
    r'\bM\s*\.?\s*E\s*\.?\s*d\s*\.?\b',  # Master of Education

    # ============================
    # ✅ GENERIC
    # ============================
    r'\bAny\s+Graduate\b',
    r'\bAny\s+Post\s+Graduate\b',
    r'\bGraduate\s+Degree\b',
    r'\bPost\s+Graduate\s+Degree\b',
    ]

        for pattern in degree_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                degree_text = match.group().strip()
                start, end = match.span()

                degree_text = re.sub(r'\s+[A-Z]\s*$', '', degree_text)
                degree_text = re.sub(r'\s+', ' ', degree_text).strip()

                if JobJDParser.is_valid_degree_ultimate(degree_text, text, start):
                    all_degree_matches.append((degree_text, start, end))

        for cert in FINANCE_CERTS:
            for match in re.finditer(r'\b' + re.escape(cert) + r'\b', text, re.IGNORECASE):
                all_degree_matches.append((cert, match.start(), match.end()))

        final_degrees = []
        final_spans = []

        all_degree_matches.sort(key=lambda x: len(x[0]), reverse=True)
        seen_degrees = set()

        for degree_text, start, end in all_degree_matches:
            is_covered = False
            for existing_degree in final_degrees:
                if degree_text.lower() in existing_degree.lower() and degree_text.lower() != existing_degree.lower():
                    is_covered = True
                    break

            normalized = degree_text.lower().strip()
            if not is_covered and normalized not in seen_degrees:
                final_degrees.append(degree_text)
                final_spans.append((start, end))
                seen_degrees.add(normalized)

        if not final_degrees:
            education_terms = [
                'education', 'qualification', 'degree', 'graduate', 'bachelor',
                'master', 'phd', 'diploma', 'university', 'college'
            ]
            has_education_context = any(term in text.lower() for term in education_terms)

            if has_education_context:
                return ["Education Not Specified"], []
            else:
                return ["No Education Requirement"], []

        return final_degrees, final_spans

    @staticmethod
    def process_job_dataset(jobs, dataset_name):
        """Process a dataset with the existing parsing logic"""
        print(f"\n🔄 Processing {dataset_name} dataset ({len(jobs)}) jobs)...")

        processed_jobs = []

        for job in tqdm(jobs, desc=f"Processing {dataset_name}"):
            processed_job = job.copy()

            original_jd_text = f"{processed_job.get('JobTitle', '')} {processed_job.get('JobDescription', '')}"

            # --- SKILL EXTRACTION ---
            skill_text = original_jd_text
            if nlp is None:
                doc = skill_text   # fallback: treat as raw text
            else:
                doc = nlp(skill_text)
            matches = skill_matcher(doc)
            found_skills = set()
            for _, start, end in matches:
                found_skills.add(doc[start:end].text.lower())
            # ✅ FIX: Use consistent field name
            processed_job["JD_Skills"] = sorted(found_skills)  # ← CHANGE TO Skills
            processed_job["Skills"] = sorted(found_skills)

            # --- EXPERIENCE EXTRACTION ---
            exp_text = f"{processed_job.get('JobTitle', '')} {processed_job.get('JobDescription', '')}"

            req_years_numbers = JobJDParser.extract_experience_fixed(exp_text)

            if not req_years_numbers:
                req_years_numbers = JobJDParser.infer_experience_from_title(processed_job.get("JobTitle", ""))

            if not req_years_numbers:
                req_years_numbers = JobJDParser.infer_from_context(exp_text)

            nuclear_cleaned = []
            for num in req_years_numbers:
                num_str = str(num)
                if len(num_str) > 2:
                    clean_num = int(num_str[-2:])
                else:
                    clean_num = int(num_str)

                if 0 <= clean_num <= 20:
                    nuclear_cleaned.append(clean_num)

            req_years_numbers = sorted(set(nuclear_cleaned))
            # Also update experience field for consistency
            processed_job["Experience"] = req_years_numbers[0] if req_years_numbers else 0  # ← ADD THIS

            if req_years_numbers:
                min_yrs, max_yrs = min(req_years_numbers), max(req_years_numbers)
                processed_job["Req_Years"] = (
                    f"{min_yrs}-{max_yrs} years ({req_years_numbers})"
                    if len(req_years_numbers) > 1 else f"{max_yrs} years"
                )
                processed_job["Req_Years_Value"] = req_years_numbers
            else:
                processed_job["Req_Years"] = "0 years"
                processed_job["Req_Years_Value"] = [0]

            # --- EDUCATION EXTRACTION ---
            edu_text = f"{processed_job.get('JobTitle', '')} {processed_job.get('JobDescription', '')}"
            degrees, spans = JobJDParser.extract_degrees_with_spans(edu_text)
            processed_job["JD_Education"] = degrees

            processed_jobs.append(processed_job)

        return processed_jobs

    @staticmethod
    def apply_nuclear_fix_and_save(jobs, dataset_name, output_path):
        """Apply the nuclear fix and save as CSV"""

        # Apply nuclear fix
        for job in jobs:
            years_value = job.get("Req_Years_Value", [])

            cleaned_years = []
            for num in years_value:
                num_str = str(num).strip()
                num_str = re.sub(r'[^\d]', '', num_str)

                if num_str:
                    if len(num_str) > 2:
                        clean_num = int(num_str[-2:])
                    else:
                        clean_num = int(num_str)

                    if 0 <= clean_num <= 20:
                        cleaned_years.append(clean_num)

            job["Req_Years_Value"] = sorted(set(cleaned_years))

            if job["Req_Years_Value"]:
                years_list = job["Req_Years_Value"]
                min_yrs, max_yrs = min(years_list), max(years_list)
                job["Req_Years"] = (
                    f"{min_yrs}-{max_yrs} years ({years_list})"
                    if len(years_list) > 1 else f"{max_yrs} years"
                )
            else:
                job["Req_Years"] = "0 years"
                job["Req_Years_Value"] = [0]

        csv_data = []
        for job in jobs:
            years_value = job.get("Req_Years_Value", [])

            fixed_years = []
            for num in years_value:
                num_str = str(num)

                if num_str == '2001':
                    fixed_years.append(1)
                elif num_str == '2002':
                    fixed_years.append(2)
                elif num_str == '2003':
                    fixed_years.append(3)
                elif num_str == '2004':
                    fixed_years.append(4)
                elif num_str == '2005':
                    fixed_years.append(5)
                elif num_str == '2006':
                    fixed_years.append(6)
                elif num_str == '2007':
                    fixed_years.append(7)
                elif num_str == '2008':
                    fixed_years.append(8)
                elif num_str == '2009':
                    fixed_years.append(9)
                elif 1 <= int(num_str) <= 20:
                    fixed_years.append(int(num_str))

            fixed_years = sorted(set(fixed_years))

            if not fixed_years:
                years_display = "0"
            elif len(fixed_years) == 1:
                years_display = f"{fixed_years[0]}"
            else:
                min_yrs = min(fixed_years)
                max_yrs = max(fixed_years)
                years_display = f"{min_yrs}-{max_yrs}"

            csv_data.append({
                "Category": job.get("Category", ""),
                "JobTitle": job.get("JobTitle", ""),
                "JobDescription": job.get("JobDescription", ""),
                "JD_Skills": ", ".join(job.get("JD_Skills", [])),
                "Req_Years_Value": years_display,
                "JD_Education": ", ".join(job.get("JD_Education", []))
            })

        df = pd.DataFrame(csv_data)
        df.to_csv(output_path, index=False, encoding="utf-8-sig")
        return jobs