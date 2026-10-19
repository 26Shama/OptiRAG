import requests
import streamlit as st

# -----------------------------
# BASE URL OF FASTAPI BACKEND
# -----------------------------
# Example: "http://localhost:8000"
API_BASE = st.secrets.get("API_BASE_URL", "http://127.0.0.1:8000")


# -----------------------------
# Helper function for handling responses
# -----------------------------
def handle_response(res):
    try:
        return res.json()
    except:
        return {"status": "error", "message": "Invalid response from server"}


# -----------------------------
# LOGIN API
# -----------------------------
def api_login(email: str, password: str):
    url = f"{API_BASE}/auth/login"

    payload = {
        "email": email,
        "password": password
    }

    try:
        res = requests.post(url, json=payload)
        data = handle_response(res)
        return data

    except Exception as e:
        return {"status": "error", "message": f"Server error: {str(e)}"}


# -----------------------------
# SIGNUP API
# -----------------------------
def api_signup(name: str, email: str, password: str):
    url = f"{API_BASE}/auth/signup"

    payload = {
        "name": name,
        "email": email,
        "password": password
    }

    try:
        res = requests.post(url, json=payload)
        data = handle_response(res)
        return data

    except Exception as e:
        return {"status": "error", "message": f"Server error: {str(e)}"}


# -----------------------------
# GENERIC API CALL (POST)
# For uploads, screening, email automation etc.
# -----------------------------
def api_post(endpoint: str, payload: dict, files=None):
    url = f"{API_BASE}{endpoint}"

    headers = {}   # ❌ REMOVED token/Authorization handling

    try:
        res = requests.post(url, json=payload, headers=headers, files=files)
        return handle_response(res)
    except Exception as e:
        return {"status": "error", "message": str(e)}


# -----------------------------
# GENERIC API CALL (GET)
# -----------------------------
def api_get(endpoint: str):
    url = f"{API_BASE}{endpoint}"

    headers = {}   # ❌ REMOVED token/Authorization handling

    try:
        res = requests.get(url, headers=headers)
        return handle_response(res)
    except Exception as e:
        return {"status": "error", "message": str(e)}
