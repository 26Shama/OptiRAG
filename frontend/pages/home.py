import streamlit as st
from components.navbar import navbar

# -----------------------------------
# PAGE CONFIG
# -----------------------------------
st.set_page_config(page_title="OptiRAG Dashboard", layout="wide")

# AUTH
if "is_authenticated" not in st.session_state or not st.session_state.is_authenticated:
    st.switch_page("app")
    st.stop()

# -----------------------------------
# GLOBAL CSS FIXES (IMPORTANT)
# -----------------------------------
st.markdown("""
<style>

/* 1. BACKGROUND IMAGE */
.stApp {
    background-image: url("https://image2url.com/images/1764942964505-d1088267-5df9-4f01-bef9-4fb829a59aa1.png");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
}

/* 2. HIDE DEFAULT STREAMLIT ELEMENTS */
header, .stHeader, footer {
    visibility: hidden !important;
}
section[data-testid="stSidebar"] {
    display: none !important;
}

/* 3. NAVBAR FIX */
.block-container {
    padding-top: 0rem !important;
    padding-bottom: 0rem !important;
    padding-left: 0rem !important;
    padding-right: 0rem !important;
    max-width: 100% !important;
}

/* ----------------------------------------------------
   4. THE CARD (Middle Column) - COLOR CHANGE HERE
---------------------------------------------------- */
div[data-testid="stHorizontalBlock"] > div:nth-child(2) > div[data-testid="stVerticalBlock"] {
    /* OPTION A: Clean Glass (Good for Dark Text) */
    background: rgba(255, 255, 255, 0.75); 
    
    /* OPTION B: Your Peach Color (Uncomment line below to use) */
    /* background: #FFCDB2; */

    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    
    border-radius: 25px;
    border: 1px solid rgba(255, 255, 255, 0.4);
    box-shadow: 0 15px 40px rgba(0,0,0,0.2);
    
    padding: 50px !important;
    margin-top: 20px; 
    
    /* Centering content inside the card */
    display: flex;
    flex-direction: column;
    align-items: center; 
}


/* ----------------------------------------------------
   5. HEADING STYLE (Dark & Attractive)
---------------------------------------------------- */
h2 {
    text-align: center;
    color: #1a237e !important; /* Dark Midnight Blue */
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 52px !important; /* Bigger Size */
    font-weight: 800 !important;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 40px !important;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
}

/* ----------------------------------------------------
   6. BUTTON STYLES (More Attractive & Reduced Width)
---------------------------------------------------- */
.stButton {
    width: 100%; /* Container width */
    display: flex;
    justify-content: center; /* Centers the button */
}

.stButton > button {
    width: 70% !important; /* Reduced Width (was 100%) */
    height: 85px !important;
    
    /* Gradient Background */
    background: linear-gradient(135deg, #151922 0%, #2c3e50 100%) !important;
    color: white !important;
    
    border: none !important;
    border-left: 6px solid #3c55d1 !important; /* Stylish Accent Border */
    border-radius: 12px !important;
    
    font-size: 24px !important;
    font-weight: 700 !important;
    letter-spacing: 1px;
    
    transition: all 0.3s ease !important;
    box-shadow: 0 5px 15px rgba(0,0,0,0.2); /* Soft Shadow */
    
    margin-bottom: 20px !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #3c55d1 0%, #2a40a0 100%) !important;
    transform: translateY(-3px) scale(1.02); /* Slight lift effect */
    box-shadow: 0 8px 25px rgba(60, 85, 209, 0.4); /* Glow effect */
    border-left: 6px solid white !important;
}
            
</style>
""", unsafe_allow_html=True)

# -----------------------------------
# NAVBAR
# -----------------------------------
navbar()

# spacing under navbar
st.markdown("<br><br><br><br>", unsafe_allow_html=True)

# -----------------------------------
# MAIN UI BUTTONS
# -----------------------------------
col_left, col_card, col_right = st.columns([3, 6, 3]) 

# 2. Put content INSIDE the middle column
with col_card:
    st.markdown("<h2>Welcome</h2>", unsafe_allow_html=True)
    
    # Only the two requested buttons remain
    if st.button("Resume Screening", use_container_width=True):
        st.switch_page("pages/rs.py")

    if st.button("Automated Email", use_container_width=True):
        st.switch_page("pages/automated_email.py")

    if st.button("Any Queries", use_container_width=True):
        st.switch_page("pages/queries.py")
