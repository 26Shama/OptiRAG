# JDExtractor.py

import os
import json
import docx
import PyPDF2
import pandas as pd
from typing import Dict, Any, List, Union
from pathlib import Path
from fastapi import HTTPException  # Added for FastAPI error handling


# 4️⃣ JD Extraction
class JDExtractor:
    """
    A class to extract job description text from various file formats
    and combine with HR-provided metadata into standardized JSON format.
    """

    def __init__(self):
        self.supported_formats = ['.pdf', '.docx', '.txt', '.json', '.csv']

    def extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF files"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading PDF file: {str(e)}")

    def extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX files"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading DOCX file: {str(e)}")

    def extract_from_txt(self, file_path: str) -> str:
        """Extract text from TXT files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading TXT file: {str(e)}")

    def extract_from_json(self, file_path: str) -> Dict[str, Any]:
        """Extract data from JSON files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading JSON file: {str(e)}")

    def extract_from_csv(self, file_path: str) -> pd.DataFrame:
        """Extract data from CSV files"""
        try:
            return pd.read_csv(file_path, encoding='utf-8', errors='ignore')
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading CSV file: {str(e)}")

    def process_file(self, file_path: str, JobID: str, JobTitle: str, Category: str) -> Dict[str, Any]:
        file_extension = Path(file_path).suffix.lower()

        if file_extension == '.pdf':
            content = self.extract_from_pdf(file_path)
        elif file_extension == '.docx':
            content = self.extract_from_docx(file_path)
        elif file_extension == '.txt':
            content = self.extract_from_txt(file_path)
        elif file_extension == '.json':
            json_data = self.extract_from_json(file_path)
            return self.process_json_data(json_data, JobID, JobTitle, Category)
        elif file_extension == '.csv':
            csv_data = self.extract_from_csv(file_path)
            return self.process_csv_data(csv_data, JobID, JobTitle, Category)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file format: {file_extension}")

        return {
            'JobID': JobID,
            'JobTitle': JobTitle,
            'Category': Category,
            'JobDescription': content
        }

    def process_json_data(self, json_data: Union[Dict, List], JobID: str, JobTitle: str, Category: str):
        results = []
        if isinstance(json_data, list):
            for item in json_data:
                result = {
                    'JobID': item.get('JobID', JobID),
                    'JobTitle': item.get('JobTitle', JobTitle),
                    'Category': item.get('Category', Category),
                    'JobDescription': item.get('JobDescription', '') or item.get('description', '')
                }
                results.append(result)
            return results

        return {
            'JobID': json_data.get('JobID', JobID),
            'JobTitle': json_data.get('JobTitle', JobTitle),
            'Category': json_data.get('Category', Category),
            'JobDescription': json_data.get('JobDescription', '') or json_data.get('description', '')
        }

    def process_csv_data(self, csv_data: pd.DataFrame, JobID: str, JobTitle: str, Category: str) -> List[Dict[str, Any]]:
        results = []

        description_columns = ['JobDescription', 'description', 'jd', 'job_desc']
        description_col = None

        for col in description_columns:
            if col in csv_data.columns:
                description_col = col
                break

        for _, row in csv_data.iterrows():
            jobid_columns = ['JobID', 'JobId', 'jobid', 'Job ID', 'Job id', 'Job Id']
            row_JobID = None
            for col in jobid_columns:
                if col in csv_data.columns and pd.notna(row.get(col)):
                    row_JobID = row.get(col)
                    break

            if row_JobID is None:
                row_JobID = JobID
            row_JobTitle = row.get('JobTitle', JobTitle)
            row_Category = row.get('Category', Category)

            description = row.get(description_col, "")
            description = "" if pd.isna(description) else str(description)

            result = {
                'JobID': row_JobID,
                'JobTitle': row_JobTitle,
                'Category': row_Category,
                'JobDescription': description
            }
            results.append(result)

        return results

    def process_direct_text(self, text: str, JobID: str, JobTitle: str, Category: str) -> Dict[str, Any]:
        return {
            'JobID': JobID,
            'JobTitle': JobTitle,
            'Category': Category,
            'JobDescription': text
        }

    def to_json(self, data: Union[Dict, List]) -> str:
        if isinstance(data, list):
            return json.dumps(data, indent=2)
        else:
            return json.dumps([data], indent=2)

# 🔹 Module-level wrapper functions for FastAPI / service imports

def extract_jd(file_paths: list, JobID: str = "", JobTitle: str = "", Category: str = "") -> list:
    """
    Wrapper function to extract job descriptions from multiple files.

    Args:
        file_paths (list): List of file paths (PDF, DOCX, TXT, CSV, JSON).
        JobID (str): Default JobID to assign if not present in file.
        JobTitle (str): Default JobTitle to assign if not present in file.
        Category (str): Default Category to assign if not present in file.

    Returns:
        list: List of standardized JD dicts.
    """
    extractor = JDExtractor()
    extracted_jds = []

    for file_path in file_paths:
        result = extractor.process_file(file_path, JobID, JobTitle, Category)

        # If result is a list (from CSV/JSON with multiple rows)
        if isinstance(result, list):
            extracted_jds.extend(result)
        else:
            extracted_jds.append(result)

    return extracted_jds


def extract_jd_from_text(text: str, JobID: str, JobTitle: str, Category: str) -> dict:
    """
    Wrapper to process direct job description text instead of files.

    Args:
        text (str): Job description text
        JobID (str): Job ID
        JobTitle (str): Job title
        Category (str): Job category

    Returns:
        dict: Standardized JD dictionary
    """
    extractor = JDExtractor()
    return extractor.process_direct_text(text, JobID, JobTitle, Category)
