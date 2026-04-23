import streamlit as st
from auth_service import signup_user
from db import get_db

def signup_page():
    db = get_db()
    st.title("🏥 MediCare - Create Account")

    role     = st.selectbox("Signup as", ["Patient", "Doctor", "Admin"])
    name     = st.text_input("Full Name")
    email    = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm  = st.text_input("Confirm Password", type="password")

    if st.button("Create Account"):
        if not name or not email or not password or not confirm:
            st.error("❌ All fields are required!")
        elif password != confirm:
            st.error("❌ Passwords do not match!")
        elif len(password) < 6:
            st.error("❌ Password must be at least 6 characters!")
        else:
            result = signup_user(name, email, password, role)
            if result["success"]:
                st.success(f"✅ {result['message']}")
                if role == "Patient":
                    user_id = result["user_id"]
                    unlinked = db.ehr_records.find({
                        "patient_email":   email,
                        "patient_user_id": {"$in": [None, "", "PENDING"]}
                    })
                    linked_count = 0
                    for rec in unlinked:
                        db.ehr_records.update_one(
                            {"_id": rec["_id"]},
                            {"$set": {"patient_user_id": user_id}}
                        )
                        linked_count += 1
                    if linked_count > 0:
                        st.info(f"🔗 {linked_count} existing EHR record(s) have been linked to your account!")
                st.info(f"Your User ID: **{result['user_id']}** — Save this for sharing with your doctor!")
                st.info("Please login with your credentials.")
            else:
                st.error(f"❌ {result['message']}")

    st.markdown("Already have an account?")
    if st.button("Login"):
        st.session_state.page = "login"
        st.rerun()