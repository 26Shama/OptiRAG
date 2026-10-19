# frontend/pages/rs.py
import mimetypes
import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
from components.navbar import navbar

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="Resume Screening - OptiRAG", layout="wide")

# ---------------------------------------------------------
# LOAD GLOBAL STYLES (background, etc.)
# ---------------------------------------------------------
try:
    with open("styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except:
    pass

# ---------------------------------------------------------
# ❌ REMOVED AUTH CHECK
# ---------------------------------------------------------

# ---------------------------------------------------------
# CSS (core layout fixes)
# ---------------------------------------------------------
st.markdown("""
<style>
/* Background Color */
.stApp {
    background-color: #DDBEA9;
}

/* Font Color Change - Scoped to content text ONLY to protect Navbar */
.block-container h1, 
.block-container h2, 
.block-container h3, 
.block-container h4, 
.block-container h5, 
.block-container h6, 
.block-container p, 
.block-container li,
.block-container label, 
.stTextInput label, 
.stNumberInput label, 
.stFileUploader label, 
.stTextArea label {
    color: #1e0533 !important;
}

/* White Buttons with Dark Border */
.stButton > button {
    background-color: #ffffff !important;
    color: #1e0533 !important;
    border: 2px solid #1e0533 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
.stButton > button:hover {
    background-color: #f0f0f0 !important;
    border-color: #1e0533 !important;
    color: #1e0533 !important;
}

/* White Input Fields (Text Input, Text Area, Number Input) */
div[data-baseweb="input"], 
div[data-baseweb="base-input"], 
textarea, 
input {
    background-color: #ffffff !important;
    color: #1e0533 !important;
    border-color: #1e0533 !important;
}

/* Specific fix for text area background if needed */
.stTextArea textarea {
    background-color: #ffffff !important;
    color: #1e0533 !important;
}

/* --- FILE UPLOADER STYLING --- */
/* The dropzone container */
[data-testid="stFileUploader"] section {
    background-color: #ffffff !important;
    border: 2px solid #1e0533 !important; 
}
/* The text inside the dropzone (Drag and drop...) */
[data-testid="stFileUploader"] section span, 
[data-testid="stFileUploader"] section div, 
[data-testid="stFileUploader"] section small {
    color: #1e0533 !important;
}
/* The 'Browse files' button inside the uploader */
[data-testid="stFileUploader"] button {
    background-color: #ffffff !important;
    color: #1e0533 !important;
    border: 1px solid #1e0533 !important;
}
            
section[data-testid="stHeader"] { display:none !important; }
section[data-testid="stSidebar"] { display:none !important; }
header, footer, #MainMenu { visibility:hidden !important; }

div[data-testid="stAppViewContainer"] {
    padding-top: 80px !important;  /* navbar spacing */
}

.block-container {
    padding-top: 0 !important;
    padding-bottom: 120px !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# NAVBAR
# ---------------------------------------------------------
navbar()

# ---------------------------------------------------------
# JS REDIRECT
# ---------------------------------------------------------
def redirect_to(path):
    components.html(f"<script>window.location.href = '{path}';</script>", height=0)

# ---------------------------------------------------------
# SIDEBAR API BASE URL
# ---------------------------------------------------------
DEFAULT_BASE_URL = "http://localhost:8000"

st.sidebar.header("API Settings")
BASE_URL = st.sidebar.text_input("Backend API Base URL", DEFAULT_BASE_URL)

st.sidebar.markdown("---")
st.sidebar.write("Session ID:", st.session_state.get("session_id", "-"))


# =========================================================
# 1️⃣ UPLOAD JD
# =========================================================
st.markdown("### 1. Upload Job Description (JD)")

jd_file = st.file_uploader("Upload JD (pdf/docx/txt)", type=["pdf", "docx", "txt"])
jd_text = st.text_area("Or paste JD text manually", height=150)

# Using columns to reduce width to approx 25% (1 part input, 3 parts empty)
c1, c2 = st.columns([1, 3])
with c1:
    job_title = st.text_input("Job Title")
    Category = st.text_input("Category")
    st.markdown("<br>", unsafe_allow_html=True) # Spacer
    jd_upload_btn = st.button("Upload JD")

if jd_upload_btn:
    if not jd_file and not jd_text.strip():
        st.error("Upload a JD file or paste text.")
    else:
        try:
            url = f"{BASE_URL}/jd/jd/upload"

            files = {}
            data = {"JobTitle": job_title, "Category": Category}

            if jd_file:
                files["jd"] = (jd_file.name, jd_file.read())
            else:
                files["jd"] = ("jd.txt", jd_text.encode())

            if job_title and Category:
                try:
                    if jd_file:
                        file_bytes = jd_file.getvalue()   # ✅ FIX: use getvalue()
                        files = {"jd": (jd_file.name, file_bytes)}
                    else:
                        files = {"jd": ("jd.txt", jd_text.encode())}

                    resp = requests.post(
                        url,
                        files=files,
                        data={"JobTitle": job_title, "Category": Category}
                    )


                    resp.raise_for_status()
                    result = resp.json()

                    st.session_state["session_id"] = result["session_id"]
                    st.success("📄 JD uploaded successfully!")

                except Exception as e:
                    st.error(f"Upload failed: {e}")
            else:
                st.error("Enter Job Title and Category.")

        except Exception as e:
            st.exception(e)

# =========================================================
# 2️⃣ UPLOAD RESUMES
# =========================================================
st.markdown("### 2. Upload Resumes")

uploaded_resumes = st.file_uploader(
    "Upload multiple resumes", type=["pdf", "docx", "txt"], accept_multiple_files=True
)

# Stacked Buttons
upload_resumes_btn = st.button("Upload Resumes")
clear_btn = st.button("Clear All")

if clear_btn:
    st.rerun()

if upload_resumes_btn:
    if not uploaded_resumes:
        st.error("Upload at least one resume.")
    elif "session_id" not in st.session_state:
        st.error("Upload JD first.")
    else:
        try:
            url = f"{BASE_URL}/resumes/resumes/upload"
            files_payload = []
            for f in uploaded_resumes:
                mime_type = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
                files_payload.append(
                    ("files", (f.name, f.read(), mime_type))  # ✅ key must be "files"
                )

            data_payload = {"session_id": st.session_state["session_id"]}  # Form field

            resp = requests.post(
                url,
                files=files_payload,
                data=data_payload
            )

            resp.raise_for_status()
            out = resp.json()
            st.success(out["message"])
            st.session_state["resumes_uploaded"] = True

        except Exception as e:
            st.exception(e)


# =========================================================
# 3️⃣ RUN SCREENING
# =========================================================
st.markdown("### 3. Run Screening")

col1, col2 = st.columns([1, 1])

with col1:
    top_n = st.number_input("Top N Candidates", min_value=1, max_value=50, value=5)

with col2:
    st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
    run_btn = st.button("Run Screening")

if run_btn:
    # ✅ Check JD uploaded
    session_id = st.session_state.get("session_id", None)
    # ✅ Check resumes uploaded flag (set True after successful resume upload)
    if not st.session_state.get("resumes_uploaded", False):
        st.error("Upload resumes first")

    if not session_id:
        st.error("Upload JD first")

    else:
        try:
            url = f"{BASE_URL}/matching/matching/run"

            # ✅ Send as form data (application/x-www-form-urlencoded)
            form_data = {
                "session_id": session_id,
                "top_n": int(top_n)
            }

            resp = requests.post(url, data=form_data)
            resp.raise_for_status()
            out = resp.json()

            if out.get("status") == "success":
                results = out.get("results")

                st.markdown("### 🎯 Best Matches")
                st.write("Results", results)

                # ✅ FULLY SAFE HANDLING
                if results is None:
                    st.error("No results returned from backend.")

                elif isinstance(results, dict) and "error" in results:
                    st.error(f"Backend Error: {results['error']}")

                elif isinstance(results, list) and len(results) == 0:
                    st.warning("No matching resumes found.")

                else:
                    import json

                    # 🔍 Step 1: If results is dict, extract inner list
                    if isinstance(results, dict) and "results" in results:
                        results = results["results"]

                    # 🔍 Step 2: Convert JSON strings → dicts (if needed)
                    if isinstance(results, list) and results and isinstance(results[0], str):
                        results = [json.loads(r) for r in results]

                    # 📊 Step 3: Create DataFrame correctly
                    df = pd.DataFrame(results)

                    # 🏷️ Step 4: Rename columns
                    df = df.rename(columns={
                        "file_name": "File Name",
                        "Name": "Name",
                        "Email": "Email",
                        "score": "Score",
                        "rank": "Rank",
                        "explanation": "Explanation"
                    })

                    # 📌 Step 5: Force column order
                    df = df[[
                        "File Name",
                        "Name",
                        "Email",
                        "Score",
                        "Rank",
                        "Explanation"
                    ]]

                    st.dataframe(df, use_container_width=True)

            else:
                st.error(out.get("message", "Unknown backend error"))

        except Exception as e:
            st.exception(e)


# =========================================================
# 4️⃣ DOWNLOAD CSV REPORT
# =========================================================
#st.markdown("### 4) Download CSV Report")

#if st.button("Download CSV"):
  #  try:
  #      session_id = st.session_state.get("session_id", "")
   #     url = f"{BASE_URL}/reports/reports/download-csv/{session_id}"

    #    resp = requests.get(url)
    #    resp.raise_for_status()

     #   st.download_button(
     #       "Download CSV File",
     #       resp.content,
      #      f"{session_id}.csv"
      #  )

   # except Exception as e:
     #   st.exception(e)

# =========================================================
# 5️⃣ SEND EMAIL (Redirect)
# =========================================================
st.markdown("### 4. Send Email to Candidates")

col_yes, col_no, _ = st.columns([1, 1, 6])

with col_yes:
    if st.button("Send Email"):
        st.switch_page("pages/automated_email.py")

with col_no:
    if st.button("No"):
        st.info("Email sending skipped.")

# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
#st.write("Current Session ID:", st.session_state.get("session_id", "-"))
