import os
import json
import spacy
from spacy.matcher import PhraseMatcher

# ✅ Global objects (IMPORTANT)
nlp = None
skill_matcher = None


def initialize_nlp():
    """
    Load spaCy model + skills list 1 time when backend starts.
    """
    global nlp, skill_matcher

    # ✅ Prevent double loading
    if nlp is not None and skill_matcher is not None:
        return

    # ✅ Load spaCy model Safely
    try:
        nlp = spacy.load("en_core_web_md")
    except:
        print("Downloading spaCy model...")
        os.system("python -m spacy download en_core_web_md")
        nlp = spacy.load("en_core_web_md")

    # ✅ Load skills JSON
    base_dir = os.path.dirname(os.path.abspath(__file__))
    skill_path = os.path.join(base_dir, "..", "assets", "skills_list_clean.json")

    with open(skill_path, "r", encoding="utf-8") as f:
        skills_data = json.load(f)

    # ✅ Handle both list & dict
    if isinstance(skills_data, dict):
        all_skills = sum(skills_data.values(), [])
    else:
        all_skills = skills_data

    # ✅ Create PhraseMatcher
    skill_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    filtered_skills = [skill for skill in all_skills if len(skill.split()) <= 5]
    patterns = [nlp.make_doc(skill) for skill in filtered_skills]
    skill_matcher.add("SKILLS", patterns)

    print("✅ NLP + Skills loaded successfully")
