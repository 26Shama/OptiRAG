import streamlit as st
import requests
from utils.session_manager import auth_guard
from components.navbar import navbar

# ---------------- AUTH ----------------
auth_guard()

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="HR Chatbot - OptiRAG", layout="wide")

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

/* ---- Chatbot page heading color fix ---- */
.chatbot-title {
    color: #000000 !important;
    font-weight: 800;
}

.chatbot-subtitle {
    color: #000000 !important;
    font-size: 20px;
    margin-bottom: 20px;
}

/* ---- Make text area label bigger & dark black ---- */
.stTextArea label {
    font-weight: 700;
    font-size: 40px !important;
}

/* ---- ONLY CHANGE: Chatbot response text color ---- */
.block-container h3,        /* 🤖 Response heading */
.block-container p,         /* Response text */
.block-container div[data-testid="stMarkdownContainer"] {
    color: #000000 !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------- NAVBAR ----------------
navbar()

# ---- SPACE BETWEEN NAVBAR & TITLE ----
st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)

# ---------------- PAGE TITLE ----------------
st.markdown(
    "<h2 class='chatbot-title'>HR Assistant</h2>",
    unsafe_allow_html=True
)

st.markdown(
    "<h3 class='chatbot-subtitle'>Ask anything about OptiRAG system</h3>",
    unsafe_allow_html=True
)

# ---------------- CHAT INPUT ----------------
question = st.text_area(
    "Enter your query",
    placeholder="ASK ANYTHING",
    height=70
)

# ---------------- BUTTON (REDUCED WIDTH) ----------------
col_left, col_btn, col_right = st.columns([3, 2, 3])

with col_btn:
    ask_btn = st.button("Ask Assistant")

# ---------------- API CALL ----------------
if ask_btn:
    if not question.strip():
        st.error("Please enter a query.")
    else:
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    "http://localhost:8000/chat/query",
                    json={"question": question},
                    timeout=30
                )

                if response.status_code == 200:
                    answer = response.json().get("answer", "")
                    st.markdown("### 🤖 Response")
                    st.write(answer)
                else:
                    st.error("Failed to get response from chatbot API.")

            except Exception:
                st.error("Backend not reachable. Please ensure FastAPI server is running.")
