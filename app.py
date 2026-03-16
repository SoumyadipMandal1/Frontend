import streamlit as st
from streamlit_option_menu import option_menu
from auth.login import login_page
from auth.signup import signup_page
from dashboards.patient_dashboard import patient_dashboard
from dashboards.doctor_dashboard import doctor_dashboard
from dashboards.admin_dashboard import admin_dashboard
# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="MediCare", layout="wide")

# ---------------- SESSION STATE INIT ----------------
st.session_state.setdefault("logged_in", False)
st.session_state.setdefault("page", "login")
st.session_state.setdefault("role", None)

# ---------------- HARD REDIRECT AFTER LOGIN ----------------
if st.session_state.logged_in:
    if st.session_state.role == "Patient":
        patient_dashboard()
        st.stop()
    elif st.session_state.role == "Doctor":
        doctor_dashboard()
        st.stop()
    elif st.session_state.role == "Admin":
        admin_dashboard()
        st.stop()

# ---------------- AUTH ROUTING ----------------
if st.session_state.page == "login":
    login_page()
elif st.session_state.page == "signup":
    signup_page()

#---------DEMO--------------
st.title("MongoDB + Streamlit Demo")

name = st.text_input("Enter Name")

if st.button("Save"):
    collection.insert_one({"name" : name})

if st.button("View Data"):
    data = list(collection.find({}, {"_id" : 0}))
    st.write(data)
