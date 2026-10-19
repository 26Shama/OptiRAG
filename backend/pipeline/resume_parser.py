import re
import spacy
from datetime import datetime
from typing import List, Dict, Any
from spacy.matcher import PhraseMatcher, Matcher
from fastapi import HTTPException

# Uses globally initialized NLP + matcher from initialization file
from ..pipeline.nlp_init import nlp, skill_matcher


# 3️⃣ NLP Resume Parsing
class ResumeParser:
    def __init__(self):
        import spacy

        if nlp is None:
            print("⚠️ Global NLP not initialized, loading locally...")
            self.nlp = spacy.load("en_core_web_md")
        else:
            self.nlp = nlp

        self.matcher = PhraseMatcher(self.nlp.vocab)
        self.pattern_matcher = Matcher(self.nlp.vocab)

        self._initialize_certification_matcher()
        self._initialize_title_patterns()


    def _initialize_certification_matcher(self):
        """Initialize certification patterns"""
        certifications = [
            # Cloud & DevOps Certifications
            "AWS Certified", "Azure Certified", "Google Cloud Certified", "Kubernetes Certified", "Docker Certified",
            "AWS Solutions Architect", "AWS Developer", "AWS SysOps", "AWS DevOps",
            "Azure Administrator", "Azure Developer", "Azure Solutions Architect",
            "Google Cloud Architect", "Google Cloud Engineer", "Google Cloud Developer",

            # Project Management Certifications
            "PMP", "PMI", "PRINCE2", "CAPM", "Agile", "Scrum Master", "CSM", "PSM",

            # Security Certifications
            "CISSP", "CISA", "CISM", "CEH", "Security+", "CompTIA Security", "GSEC", "OSCP",
            "CCNA Security", "CCNP Security", "CCIE Security",

            # Networking Certifications
            "CCNA", "CCNP", "CCIE", "CCDA", "CCDP", "JNCIA", "JNCIS", "JNCIE",
            "Network+", "CompTIA Network",

            # IT Infrastructure Certifications
            "ITIL", "COBIT", "TOGAF", "VMware Certified", "Red Hat Certified", "RHCE", "RHCSA",

            # Database Certifications
            "Oracle Certified", "MongoDB Certified", "MySQL Certified", "PostgreSQL Certified",
            "Oracle DBA", "Oracle Developer", "Microsoft SQL Server Certified",

            # Software Development Certifications
            "Microsoft Certified", "Java Certified", "Python Certified", "AWS Certified Developer",
            "Microsoft Azure Developer", "Google Cloud Developer",

            # Data Science & AI Certifications
            "TensorFlow Developer", "Google Cloud Data Engineer", "AWS Data Analytics",
            "Microsoft Data Analyst", "Cloudera Certified", "Data Science Council of America",

            # Finance Certifications
            "CFA", "Chartered Financial Analyst", "CPA", "Certified Public Accountant",
            "FRM", "Financial Risk Manager", "CA", "Chartered Accountant",
            "CMA", "Certified Management Accountant", "CIMA", "ACCA",
            "Series 7", "Series 63", "Series 65", "Series 66",
            "CFP", "Certified Financial Planner", "ChFC", "Chartered Financial Consultant",
            "PRM", "Professional Risk Manager", "ERP", "Enterprise Risk Professional",
            "CVA", "Certified Valuation Analyst", "ABV", "Accredited in Business Valuation",
            "CFE", "Certified Fraud Examiner", "CIA", "Certified Internal Auditor",
            "CRMA", "Certification in Risk Management Assurance",

            # Banking Certifications
            "CIPM", "Certificate in Investment Performance",
            "CAIA", "Chartered Alternative Investment Analyst",

            # Six Sigma & Quality Certifications
            "Six Sigma", "Lean Six Sigma", "Black Belt", "Green Belt", "Yellow Belt",
            "CQE", "Certified Quality Engineer", "CQA", "Certified Quality Auditor",

            # Compliance Certifications
            "CRCM", "Certified Regulatory Compliance Manager", "CAMS", "Certified Anti-Money Laundering",
            "CFCS", "Certified Financial Crime Specialist"
        ]

        patterns = [self.nlp.make_doc(cert) for cert in certifications]
        self.matcher.add("CERTIFICATIONS", patterns)

    def _initialize_title_patterns(self):
        """Initialize comprehensive job title patterns for IT and Finance"""
        title_patterns = [
            # IT - Engineering & Development
            [{"LOWER": {"in": ["senior", "lead", "principal", "staff"]}}, {"LOWER": "software"}, {"LOWER": "engineer"}],
            [{"LOWER": {"in": ["junior", "associate", "entry"]}}, {"LOWER": "software"}, {"LOWER": "engineer"}],
            [{"LOWER": "software"}, {"LOWER": "engineer"}],
            [{"LOWER": "software"}, {"LOWER": "developer"}],
            [{"LOWER": "web"}, {"LOWER": "developer"}],
            [{"LOWER": "frontend"}, {"LOWER": "developer"}],
            [{"LOWER": "backend"}, {"LOWER": "developer"}],
            [{"LOWER": "full"}, {"LOWER": "stack"}, {"LOWER": "developer"}],
            [{"LOWER": "mobile"}, {"LOWER": "developer"}],
            [{"LOWER": "android"}, {"LOWER": "developer"}],
            [{"LOWER": "ios"}, {"LOWER": "developer"}],
            [{"LOWER": "python"}, {"LOWER": "developer"}],
            [{"LOWER": "java"}, {"LOWER": "developer"}],
            [{"LOWER": "javascript"}, {"LOWER": "developer"}],

            # IT - Data & AI
            [{"LOWER": "data"}, {"LOWER": "scientist"}],
            [{"LOWER": "data"}, {"LOWER": "analyst"}],
            [{"LOWER": "data"}, {"LOWER": "engineer"}],
            [{"LOWER": "machine"}, {"LOWER": "learning"}, {"LOWER": "engineer"}],
            [{"LOWER": "ai"}, {"LOWER": "engineer"}],
            [{"LOWER": "business"}, {"LOWER": "intelligence"}, {"LOWER": "analyst"}],
            [{"LOWER": "bi"}, {"LOWER": "analyst"}],

            # IT - DevOps & Cloud
            [{"LOWER": "devops"}, {"LOWER": "engineer"}],
            [{"LOWER": "cloud"}, {"LOWER": "engineer"}],
            [{"LOWER": "site"}, {"LOWER": "reliability"}, {"LOWER": "engineer"}],
            [{"LOWER": "sre"}],
            [{"LOWER": "systems"}, {"LOWER": "administrator"}],
            [{"LOWER": "sysadmin"}],
            [{"LOWER": "network"}, {"LOWER": "engineer"}],
            [{"LOWER": "network"}, {"LOWER": "administrator"}],

            # IT - Security
            [{"LOWER": "security"}, {"LOWER": "engineer"}],
            [{"LOWER": "cyber"}, {"LOWER": "security"}, {"LOWER": "analyst"}],
            [{"LOWER": "information"}, {"LOWER": "security"}, {"LOWER": "analyst"}],

            # IT - Database
            [{"LOWER": "database"}, {"LOWER": "administrator"}],
            [{"LOWER": "dba"}],
            [{"LOWER": "sql"}, {"LOWER": "developer"}],

            # IT - Management
            [{"LOWER": "technical"}, {"LOWER": "lead"}],
            [{"LOWER": "team"}, {"LOWER": "lead"}],
            [{"LOWER": "engineering"}, {"LOWER": "manager"}],
            [{"LOWER": "development"}, {"LOWER": "manager"}],
            [{"LOWER": "it"}, {"LOWER": "manager"}],
            [{"LOWER": "cto"}],
            [{"LOWER": "cio"}],

            # IT - Architecture
            [{"LOWER": "solution"}, {"LOWER": "architect"}],
            [{"LOWER": "system"}, {"LOWER": "architect"}],
            [{"LOWER": "software"}, {"LOWER": "architect"}],
            [{"LOWER": "enterprise"}, {"LOWER": "architect"}],
            [{"LOWER": "cloud"}, {"LOWER": "architect"}],

            # IT - QA & Testing
            [{"LOWER": "quality"}, {"LOWER": "assurance"}, {"LOWER": "engineer"}],
            [{"LOWER": "qa"}, {"LOWER": "engineer"}],
            [{"LOWER": "test"}, {"LOWER": "engineer"}],
            [{"LOWER": "automation"}, {"LOWER": "engineer"}],

            # IT - Design
            [{"LOWER": "ui"}, {"LOWER": "designer"}],
            [{"LOWER": "ux"}, {"LOWER": "designer"}],
            [{"LOWER": "product"}, {"LOWER": "designer"}],

            # IT - Product & Project Management
            [{"LOWER": "product"}, {"LOWER": "manager"}],
            [{"LOWER": "project"}, {"LOWER": "manager"}],
            [{"LOWER": "program"}, {"LOWER": "manager"}],
            [{"LOWER": "scrum"}, {"LOWER": "master"}],
            [{"LOWER": "agile"}, {"LOWER": "coach"}],

            # IT - Business Analysis
            [{"LOWER": "business"}, {"LOWER": "analyst"}],
            [{"LOWER": "systems"}, {"LOWER": "analyst"}],
            [{"LOWER": "it"}, {"LOWER": "analyst"}],

            # FINANCE - Accounting
            [{"LOWER": "accountant"}],
            [{"LOWER": "senior"}, {"LOWER": "accountant"}],
            [{"LOWER": "staff"}, {"LOWER": "accountant"}],
            [{"LOWER": "cost"}, {"LOWER": "accountant"}],
            [{"LOWER": "tax"}, {"LOWER": "accountant"}],
            [{"LOWER": "auditor"}],
            [{"LOWER": "internal"}, {"LOWER": "auditor"}],
            [{"LOWER": "financial"}, {"LOWER": "auditor"}],

            # FINANCE - Analysis
            [{"LOWER": "financial"}, {"LOWER": "analyst"}],
            [{"LOWER": "senior"}, {"LOWER": "financial"}, {"LOWER": "analyst"}],
            [{"LOWER": "investment"}, {"LOWER": "analyst"}],
            [{"LOWER": "equity"}, {"LOWER": "analyst"}],
            [{"LOWER": "research"}, {"LOWER": "analyst"}],
            [{"LOWER": "credit"}, {"LOWER": "analyst"}],
            [{"LOWER": "risk"}, {"LOWER": "analyst"}],

            # FINANCE - Management
            [{"LOWER": "finance"}, {"LOWER": "manager"}],
            [{"LOWER": "financial"}, {"LOWER": "manager"}],
            [{"LOWER": "accounting"}, {"LOWER": "manager"}],
            [{"LOWER": "tax"}, {"LOWER": "manager"}],
            [{"LOWER": "audit"}, {"LOWER": "manager"}],
            [{"LOWER": "treasury"}, {"LOWER": "manager"}],
            [{"LOWER": "cfo"}],
            [{"LOWER": "controller"}],

            # FINANCE - Banking
            [{"LOWER": "investment"}, {"LOWER": "banker"}],
            [{"LOWER": "relationship"}, {"LOWER": "manager"}],
            [{"LOWER": "credit"}, {"LOWER": "manager"}],
            [{"LOWER": "branch"}, {"LOWER": "manager"}],
            [{"LOWER": "loan"}, {"LOWER": "officer"}],

            # FINANCE - Advisory & Planning
            [{"LOWER": "financial"}, {"LOWER": "advisor"}],
            [{"LOWER": "wealth"}, {"LOWER": "manager"}],
            [{"LOWER": "investment"}, {"LOWER": "advisor"}],
            [{"LOWER": "portfolio"}, {"LOWER": "manager"}],

            # FINANCE - Treasury & Risk
            [{"LOWER": "treasury"}, {"LOWER": "analyst"}],
            [{"LOWER": "risk"}, {"LOWER": "manager"}],
            [{"LOWER": "compliance"}, {"LOWER": "officer"}],
            [{"LOWER": "internal"}, {"LOWER": "control"}],

            # FINANCE - Corporate Finance
            [{"LOWER": "corporate"}, {"LOWER": "finance"}],
            [{"LOWER": "fp&a"}, {"LOWER": "analyst"}],
            [{"LOWER": "financial"}, {"LOWER": "planning"}, {"LOWER": "analyst"}],

            # Single word titles
            [{"LOWER": "architect"}],
            [{"LOWER": "consultant"}],
            [{"LOWER": "specialist"}],
            [{"LOWER": "coordinator"}],
            [{"LOWER": "associate"}],
        ]

        for i, pattern in enumerate(title_patterns):
            self.pattern_matcher.add(f"TITLE_{i}", [pattern])

    def extract_experience_years(self, text: str) -> float:
        """FIXED VERSION - Calculate total years of experience from all roles"""
        
        total_years = 0.0
        current_year = datetime.now().year
        current_month = datetime.now().month

        # Track matched positions to avoid overlapping matches
        matched_positions = []

        def is_overlapping(start, end):
            """Check if position overlaps with already matched text"""
            for m_start, m_end in matched_positions:
                if not (end <= m_start or start >= m_end):
                    return True
            return False

        def add_match(start, end, years):
            """Add a match if it doesn't overlap and is valid"""
            nonlocal total_years
            if not is_overlapping(start, end) and 0.1 <= years <= 40:
                matched_positions.append((start, end))
                total_years += years
                return True
            return False

        def calculate_months_duration(start_month, start_year, end_month, end_year):
            """Calculate duration in years between two dates"""
            start_total_months = start_year * 12 + start_month
            end_total_months = end_year * 12 + end_month
            duration = (end_total_months - start_total_months) / 12.0
            return max(0, duration)

        # Priority 1: Date ranges with months (most accurate)
        patterns_priority_1 = [
            # MM-YYYY to MM-YYYY or MM/YYYY to MM/YYYY
            (r'(\d{1,2})[-/](\d{4})\s*(?:to|[-–—])\s*(\d{1,2})[-/](\d{4})',
             lambda m: calculate_months_duration(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)))),

            # Parentheses: (MM-YYYY to MM-YYYY)
            (r'\((\d{1,2})[-/](\d{4})\s*(?:to|[-–—])\s*(\d{1,2})[-/](\d{4})\)',
             lambda m: calculate_months_duration(int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)))),

            # MM-YYYY to present/current/now
            (r'(\d{1,2})[-/](\d{4})\s*(?:to|[-–—])\s*(?:present|current|now)',
             lambda m: calculate_months_duration(int(m.group(1)), int(m.group(2)), current_month, current_year)),

            # Parentheses: (MM-YYYY to present)
            (r'\((\d{1,2})[-/](\d{4})\s*(?:to|[-–—])\s*(?:present|current|now)\)',
             lambda m: calculate_months_duration(int(m.group(1)), int(m.group(2)), current_month, current_year)),

            # Month YYYY to Month YYYY
            (r'(\w+)\s+(\d{4})\s*(?:to|[-–—])\s*(\w+)\s+(\d{4})',
             lambda m: calculate_months_duration(self._month_to_number(m.group(1)), int(m.group(2)),
                                               self._month_to_number(m.group(3)), int(m.group(4)))),
        ]

        for pattern, calc_func in patterns_priority_1:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                try:
                    years = calc_func(match)
                    if years > 0:
                        add_match(match.start(), match.end(), years)
                except (ValueError, TypeError, IndexError):
                    continue

        # Priority 2: Year ranges (only if no Priority 1 matches)
        if total_years == 0:
            patterns_priority_2 = [
                (r'(\d{4})\s*(?:to|[-–—])\s*(\d{4})',
                 lambda m: min(int(m.group(2)), current_year) - int(m.group(1))),
            ]

            for pattern, calc_func in patterns_priority_2:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    try:
                        years = calc_func(match)
                        if 0 < years <= 40:
                            add_match(match.start(), match.end(), years)
                    except (ValueError, TypeError):
                        continue

        # Priority 3: Explicit years at companies (only if no Priority 1-2)
        if total_years == 0:
            patterns_priority_3 = [
                (r'(\d+\.?\d*)\s+(?:years?|yrs?)\s+(?:at|in|with)\s+[A-Za-z&]',
                 lambda m: float(m.group(1))),
                (r'(\d+\.?\d*)[\+]?\s+(?:years?|yrs?)(?:\s+of)?\s+(?:experience\s+)?(?:at|in|with)\s+[A-Za-z&]',
                 lambda m: float(m.group(1))),
                (r'(?:worked|served)(?:\s+for)?\s+(\d+\.?\d*)\s+(?:years?|yrs?)\s+(?:at|in|with)',
                 lambda m: float(m.group(1))),
                (r'(\d+\.?\d*)\s+(?:years?|yrs?)\s*[:\-–—]\s*[A-Za-z&]',
                 lambda m: float(m.group(1))),
            ]

            for pattern, calc_func in patterns_priority_3:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    try:
                        years = calc_func(match)
                        if 0.1 <= years <= 25:
                            add_match(match.start(), match.end(), years)
                    except (ValueError, TypeError):
                        continue

        # Priority 4: General experience (fallback)
        if total_years == 0:
            patterns_priority_4 = [
                (r'(?:total\s+)?experience\s*:\s*(\d+\.?\d*)\s+(?:years?|yrs?)',
                 lambda m: float(m.group(1))),
                (r'(\d+\.?\d*)[\+]?\s+(?:years?|yrs?)(?:\s+of)?\s+experience',
                 lambda m: float(m.group(1))),
                (r'(\d+\.?\d*)\s+(?:years?|yrs?)\s+in\s+the\s+industry',
                 lambda m: float(m.group(1))),
            ]

            for pattern, calc_func in patterns_priority_4:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    try:
                        years = calc_func(match)
                        if 0.1 <= years <= 40:
                            add_match(match.start(), match.end(), years)
                    except (ValueError, TypeError):
                        continue

        # Final sanity check
        if total_years > 45:
            total_years = 45.0

        return round(total_years, 1)

    def _month_to_number(self, month_str: str) -> int:
        """Convert month name to number"""
        if not month_str:
            return 6

        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        return months.get(month_str.lower(), 6)

    def extract_certifications(self, doc) -> List[str]:
        """Extract professional certifications"""
        certifications = set()

        matches = self.matcher(doc)
        for match_id, start, end in matches:
            if "CERTIFICATIONS" in self.nlp.vocab.strings[match_id]:
                span = doc[start:end]
                certifications.add(span.text.title())

        return list(certifications)

    def extract_recent_titles(self, doc) -> List[str]:
        """Extract recent job titles"""
        titles = set()

        matches = self.pattern_matcher(doc)
        for match_id, start, end in matches:
            if "TITLE" in self.nlp.vocab.strings[match_id]:
                span = doc[start:end]
                titles.add(span.text.title())

        for sent in doc.sents:
            sent_lower = sent.text.lower()
            if any(word in sent_lower for word in ['experience', 'worked as', 'role', 'position', 'job title']):
                for chunk in sent.noun_chunks:
                    chunk_text = chunk.text.lower()
                    if any(title_word in chunk_text for title_word in
                          ['developer', 'engineer', 'manager', 'analyst', 'designer', 'architect', 'lead', 'specialist']):
                        titles.add(chunk.text.title())

        return list(titles)[:5]

    def extract_achievements(self, doc) -> List[str]:
        """Extract achievements using comprehensive heuristics"""
        achievements = []
        achievement_indicators = [
            'achieved', 'improved', 'increased', 'reduced', 'decreased',
            'saved', 'optimized', 'implemented', 'developed', 'created',
            'led', 'managed', 'delivered', 'completed', 'won', 'awarded',
            'spearheaded', 'pioneered', 'transformed', 'streamlined',
            'enhanced', 'maximized', 'minimized', 'accelerated',
            'achievement', 'award', 'recognition', 'accomplishment',
            'success', 'result', 'performance', 'contribution',
            'finalist', 'winner', 'top', 'ranked', 'awarded', 'recognized'
        ]

        sentences = [sent.text.strip() for sent in doc.sents]

        for sent in sentences:
            sent_lower = sent.lower()

            has_indicator = any(indicator in sent_lower for indicator in achievement_indicators)
            has_quantifiable_result = re.search(r'\d+%|\$\d+|\d+\s*(?:years?|months?|days?|times?|x)', sent_lower)
            has_bullet_point = sent.startswith(('•', '-', '*', '·'))
            has_competition = any(word in sent_lower for word in ['finalist', 'winner', 'top', 'ranked', 'competition'])
            is_achievement_section = 'achievement' in sent_lower and len(sent) < 50

            if (has_indicator and (has_quantifiable_result or has_bullet_point or has_competition)) or is_achievement_section:
                achievement = sent.strip()
                if len(achievement) > 5 and len(achievement) < 500:
                    achievements.append(achievement)
            elif has_competition and not any(section in sent_lower for section in ['education', 'experience', 'skills']):
                achievements.append(sent.strip())

        return achievements[:10]


    def parse_resume(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main parsing function that handles all fields"""
        try:
            text = resume_data.get("cleaned_text", "")
            doc = self.nlp(text)

            category_mapping = {
                "Information Technology": "IT",
                "Information Technol": "IT",
                "IT": "IT",
                "Finance": "Finance",
                "Accounting": "Finance",
            }

            original_category = resume_data.get("Category", "")
            category = category_mapping.get(original_category, original_category)

            return {
                "ResumeID": resume_data["ResumeID"],
                "Category": category,
                "skills": resume_data.get("skills", []),
                "experience": self.extract_experience_years(text),
                "education": resume_data.get("education", []),
                "certifications": self.extract_certifications(doc),
                "RecentTitles": self.extract_recent_titles(doc),
                "achievements": self.extract_achievements(doc),
            }

        except Exception as e:
            print(f"Error parsing resume {resume_data.get('ResumeID', 'unknown')}: {str(e)}")

            original_category = resume_data.get("Category", "")
            category = category_mapping.get(original_category, original_category)

            return {
                "ResumeID": resume_data["ResumeID"],
                "Category": category,
                "skills": resume_data.get("skills", []),
                "experience": 0.0,
                "education": resume_data.get("education", []),
                "certifications": [],
                "RecentTitles": [],
                "achievements": [],
            }
        
        
# 🔹 Module-level wrapper function for FastAPI / service imports
def parse_resume(resumes: list) -> list:
    """
    Wrapper function to parse a list of resumes using ResumeParser.

    Args:
        resumes (list): List of dicts, each with at least 'ResumeID' and 'cleaned_text' keys.

    Returns:
        list: List of parsed resume dicts with Skills, Degrees, Experience, etc.
    """
    parser = ResumeParser()
    parsed_resumes = []

    for resume in resumes:
        parsed_data = parser.parse_resume(resume)
        # Merge parsed fields back into original dict if needed
        resume.update(parsed_data)
        parsed_resumes.append(resume)

    return parsed_resumes
