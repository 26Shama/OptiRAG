VALID_CATEGORIES = ["IT", "Finance"]
import faiss
import numpy as np
import os
import uuid
from ..utils.deepseek_client import generate_deepseek_response
# In Cell 4 - Update the validate_inputs function:
def validate_inputs(category, jd_input, resumes_input, top_n):
    """Validate pipeline inputs - FIXED FOR FILE PATHS"""
    # ✅ REMOVE CATEGORY VALIDATION
    # if category not in VALID_CATEGORIES:
    #     raise ValueError(f"Category must be one of {VALID_CATEGORIES}")
    if top_n <= 0 or top_n > 50:
        raise ValueError("top_n must be between 1 and 50")
    # ✅ Handle JD input
    if isinstance(jd_input, str):
        if jd_input.endswith('.json'):
            if not os.path.exists(jd_input):
                raise ValueError(f"JD JSON file not found: {jd_input}")
        else:
            if not os.path.exists(jd_input):
                raise ValueError(f"JD file not found: {jd_input}")
    elif not isinstance(jd_input, dict):
        raise ValueError(f"JD input must be file path (string) or JSON data (dict), got {type(jd_input)}")
    # ✅ FIXED: Handle resumes input - accept list of file paths OR folder path
    if isinstance(resumes_input, str):
        if resumes_input.endswith('.json'):
            if not os.path.exists(resumes_input):
                raise ValueError(f"Resumes JSON file not found: {resumes_input}")
        else:
            if not os.path.exists(resumes_input):
                raise ValueError(f"Resumes folder not found: {resumes_input}")
    elif isinstance(resumes_input, list):
        # ✅ ALLOW list of file paths (strings) OR list of dictionaries
        if resumes_input and all(isinstance(r, (str, dict)) for r in resumes_input):
            # Check if file paths exist
            for item in resumes_input:
                if isinstance(item, str) and not os.path.exists(item):
                    print(f"⚠️ Warning: File not found: {item}")
        else:
            raise ValueError("Resumes list must contain file paths (strings) or dictionary objects")
    else:
        raise ValueError(f"Resumes input must be folder path (string) or list of file paths, got {type(resumes_input)}")
    return True

def faiss_retrieve(jd_embedding, resume_embeddings, top_n):
    try:
        d = resume_embeddings.shape[1]
        index = faiss.IndexFlatIP(d)
        faiss.normalize_L2(resume_embeddings)
        faiss.normalize_L2(jd_embedding)
        index.add(resume_embeddings)
        distances, indices = index.search(jd_embedding, top_n)
        return distances[0], indices[0]
    finally:
        if 'index' in locals():
            del index

def compute_skill_overlap(jd_skills, resume_skills):
    if not jd_skills or not resume_skills: return 0.0
    jd_set = set([s.lower().strip() for s in jd_skills])
    resume_set = set([s.lower().strip() for s in resume_skills])
    matches = jd_set.intersection(resume_set)
    return len(matches) / len(jd_set) if jd_set else 0.0

def compute_exp_match(jd_exp, resume_exp):
    if jd_exp <= 0: return 1.0
    return min(resume_exp / jd_exp, 1.0)

def compute_hybrid_score(jd_emb, resume_emb, skill_overlap, exp_match):
    cosine_sim = float(np.dot(jd_emb, resume_emb) / (np.linalg.norm(jd_emb) * np.linalg.norm(resume_emb) + 1e-8))
    return 0.7 * cosine_sim + 0.2 * skill_overlap + 0.1 * exp_match

