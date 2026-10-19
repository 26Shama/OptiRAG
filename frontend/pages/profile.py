import streamlit as st
from utils.session_manager import auth_guard, logout_user
from components.navbar import navbar

st.set_page_config(page_title="Profile", page_icon="👤", layout="wide")

# 🔥 Show sidebar
st.markdown("""
<style>
/* Hide Streamlit's default sidebar */
section[data-testid="stSidebar"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)


auth_guard()
navbar()

st.subheader("My Profile")
st.text_input("Name", value=st.session_state["user"]["name"], disabled=True)
st.text_input("Email", value=st.session_state["user"]["email"], disabled=True)

if st.button("Logout", use_container_width=True):
    logout_user()
    st.rerun()
