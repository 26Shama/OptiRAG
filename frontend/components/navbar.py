import streamlit as st
import textwrap

def navbar():
    # 1. LOGIC: Check if logout was clicked
    if st.query_params.get("logout") == "true":
        st.session_state.clear()
        st.query_params.clear()
        # Make sure "app.py" is your login/entry file
        st.switch_page("app.py") 
        st.stop()

    # 2. UI: Updated HTML
    html = textwrap.dedent("""
    <style>
        #top-nav {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100px;
            background: linear-gradient(135deg, #1e0533 0%, #3a0ca3 50%, #1e0533 100%);
            color: white; display: flex; justify-content: center;
            align-items: center; font-size: 24px; font-weight: 700;
            z-index: 99999; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        .nav-logo { position: absolute; left: 25px; height: 75px; width: auto; }
        .logout-button {
            position: absolute; right: 25px; padding: 8px 16px;
            background: rgba(255, 69, 58, 0.2); border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.3); cursor: pointer;
            font-size: 16px; text-decoration: none; color: white; transition: 0.3s;
        }
        .logout-button:hover { background: rgba(255, 69, 58, 0.5); border-color: #ff453a; }
    </style>

    <div id="top-nav">
        <img src="https://image2url.com/images/1764934626437-61894f61-95af-457f-a0ac-0ae789b7ab8b.png" class="nav-logo" alt="Logo">
        <div>OptiRAG: Optimizing Resume Screening Using RAG</div>
        <a href="./home?logout=true" target="_self" class="logout-button">Logout ⏻</a>
    </div>
    """)
    st.markdown(html, unsafe_allow_html=True)

# DO NOT CALL navbar() HERE