def template_rejection(jd_skills, resume_skills, jd_exp, resume_exp, score):
    jd_set = set([s.lower().strip() for s in jd_skills])
    resume_set = set([s.lower().strip() for s in resume_skills])
    missing_skills = jd_set - resume_set
    exp_gap = jd_exp - resume_exp
    skill_ratio = len(jd_set & resume_set) / len(jd_set) if jd_set else 0
    if skill_ratio < 0.3 and exp_gap > 2:
        reason = f"Low skill alignment ({skill_ratio:.0%}) + {exp_gap:.1f}y experience gap"
    elif skill_ratio < 0.4:
        reason = f"Missing {len(missing_skills)} key skills"
    elif exp_gap > 2:
        reason = f"Experience gap: {resume_exp}y vs required {jd_exp}y"
    elif score < 0.5:
        reason = "Overall profile doesn't strongly align"
    else:
        reason = "Other candidates demonstrated stronger alignment"
    return f"Not selected: {reason}"

def deepseek_profile_summary_llm(parsed_resume: dict, jd_data: dict = None) -> str:
    """
    Generate a structured HR-style candidate profile summary
    using ONLY extracted fields from Step-8 pipeline.
    """

    skills = parsed_resume.get("skills", [])
    experience = parsed_resume.get("experience", 0)
    certifications = parsed_resume.get("certifications", [])
    achievements = parsed_resume.get("achievements", [])
    education = parsed_resume.get("education", [])

    jd_skills = jd_data.get("skills", []) if jd_data else []
    jd_education = jd_data.get("education", []) if jd_data else []

    prompt = f"""
You are an HR screening assistant.

Write a concise, factual candidate profile summary
using ONLY the structured data provided.

Candidate Information:
- skills: {skills}
- experience (years): {experience}
- certifications: {certifications}
- achievements: {achievements}
- education: {education}

Job Requirements:
- Required Skills: {jd_skills}
- Preferred Education: {jd_education}

Rules:
- Do NOT assume or hallucinate
- Do NOT invent job titles or experience
- Use short professional sentences
"""

    return generate_deepseek_response(
        prompt=prompt,
        temperature=0.3,
        max_tokens=180
    )

def deepseek_explanation(jd_text, resume_summary, score):
    # TODO: Replace with actual DeepSeek API
    if score > 0.8:
        return "Excellent match: Candidate possesses all key required skills and exceeds experience requirements."
    elif score > 0.6:
        return "Good fit: Core skills and experience align well with position requirements."
    else:
        return "Reasonable match: Shows relevant background and some required skills."

def integrate_with_step8(step8_output, category_filter=None):
    processed_resumes = []
    for resume in step8_output.get("processed_resumes_data", []):
        # ---- safe key mapping with fallbacks ----
        skills = (
            resume.get("skills")
            or resume.get("Skills")
            or resume.get("ExtractedSkills")
            or resume.get("SkillEntities")
            or []
        )

        experience = (
            resume.get("experience")
            or resume.get("Experience")
            or resume.get("TotalExperience")
            or resume.get("WorkExperienceYears")
            or 0
        )

        certifications = (
            resume.get("certifications")
            or resume.get("Certifications")
            or resume.get("Certificates")
            or []
        )

        achievements = (
            resume.get("achievements")
            or resume.get("Achievements")
            or resume.get("Accomplishments")
            or []
        )

        education = (
            resume.get("education")
            or resume.get("Education")
            or resume.get("Degrees")
            or resume.get("ParsedEducation")
            or []
        )
        resume_data = {
            'id': resume.get("ResumeID", f"candidate_{uuid.uuid4().hex[:8]}"),
            'full_text': resume.get("RedactedText", ""),
            'category': resume.get("Category", "Unknown"),
            'parsed': {
                "skills": skills,
                "experience": experience,
                "certifications": certifications,
                "achievements": achievements,
                "education": education,
            }
        }
        if not category_filter or resume_data['category'] == category_filter:
            processed_resumes.append(resume_data)
    return processed_resumes

def parse_jd_with_step8(step8_output):
    processed_jds = step8_output.get("processed_jds", [])
    if not processed_jds: return {"text": "", "skills": [], "experience": 0}
    jd_data = processed_jds[0]
    return {
        'text': jd_data.get("JobDescription", ""),
        'skills': jd_data.get("Skills", []),
        'experience': jd_data.get("Experience", 0)
    }

