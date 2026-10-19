import streamlit as st
import time

# ---------------------------------------------------------
# Initialize session state fields
# ---------------------------------------------------------
def init_session():
    if "is_authenticated" not in st.session_state:
        st.session_state["is_authenticated"] = False

    # ❌ REMOVED: token session field

    if "user" not in st.session_state:
        st.session_state["user"] = {
            "name": "",
            "email": ""
        }


# ---------------------------------------------------------
# Login: Save User Data (JWT REMOVED)
# ---------------------------------------------------------
def login_user(user_data: dict):
    st.session_state["is_authenticated"] = True
    # ❌ REMOVED: st.session_state["token"] = token
    st.session_state["user"] = user_data


# ---------------------------------------------------------
# Logout: Clear Session (JWT REMOVED)
# ---------------------------------------------------------
def logout_user():
    st.session_state["is_authenticated"] = False
    # ❌ REMOVED: st.session_state["token"] = None
    st.session_state["user"] = {"name": "", "email": ""}


# ---------------------------------------------------------
# Page Protection: Redirect if Not Logged In
# ---------------------------------------------------------
def auth_guard():
    if not st.session_state.get("is_authenticated", False):
        st.warning("You must log in first.")
        time.sleep(1)
        st.switch_page("app.py")   # Redirect to login
