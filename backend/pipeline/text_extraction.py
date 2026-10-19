import os
import re
import json
import uuid
import pdfplumber
import fitz  # PyMuPDF
from pdfminer.high_level import extract_text as pdfminer_extract
import docx2txt
from docx import Document
import pytesseract
from PIL import Image
import io
from tqdm import tqdm
# 1️⃣ Resume Text Extraction & Cleaning
class TextExtraction:

    # -------- CONFIGURATION -------- #
    EXTRACTION_METHODS = ['pymupdf', 'pdfplumber', 'pdfminer', 'ocr']

    # -------- REGEX PATTERNS -------- #
    EMAIL_PATTERN = r"[a-zA-Z0-9+._%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    PHONE_PATTERN = r"(?:\+?\d{1,3}[\s\-]?)?(?:\(?\d{3}\)?[\s\-]?)?\d{3}[\s\-]?\d{4}"

    # -------- TEXT EXTRACTION FUNCTIONS -------- #
    @staticmethod
    def extract_with_pymupdf(file_path):
        text = ""
        try:
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text()
            return text.strip()
        except Exception as e:
            print(f"PyMuPDF extraction failed: {e}")
            return None

    @staticmethod
    def extract_with_pdfplumber(file_path):
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()
        except Exception as e:
            print(f"PDFPlumber extraction failed: {e}")
            return None

    @staticmethod
    def extract_with_pdfminer(file_path):
        try:
            text = pdfminer_extract(file_path)
            return text.strip()
        except Exception as e:
            print(f"PDFMiner extraction failed: {e}")
            return None

    @staticmethod
    def extract_with_ocr(file_path):
        text = ""
        try:
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap()
                img_data = pix.tobytes("ppm")
                image = Image.open(io.BytesIO(img_data))
                text += pytesseract.image_to_string(image) + "\n"
            return text.strip()
        except Exception as e:
            print(f"OCR extraction failed: {e}")
            return None

    @staticmethod
    def extract_pdf_text(file_path):
        for method in TextExtraction.EXTRACTION_METHODS:
            if method == 'pymupdf':
                text = TextExtraction.extract_with_pymupdf(file_path)
            elif method == 'pdfplumber':
                text = TextExtraction.extract_with_pdfplumber(file_path)
            elif method == 'pdfminer':
                text = TextExtraction.extract_with_pdfminer(file_path)
            elif method == 'ocr':
                text = TextExtraction.extract_with_ocr(file_path)

            if text and len(text) > 50:
                print(f"Extracted with {method}")
                return text

        print("All extraction methods failed")
        return None

    @staticmethod
    def extract_docx_text(file_path):
        try:
            text = docx2txt.process(file_path)
            if text and len(text.strip()) > 50:
                return text.strip()

            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            print(f"DOCX extraction failed: {e}")
            return None

    @staticmethod
    def enhanced_clean_text(text):
        if not text:
            return ""

        email_pattern = r'\S+@\S+\.\S+'
        phone_pattern = r'[\+\(]?[1-9][0-9 .\-\(]{8,}[0-9]'
        url_pattern = r'https?://\S+'

        emails = re.findall(email_pattern, text)
        phones = re.findall(phone_pattern, text)
        urls = re.findall(url_pattern, text)

        text = re.sub(r'[^\x00-\x7F]+', ' ', text)

        formatting_patterns = [
            r'={3,}', r'\*{3,}', r'-{3,}', r'_{3,}', r'#{3,}', r'~{3,}', r'\.{3,}', r'/{3,}'
        ]
        for pattern in formatting_patterns:
            text = re.sub(pattern, ' ', text)

        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        for email in emails:
            if email not in text:
                text += f" {email}"
        for phone in phones:
            if phone not in text:
                text += f" {phone}"
        for url in urls:
            if url not in text:
                text += f" {url}"

        return text

    @staticmethod
    def extract_email(text):
        match = re.search(TextExtraction.EMAIL_PATTERN, text)
        return match.group(0) if match else None

    @staticmethod
    def extract_phone(text):
        clean_text = re.sub(r'[\(\)\-\s]', '', text)
        match = re.search(TextExtraction.PHONE_PATTERN, text)
        return match.group(0) if match else None

    @staticmethod
    def is_valid_resume(text):
        return bool(
            TextExtraction.extract_email(text) or
            TextExtraction.extract_phone(text)
        )

    # -------- FastAPI Compatible Multiple Resume Processor -------- #
    @staticmethod
    def process_uploaded_resumes(file_paths: list, category: str):
        resumes_data = []

        for file_path in file_paths:
            file_ext = os.path.splitext(file_path)[-1].lower()

            if file_ext == ".pdf":
                text = TextExtraction.extract_pdf_text(file_path)
            elif file_ext == ".docx":
                text = TextExtraction.extract_docx_text(file_path)
            else:
                continue

            if not text:
                continue

            cleaned_text = TextExtraction.enhanced_clean_text(text)
            email = TextExtraction.extract_email(cleaned_text)
            phone = TextExtraction.extract_phone(cleaned_text)
            resume_id = os.path.splitext(os.path.basename(file_path))[0]
            if email:
                resume_data = {
                    "ResumeID": resume_id,
                    "FileName": os.path.basename(file_path),
                    "Category": category,
                    "Text": cleaned_text,
                    "EmailFound": bool(email),
                    "PhoneFound": bool(phone)
                }
                resumes_data.append(resume_data)

        return resumes_data


# Wrapper required for backend compatibility
def extract_text(file_path):
    ext = os.path.splitext(file_path)[-1].lower()
    if ext == ".pdf":
        return TextExtraction.extract_pdf_text(file_path)
    elif ext == ".docx":
        return TextExtraction.extract_docx_text(file_path)
    return ""