# Cell 4: SIMPLIFIED EXPLANATION SYSTEM
def deepseek_highlight(jd_text: str, resume_text: str) -> str:
    """Extract highlights only from professional sections"""
    # Split resume into sections
    sections = {
        'projects': [],
        'experience': [],
        'skills': [],
        'achievements': []
    }
    current_section = None
    lines = resume_text.split('\n')
    for line in lines:
        line_clean = line.strip().lower()
        # Detect section headers
        if any(keyword in line_clean for keyword in ['project', 'experience', 'work', 'intern']):
            current_section = 'projects'
        elif 'skill' in line_clean:
            current_section = 'skills'
        elif any(keyword in line_clean for keyword in ['achievement', 'accomplishment']):
            current_section = 'achievements'
        elif line_clean and current_section:
            # Add content to current section
            if len(line.strip()) > 20:  # Meaningful content
                sections[current_section].append(line.strip())
    # Build highlights from
    # professional sections only
    highlights = []
    # Get from projects/experience first
    for item in sections['projects'][:2]:
        highlights.append(item)
    # Fallback to achievements
    if not highlights and sections['achievements']:
        highlights.extend(sections['achievements'][:2])
    return ' | '.join(highlights) if highlights else "Relevant professional experience"

import random

def llm_generate_rejection(jd_skills: list, resume_skills: list, jd_exp: float, resume_exp: float) -> str:
    """Generate rejection reason based on skill and experience gaps"""
    jd_set = set([s.lower().strip() for s in jd_skills])
    resume_set = set([s.lower().strip() for s in resume_skills])
    matched_skills = jd_set.intersection(resume_set)
    missing_skills = jd_set - resume_set
    exp_gap = jd_exp - resume_exp
    
    # Build rejection reason based on gaps
    reasons = []
    
    # Skill-focused reasons with multiple variations (2+ sentences each)
    if len(matched_skills) < len(jd_set) * 0.4:  # Less than 40% skills matched
        skill_match_percent = (len(matched_skills) / len(jd_set)) * 100 if jd_set else 0
        
        skill_reasons = [
            # Missing skills variations
            f"Your application demonstrates a gap in several key technical areas required for this role. Specifically, we're looking for stronger experience with {', '.join(list(missing_skills)[:min(3, len(missing_skills))])}, which weren't sufficiently highlighted in your profile.",
            
            f"We've reviewed your technical background and found it lacks some core competencies essential for this position. The role requires demonstrated expertise in areas such as {', '.join(list(missing_skills)[:min(3, len(missing_skills))])}, which weren't evident in your application materials.",
            
            f"While you have relevant experience in some areas, your profile doesn't fully align with our technical requirements. We're seeking candidates with more comprehensive skills including {', '.join(list(missing_skills)[:min(2, len(missing_skills))])} to succeed in this position.",
            
            f"Our evaluation indicates your skill set doesn't provide the complete technical coverage needed for this role. The position demands proficiency in {len(missing_skills)} key areas that weren't sufficiently demonstrated in your application.",
            
            # Skill percentage variations
            f"Your technical qualifications show only {skill_match_percent:.0f}% alignment with our role requirements. For this position, we need candidates with a stronger match across our core technology stack and methodologies.",
            
            f"We assessed your skills against our requirements and found limited overlap in several critical areas. With only {skill_match_percent:.0f}% of required competencies demonstrated, other candidates presented more comprehensive technical backgrounds.",
            
            f"The role demands a specific technical profile that your application doesn't fully match. Your {skill_match_percent:.0f}% skill alignment falls below our threshold for advancing to the next stage of consideration.",
            
            # General skill misalignment
            f"Your professional background doesn't demonstrate the specific technical expertise we require for this position. We're seeking candidates whose skills more directly correspond to our technology stack and project requirements.",
            
            f"After careful review, we've determined your technical qualifications don't align closely enough with our current needs. The role requires specialized skills that weren't sufficiently evident in your application materials.",
        ]
        
        # Choose a random skill reason
        skill_reason = random.choice(skill_reasons)
        
        # Sometimes add experience mention as a separate sentence
        if 1 < exp_gap <= 3 and random.random() < 0.4:  # 40% chance to add experience mention
            exp_additions = [
                f" Additionally, we're seeking candidates with more direct experience in this specific domain.",
                f" This is compounded by our need for candidates with slightly more relevant professional background.",
                f" Combined with our preference for candidates having more extensive practical application of these skills.",
            ]
            skill_reason += random.choice(exp_additions)
                
        reasons.append(skill_reason)
    
    # Experience reasons (as separate, complete sentences)
    if exp_gap > 2:
        exp_reasons = [
            f"While your background is valuable, this role requires {jd_exp} years of specialized experience. With your {resume_exp} years in the field, we're pursuing candidates whose professional tenure more closely matches our requirements.",
            
            f"We're seeking applicants with more extensive experience in this particular domain. Your {resume_exp} years of background, while relevant, doesn't meet our threshold of {jd_exp} years for this seniority level.",
            
            f"The position demands candidates with deeper industry experience than your current {resume_exp} years provides. We've identified other applicants whose {jd_exp}+ years of relevant experience better aligns with our needs.",
        ]
        
        # Add experience reason if not already heavily focused on skills
        if not reasons or (exp_gap > 3 and random.random() < 0.6):  # Higher chance for large experience gaps
            reasons.append(random.choice(exp_reasons))
    
    if not reasons:  # Fallback if no clear reason
        fallback_reasons = [
            "After reviewing all applications, we've identified other candidates whose qualifications more closely match our specific requirements. Their backgrounds demonstrated stronger alignment with both our technical needs and team dynamics.",
            
            "We appreciate your interest in this position, but we're pursuing candidates whose profiles show a more direct correlation to our current needs. Other applicants presented more comprehensive alignment with our role specifications.",
            
            "While your background has merit, we've found other candidates whose experience and skills more precisely fit our requirements. Their applications demonstrated stronger synergy with both our technical stack and project objectives.",
            
            "Our selection process identified several candidates with qualifications that more comprehensively address our position requirements. We're moving forward with applicants whose profiles show optimal alignment across all evaluation criteria.",
        ]
        reasons.append(random.choice(fallback_reasons))
    
    # Combine reasons with proper formatting
    if len(reasons) == 1:
        return f"Not selected: {reasons[0]}"
    else:
        # Join multiple reasons with proper paragraph breaks
        combined = " ".join(reasons)
        return f"Not selected: {combined}"

