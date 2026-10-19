import streamlit as st
import pandas as pd
import requests
from utils.session_manager import auth_guard
from components.navbar import navbar

# ---------------- AUTH ----------------
auth_guard()

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Automated Email", layout="wide")

# ---------------- GLOBAL CSS ----------------
st.markdown("""
<style>
section[data-testid="stSidebar"] { 
    display:none !important; 
}

header, footer, #MainMenu { 
    visibility:hidden !important; 
}

div[data-testid="stAppViewContainer"] {
    padding-top: 120px !important;
    min-height: 120vh !important;
    background-color: #DDBEA9 !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------- NAVBAR ----------------
navbar()

# ---------------- PAGE TITLE ----------------
st.markdown(
    "<h2 style='text-align:left; margin-top:20px;'>Automated Email Dashboard</h2>",
    unsafe_allow_html=True
)

# ---------------- API BASE URL ----------------
DEFAULT_BASE_URL = "http://localhost:8000"

st.sidebar.header("API Settings")
BASE_URL = st.sidebar.text_input("Backend API Base URL", DEFAULT_BASE_URL)

# ---------------- CSV UPLOAD ----------------
st.markdown("### Upload CSV (must contain an email column)")

csv = st.file_uploader(
    "Upload CSV file",
    type=["csv"],
    label_visibility="collapsed"
)

if csv:
    try:
        df = pd.read_csv(csv)

        # ✅ ONLY REQUIRED CHANGE STARTS HERE
        df.columns = df.columns.str.strip().str.lower()

        email_columns = ["email", "email id", "email_id", "candidate_email"]
        email_col = next((col for col in email_columns if col in df.columns), None)

        if not email_col:
            st.error("CSV must contain an 'email' column.")
        else:
            df.rename(columns={email_col: "email"}, inplace=True)
        # ✅ ONLY REQUIRED CHANGE ENDS HERE

            st.success("CSV uploaded successfully!")
            st.dataframe(df, use_container_width=True)

            # ---------------- GMAIL DETAILS ----------------
            st.markdown("### Enter Gmail Details")

            col1, col2 = st.columns([1, 1])

            with col1:
                sender_email = st.text_input("Sender Gmail ID")
                sender_name = st.text_input("Sender Name", value="HR Team")

            with col2:
                app_password = st.text_input("Gmail App Password", type="password")
                position = st.text_input("Job Position")

            # ---------------- CONFIRMATION ----------------
            st.markdown(
                "<h3>Do you want to send emails?</h3>",
                unsafe_allow_html=True
            )

            btn_col1, btn_col2 = st.columns([1, 1])

            with btn_col1:
                yes = st.button("YES", use_container_width=True)

            with btn_col2:
                no = st.button("NO", use_container_width=True)

            # ------------ YES CLICK ------------
            if yes:
                if not sender_email or not app_password or not position:
                    st.error("Please fill all Gmail credentials and job position.")
                else:
                    with st.spinner("Sending emails..."):
                        try:
                            files = {
                                "file": (
                                    csv.name,
                                    csv.getvalue(),
                                    "text/csv"
                                )
                            }

                            data = {
                                "sender_email": sender_email,
                                "sender_name": sender_name,
                                "app_password": app_password,
                                "position": position
                            }

                            resp = requests.post(
                                f"{BASE_URL}/api/hr-emailer/send-emails",
                                files=files,
                                data=data,
                                timeout=300
                            )

                            if resp.status_code == 200:
                                result = resp.json()

                                st.success(
                                    f"Emails sent successfully!\n\n"
                                    f"Sent: {result.get('sent')}\n"
                                    f"Failed: {result.get('failed')}"
                                )

                                if "details" in result:
                                    st.subheader("📊 Email Send Report")
                                    st.dataframe(
                                        pd.DataFrame(result["details"]),
                                        use_container_width=True
                                    )

                            else:
                                st.error(f"Error: {resp.text}")

                        except Exception as e:
                            st.exception(e)

            # ------------ NO CLICK ------------
            if no:
                st.info("Email sending cancelled.")

    except Exception as e:
        st.error(f"Failed to read CSV: {e}")
