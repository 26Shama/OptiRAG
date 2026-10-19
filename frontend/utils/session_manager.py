# frontend/utils/session_manager.py
import streamlit as st
import time

def init_session():
    if "is_authenticated" not in st.session_state:
        st.session_state["is_authenticated"] = False
    if "user" not in st.session_state:
        st.session_state["user"] = {"name": "", "email": ""}
    if "auth_page" not in st.session_state:
        st.session_state["auth_page"] = "login"

def login_user(token: str | None, user_data: dict):
    """If you have real token, set it. For now we set user data only."""
    st.session_state["is_authenticated"] = True
    st.session_state["user"] = user_data
    st.session_state["token"] = token

def logout_user():
    st.session_state["is_authenticated"] = False
    st.session_state["user"] = {"name": "", "email": ""}
    st.session_state["token"] = None

def auth_guard():
    """
    Call at top of any page inside frontend/pages/ to force login.
    When user not logged in, redirect to app.py (login page).
    Use path relative to pages/ -> "../app.py"
    """
    if not st.session_state.get("is_authenticated", False):
        st.warning("Please login to continue.")
        time.sleep(0.7)
        # streamlit expects switch_page to reference paths under pages,
        # using "../app.py" will navigate back to main script
        