print("✅ Steps 9-11 Functions loaded!")

def rank_resumes(jd_embedding, resume_embeddings, jd_skills, jd_exp, resumes_data, top_n=10):
    """
    Rank resumes based on embeddings, skill overlap, and experience match.
    Returns list of dicts with resume index, score, and reason.
    """
    scores = []
    distances, indices = faiss_retrieve(jd_embedding, resume_embeddings, top_n)
    
    for rank, idx in enumerate(indices):
        resume = resumes_data[idx]
        resume_emb = resume_embeddings[idx]
        skill_overlap = compute_skill_overlap(jd_skills, resume.get("skills", []))
        exp_match = compute_exp_match(jd_exp, resume.get("experience", 0))
        hybrid_score = compute_hybrid_score(jd_embedding[0], resume_emb, skill_overlap, exp_match)
        rejection_reason = template_rejection(jd_skills, resume.get("skills", []), jd_exp, resume.get("experience", 0), hybrid_score)
        scores.append({
            "ResumeIndex": idx,
            "ResumeID": resume.get("ResumeID", f"candidate_{uuid.uuid4().hex[:8]}"),
            "Score": round(hybrid_score, 3),
            "RejectionReason": rejection_reason
        })
    # Sort by Score descending
    scores = sorted(scores, key=lambda x: x["Score"], reverse=True)
    return scores[:top_n]
