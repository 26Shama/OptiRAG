import streamlit as st

# ✅ ADD ONLY THESE TWO LINES
import requests
BACKEND_URL = "http://localhost:8000"
# ✅ END ADD

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="OptiRAG:Optimizing Resume Screening Using RAG", page_icon="🔐", layout="wide")

# ---------------------------------------------------------
# SESSION STATE INIT
# ---------------------------------------------------------
if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False

if "auth_page" not in st.session_state:
    st.session_state.auth_page = "login"   # login | signup | forgot

# Hide sidebar for all auth pages
st.markdown("""
<style>
[data-testid="stSidebar"], header, footer { display: none !important; }
.block-container { padding-top: 50px !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# GLOBAL UI CSS
# ---------------------------------------------------------
st.markdown("""
<style>
body { background-color: #0f1116; font-family: 'Segoe UI', sans-serif; }
#MainMenu { visibility: hidden; }

.stButton > button {
    width: 150px; height: 45px;
    background-color: #ff5a1f;
    color: white; font-size: 18px;
    font-weight: 600; border-radius: 10px;
    border: none; margin: auto; display: block;
    transition: 0.2s; cursor: pointer;
}
.stButton > button:hover {
    background-color: #e24a18;
    transform: scale(1.05);
}

.login-title {
    font-size: 35px; font-weight: 800; text-align: center;
    color: #1d45a5; margin-bottom: 10px;
}
.login-subtitle {
    text-align: center; margin-top: -5px;
    color: #c0c0c0; font-size: 16px;
}
.other-btn a {
    text-decoration: none;
    color: #1d45a5;
    font-weight: 600;
    font-size: 18px;
}
.other-btn a:hover { text-decoration: underline; }

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# LOGIN SCREEN
# ---------------------------------------------------------
def login_screen():
    # --- 1. CSS Styling (SAME AS SIGNUP) ---
    st.markdown(r"""
    <style>
    /* GLOBAL STYLES */
    html, body, .stApp {
        background: linear-gradient(135deg, #1e0533 0%, #3a0ca3 50%, #1e0533 100%);
        font-family: 'Sans-serif';
        color: white;
    }

    /* HIDE STREAMLIT HEADER/FOOTER */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    .block-container {
        padding-top: 0.25rem !important;
        padding-bottom: 2rem;
    }

    /* --- LEFT COLUMN STYLING --- */
    .left-container {
        text-align: center;
        padding-right: 40px;
        animation: fadeIn 1.5s ease-in-out;
    }
    
    div[data-testid="stImage"] > img {
        filter: drop-shadow(0 0 10px rgba(224, 170, 255, 0.5));
    }

    .welcome-text {
        font-size: 50px;
        font-weight: 800;
        background: -webkit-linear-gradient(#fff, #E0AAFF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-top: -20px;
        margin-bottom: 10px;
    }

    .quote-text {
        font-size: 18px;
        color: #cfcfe8;
        font-style: italic;
        font-weight: 300;
        line-height: 1.6;
    }

    /* --- RIGHT COLUMN (INPUT CONTAINER) STYLING --- */
    /* Since we removed st.form, we style the container of the inputs if needed, 
       but standard inputs look fine on this background */

    /* INPUT FIELDS */
    .stTextInput > div > div > input {
        background-color: rgba(0, 0, 0, 0.2);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 10px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #E0AAFF;
        box-shadow: 0 0 5px rgba(224, 170, 255, 0.5);
    }
    .stTextInput label {
        color: #E0AAFF !important;
        font-weight: 500;
    }

    /* --- BUTTON STYLING --- */
    
    /* 1. "Login" Button (Gradient) - We identify it by type="primary" */
    div[data-testid="stButton"] button[kind="primary"] {
        width: 100%;
        background: linear-gradient(90deg, #b298dc 0%, #6f2c91 100%);
        border: none;
        color: white;
        font-weight: bold;
        padding: 0.5rem 1rem;
        border-radius: 10px;
        transition: transform 0.2s;
    }
    
    div[data-testid="stButton"] button[kind="primary"]:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 15px rgba(229, 46, 113, 0.4);
        border: none; /* Ensure no border appears on hover */
    }

    /* 2. "Sign Up" Button (Purple Outline) - Standard buttons (secondary) */
    div[data-testid="stButton"] button[kind="secondary"] {
        background: transparent;
        border: 1px solid #b298dc;
        color: white;
        border-radius: 20px;
        padding: 6px 20px;
        font-size: 14px;
        transition: all 0.3s ease;
    }

    div[data-testid="stButton"] button[kind="secondary"]:hover {
        background: #b298dc;
        color: #1e0533;
        border-color: #b298dc;
        box-shadow: 0 0 15px rgba(178, 152, 220, 0.4);
    }
    
    /* Forgot Password Link Style */
    .fp-link {
        text-align: center; 
        margin-top: 10px; 
        font-size: 0.9em;
    }
    .fp-link a {
        color: #cfcfe8;
        text-decoration: none;
    }
    .fp-link a:hover {
        color: #E0AAFF;
        text-decoration: underline;
    }

    /* ANIMATION */
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(20px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    </style>
    """, unsafe_allow_html=True)

    # --- 2. Layout Structure ---
    
    # Create columns with vertical centering
    col1, col2 = st.columns([1.2, 1], gap="large", vertical_alignment="center")

    # --- LEFT COLUMN (Info) ---
    with col1:
        st.markdown('<div class="left-container">', unsafe_allow_html=True)
        
        try:
            st.image("frontend/assets/logo.png", width=250) 
        except:
            st.markdown("<h1>💎</h1>", unsafe_allow_html=True)

        st.markdown('<div class="welcome-text">Welcome Back!</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="quote-text">Unlock your potential.<br>Smart Resume and JD Matching made effortless.</div>', 
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # --- RIGHT COLUMN (Login Form) ---
    with col2:
        st.markdown("<h3 style='text-align: center; color: white; margin-bottom: 20px;'>Log In</h3>", unsafe_allow_html=True)
        
        # Wrapped your inputs in st.form for the glass styling
        with st.form("login_form", clear_on_submit=False):
            
            email = st.text_input("Email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # This is your existing Logic inside the button
            submitted = st.form_submit_button("Login")

            if submitted:
                if email.strip() == "" or password.strip() == "":
                    st.error("⚠ Please enter both email and password")
                else:
                    try:
                        resp = requests.post(
                            f"{BACKEND_URL}/auth/auth/login",
                            json={"email": email, "password": password}
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            st.session_state.is_authenticated = True
                            st.session_state["user"] = data["email"]
                            st.success("✔ Login successful")
                            st.switch_page("pages/home.py")
                        else:
                            st.error(resp.json().get("detail", "Invalid login"))

                    except Exception as e:
                        st.error(f"Server error: {e}")

    # --- FOOTER SECTION ---
    # Centered Buttons for Navigation
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 1. Add the new text
    st.markdown('<div style="text-align: center; margin-bottom: 10px; color: #E0AAFF;">New to OptiRAG?</div>', unsafe_allow_html=True)
    
    # 2. Use columns to center the button and make it small
    _, c_col, _ = st.columns([1, 0.6, 1])

    with c_col:
        #st.markdown(
           # '<div style="text-align: center;"><a href="?signup=1" class="signup-btn" target="_self">Create Account</a></div>', 
           # unsafe_allow_html=True
       # )
        if st.button("Create Account"):
            st.session_state.auth_page = "signup"
            st.rerun()
    #query = st.query_params

    #if "signup" in query:
       # st.session_state.auth_page = "signup"
       # st.rerun()


# ---------------------------------------------------------
# SIGNUP SCREEN
# ---------------------------------------------------------
def signup_screen():
    # --- 1. CSS Styling ---
    st.markdown(r"""
    <style>
    /* GLOBAL STYLES */
    html, body, .stApp {
        background: linear-gradient(135deg, #1e0533 0%, #3a0ca3 50%, #1e0533 100%);
        font-family: 'Sans-serif';
        color: white;
    }

    /* HIDE STREAMLIT HEADER/FOOTER */
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* CENTER THE LAYOUT VERTICALLY */
    .block-container {
        padding-top: 0.25rem !important; /* REDUCED GAP HERE */
        padding-bottom: 2rem;
    }

    /* --- LEFT COLUMN STYLING --- */
    .left-container {
        text-align: center;
        padding-right: 40px;
        animation: fadeIn 1.5s ease-in-out;
    }
    
    .logo-img {
        margin-bottom: 20px;
        filter: drop-shadow(0 0 10px rgba(224, 170, 255, 0.5));
    }

    .welcome-text {
        font-size: 50px;
        font-weight: 800;
        background: -webkit-linear-gradient(#fff, #E0AAFF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-top: -20px;
        margin-bottom: 10px;
    }

    .quote-text {
        font-size: 18px;
        color: #cfcfe8;
        font-style: italic;
        font-weight: 300;
        line-height: 1.6;
    }

    /* --- RIGHT COLUMN (FORM) STYLING --- */
    [data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 30px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }

    /* INPUT FIELDS */
    .stTextInput > div > div > input {
        background-color: rgba(0, 0, 0, 0.2);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 10px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #E0AAFF;
        box-shadow: 0 0 5px rgba(224, 170, 255, 0.5);
    }
    .stTextInput label {
        color: #E0AAFF !important;
        font-weight: 500;
    }

    /* --- BUTTON STYLING FIX --- */
    
    /* FIX 2: Target ONLY the Submit Button (Create Account) */
    /* This excludes the password 'eye' button */
    [data-testid="stForm"] [data-testid="stFormSubmitButton"] button {
        width: 100%;
        background: linear-gradient(90deg, #b298dc 0%, #6f2c91 100%);
        border: none;
        color: white;
        font-weight: bold;
        padding: 0.5rem 1rem;
        border-radius: 10px;
        transition: transform 0.2s;
    }
    
    [data-testid="stForm"] [data-testid="stFormSubmitButton"] button:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 15px rgba(229, 46, 113, 0.4);
    }

    /* 2. "Login Here" Button (Purple Outline) */
    /* We target the regular stButton. This WON'T affect the form button or eye icon */
    div[data-testid="stButton"] button {
        background: transparent;
        border: 1px solid #b298dc;
        color: white;
        border-radius: 20px;
        padding: 6px 20px;
        font-size: 14px;
        transition: all 0.3s ease;
    }

    div[data-testid="stButton"] button:hover {
        background: #b298dc;
        color: #1e0533;
        border-color: #b298dc;
        box-shadow: 0 0 15px rgba(178, 152, 220, 0.4);
    }

    /* ANIMATION */
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(20px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    </style>
    """, unsafe_allow_html=True)

    # --- 2. Layout Structure ---
    
    # Create columns with vertical centering
    col1, col2 = st.columns([1.2, 1], gap="large", vertical_alignment="center")

    # --- LEFT COLUMN (Welcome Info) ---
    with col1:
        st.markdown('<div class="left-container">', unsafe_allow_html=True)
        
        # Display Logo (Ensure path is correct, or use a placeholder icon)
        try:
            st.image("frontend/assets/logo.png", width=250) 
        except:
            # Fallback if image not found
            st.markdown("<h1>💎</h1>", unsafe_allow_html=True)

        st.markdown('<div class="welcome-text">Welcome to OptiRAG!</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="quote-text">Unlock your potential. <br> Smart Resume and JD Matching made effortless.</div>', 
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # --- RIGHT COLUMN (Signup Form) ---
    with col2:
        # Title inside the column before the form
        st.markdown("<h3 style='text-align: center; color: white; margin-bottom: 20px;'>Sign Up</h3>", unsafe_allow_html=True)
        
        with st.form("signup_form", clear_on_submit=False):
            
            # Using columns inside form for cleaner layout if needed, or simple stack
            full_name = st.text_input("Full Name", placeholder="John Doe")
            email = st.text_input("Email", placeholder="john@example.com")
            username = st.text_input("Username", placeholder="johndoe123")
            
            # Password fields
            password = st.text_input("Password", type="password", placeholder="••••••••")
            cpassword = st.text_input("Confirm Password", type="password", placeholder="••••••••")
            
            agree = st.checkbox("I agree to Terms & Conditions")
            
            # Spacer
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Submit Button
            submitted = st.form_submit_button("Create Account")

            if submitted:
                if not full_name or not email or not username or not password or not cpassword:
                    st.error("Please fill all fields")
                elif password != cpassword:
                    st.error("Passwords do not match")
                elif not agree:
                    st.warning("Please accept Terms")
                else:
                    # Backend Logic
                    try:
                        resp = requests.post(
                            f"{BACKEND_URL}/auth/auth/signup",
                            json={
                                "name": full_name,
                                "email": email,
                                "username": username,
                                "password": password
                            }
                        )

                        if resp.status_code == 200:
                            st.success("Account created! Redirecting...")
                            st.session_state.auth_page = "login"
                            st.rerun()
                        else:
                            st.error(resp.json().get("detail", "Signup failed"))

                    except Exception as e:
                        st.error(f"Server connection failed: {e}")

    # --- FOOTER SECTION (Login Button) ---
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Using columns to center the small button specifically
    b_col1, b_col2, b_col3 = st.columns([1.5, 1, 1.5])
    
    with b_col2:
        st.markdown(
            """<div style="text-align: center; font-size: 14px; margin-bottom: 5px; color: rgba(255,255,255,0.7);">
            Already have an account?
            </div>""", 
            unsafe_allow_html=True
        )
        # REMOVED 'use_container_width=True' to make it small
        if st.button("Login Here"):
            st.session_state.auth_page = "login"
            st.rerun()



# ---------------------------------------------------------
# ROUTER
# ---------------------------------------------------------
if not st.session_state.is_authenticated:

    if st.session_state.auth_page == "login":
        login_screen()

    elif st.session_state.auth_page == "signup":
        signup_screen()


else:
    st.switch_page("pages/home.py")
