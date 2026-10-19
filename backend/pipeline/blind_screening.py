import re
import json
import uuid
from tqdm import tqdm
from ..pipeline.nlp_init import nlp, skill_matcher
# Finance certifications / degrees to handle carefully
FINANCE_CERTS = ['CFA', 'CPA', 'CA', 'CMA', 'FRM', 'CFP', 'ACCA', 'CIMA','CIM', 'IBC']


# 2️⃣ Blind Screening
class BlindScreening:

    @staticmethod
    def extract_skills_phrasematcher(text):
        if not text.strip():
            return []

        try:
            # 🔥 ADD LAZY INITIALIZATION HERE
            from ..pipeline.nlp_init import nlp, skill_matcher, initialize_nlp
        
            # Check if NLP is loaded
            if nlp is None or skill_matcher is None:
                print("⚠️ Global NLP not initialized, loading locally...")
                initialize_nlp()  # This will load the NLP model
                # Re-import after initialization
                from ..pipeline.nlp_init import nlp, skill_matcher
            doc = nlp(text)
            matches = skill_matcher(doc)
            skills_found = set()

            for match_id, start, end in matches:
                try:
                    if start < len(doc) and end <= len(doc):
                        skill_text = doc[start:end].text.strip()
                        if skill_text:
                            skills_found.add(skill_text)
                except IndexError:
                    continue

            return sorted(list(skills_found))
        except Exception:
            return []

    @staticmethod
    def is_valid_degree_final(degree_text, full_text, position):
        lower_degree = degree_text.lower()
        false_positives = ['be', 'ba', 'ma']

        if lower_degree in false_positives:
            context_start = max(0, position - 100)
            context_end = min(len(full_text), position + 100)
            context = full_text[context_start:context_end].lower()

            education_terms = [
                'education', 'qualification', 'degree', 'bachelor', 'master',
                'graduat', 'engineer', 'study', 'college', 'university',
                'institute', 'course', 'program', 'passed', 'marks', 'percentage'
            ]

            if not any(term in context for term in education_terms):
                return False

        return True

    @staticmethod
    def extract_degrees_with_spans(text):
        if not text.strip():
            return [], []

        all_degree_matches = []

        degree_patterns = [
            r'\b(B\.?\s*Tech\s+in\s+[A-Za-z\s]+)\b',
            r'\b(B\.?\s*E\s+in\s+[A-Za-z\s]+)\b',
            r'\b(B\.?\s*Sc\s+in\s+[A-Za-z\s]+)\b',
            r'\b(M\.?\s*Tech\s+in\s+[A-Za-z\s]+)\b',
            r'\b(M\.?\s*Sc\s+in\s+[A-Za-z\s]+)\b',
            r'\b(MBA\s+in\s+[A-Za-z\s]+)\b',
            r'\b(MCA\s+in\s+[A-Za-z\s]+)\b',
            r'\b(Bachelor\s+of\s+[A-Za-z\s]+)\b',
            r'\b(B\.?Com)\b',
            r'\b(B\.?A\.?)\b',
            r'\b(Master\s+of\s+[A-Za-z\s]+)\b',
            r'\b(M\.?Com)\b',
            r'\b(M\.?A\.?)\b',
            r'\b(B\.?Tech)\b',
            r'\b(B\.?Sc\.?)\b',
            r'\b(M\.?Tech)\b',
            r'\b(M\.?Sc\.?)\b',
            r'\b(MBA)\b',
            r'\b(MCA)\b',
            r'\b(PhD)\b',
            r'\b(B\.?E\.?)\b',
            r'\b(HSC|Higher Secondary School Certificate)\b',
            r'\b(SSC|Secondary School Certificate)\b',
        ]

        for pattern in degree_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                degree_text = match.group().strip()
                start, end = match.span()

                degree_text = re.sub(r'\s+[A-Z]\s*$', '', degree_text)
                degree_text = re.sub(r'\s+', ' ', degree_text).strip()

                if BlindScreening.is_valid_degree_final(degree_text, text, start):
                    all_degree_matches.append((degree_text, start, end))

        manual_degree_checks = [
            (r'bechalore of commerece', 'Bachelor of Commerce'),
            (r'bachelor of commerece', 'Bachelor of Commerce'),
            (r'bechalore of commerce', 'Bachelor of Commerce'),
            (r'bachelor of commerce', 'Bachelor of Commerce'),
        ]

        for pattern, replacement in manual_degree_checks:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                all_degree_matches.append((replacement, match.start(), match.end()))

        for cert in FINANCE_CERTS:
            for match in re.finditer(r'\b' + re.escape(cert) + r'\b', text, re.IGNORECASE):
                all_degree_matches.append((cert, match.start(), match.end()))

        final_degrees, final_spans = [], []
        all_degree_matches.sort(key=lambda x: len(x[0]), reverse=True)
        seen_degrees = set()

        for degree_text, start, end in all_degree_matches:
            is_covered = False

            for existing_degree in final_degrees:
                if degree_text in existing_degree and degree_text != existing_degree:
                    is_covered = True
                    break

            normalized = degree_text.lower().strip()
            if not is_covered and normalized not in seen_degrees:
                final_degrees.append(degree_text)
                final_spans.append((start, end))
                seen_degrees.add(normalized)

        return final_degrees, final_spans

    @staticmethod
    def blind_screen_protected(text):
        if not text.strip():
            return text

        degrees, degree_spans = BlindScreening.extract_degrees_with_spans(text)
        skills = BlindScreening.extract_skills_phrasematcher(text)

        protected_spans = degree_spans.copy()
        for skill in skills:
            for match in re.finditer(re.escape(skill), text, re.IGNORECASE):
                protected_spans.append(match.span())

        protected_spans.sort()
        merged_spans = []
        for start, end in protected_spans:
            if merged_spans and start <= merged_spans[-1][1]:
                merged_spans[-1] = (merged_spans[-1][0], max(merged_spans[-1][1], end))
            else:
                merged_spans.append((start, end))
        protected_spans = merged_spans

        def is_protected(position):
            for start, end in protected_spans:
                if start <= position < end:
                    return True
            return False

        redaction_ops = []

        for match in re.finditer(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', text):
            if not is_protected(match.start()):
                redaction_ops.append((match.start(), match.end(), '[REDACTED_EMAIL]'))

        for match in re.finditer(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', text):
            if not is_protected(match.start()):
                redaction_ops.append((match.start(), match.end(), '[REDACTED_PHONE]'))

        for match in re.finditer(r'\b\d{10}\b', text):
            if not is_protected(match.start()):
                redaction_ops.append((match.start(), match.end(), '[REDACTED_PHONE]'))

        link_patterns = [
            r'https?://(?:www\.)?github\.com/[\w\-]+',
            r'GitHub:\s*https?://(?:www\.)?github\.com/[\w\-]+',
            r'GitHub:\s*[\w\-]+',
            r'github\.com/[\w\-]+',
            r'https?://(?:www\.)?linkedin\.com/in/[\w\-]+',
            r'LinkedIn:\s*https?://(?:www\.)?linkedin\.com/in/[\w\-]+',
            r'LinkedIn:\s*[\w\-]+',
            r'linkedin\.com/in/[\w\-]+',
        ]

        for pattern in link_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                if not is_protected(match.start()):
                    redaction_ops.append((match.start(), match.end(), '[REDACTED_LINK]'))

        try:
            doc = nlp(text)
            for ent in doc.ents:
                if ent.label_ in ["PERSON"]:
                    overlap = False
                    for start, end in protected_spans:
                        if not (ent.end_char <= start or ent.start_char >= end):
                            overlap = True
                            break
                    if not overlap:
                        redaction_ops.append((ent.start_char, ent.end_char, '[REDACTED_PERSON]'))

                elif ent.label_ in ["ORG"]:
                    org_text = ent.text.lower()
                    is_educational = any(edu_term in org_text for edu_term in
                                         ['university', 'college', 'institute', 'school'])

                    if not is_educational and not is_protected(ent.start_char):
                        redaction_ops.append((ent.start_char, ent.end_char, '[REDACTED_ORG]'))

                elif ent.label_ in ["GPE"]:
                    if not is_protected(ent.start_char):
                        redaction_ops.append((ent.start_char, ent.end_char, '[REDACTED_LOCATION]'))
        except Exception:
            for match in re.finditer(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', text):
                if not is_protected(match.start()):
                    redaction_ops.append((match.start(), match.end(), '[REDACTED_PERSON]'))

        redaction_ops.sort(key=lambda x: x[0], reverse=True)
        for start, end, replacement in redaction_ops:
            text = text[:start] + replacement + text[end:]

        return text

    @staticmethod
    def process_resume_protected(text, skills_list):
        if not text.strip():
            return {
                "education": [],
                "skills": [],
                "cleaned_text": ""
            }

        try:
            degrees, _ = BlindScreening.extract_degrees_with_spans(text)
            skills = BlindScreening.extract_skills_phrasematcher(text)
            cleaned_text = BlindScreening.blind_screen_protected(text)

            return {
                "education": degrees,
                "skills": skills,
                "cleaned_text": cleaned_text
            }
        except Exception:
            return {
                "education": [],
                "skills": [],
                "cleaned_text": text
            }

    # 🔹 ONLY ADDING THIS WRAPPER FOR FASTAPI SUPPORT
    @staticmethod
    def blind_screen_uploaded_resumes(resumes: list):
        updated = []
        for resume in resumes:
            text = resume.get("Text", "")
            result = BlindScreening.process_resume_protected(text, [])
            resume.update(result)  # merge fields into original dict
            updated.append(resume)
        return updated

# Convenience wrapper for module-level import
def blind_screen(resumes):
    return BlindScreening.blind_screen_uploaded_resumes(resumes)
