import streamlit as st
from  auth_service import login_user

def login_page():
    st.title("🏥 MediCare Login")

    role     = st.selectbox("Login as", ["Patient", "Doctor", "Admin"])
    email    = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if not email or not password:
            st.error("Please enter email and password")
        else:
            result = login_user(email, password, role)
            if result["success"]:
                st.session_state.logged_in = True
                st.session_state.role      = result["role"]
                st.session_state.page      = "dashboard"
                st.session_state.user_id   = result["user_id"]
                st.session_state.user_name = result["name"]
                st.session_state.email     = result["email"]
                st.rerun()
            else:
                st.error(result["message"])

    st.markdown("Don't have an account?")
    if st.button("Signup"):
        st.session_state.page = "signup"
        st.rerun()

