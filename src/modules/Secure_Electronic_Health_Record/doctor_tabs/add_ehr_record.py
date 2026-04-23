import streamlit as st
from datetime import datetime
from db import get_db
from utils import log_audit, generate_ehr_id

def render_add_ehr_record():
    db = get_db()
    st.markdown("### Add New EHR Record")
    st.info("💡 If the patient hasn't signed up yet, enter their email. Their account will auto-link when they register.")

    with st.form("add_ehr_form"):
        col1, col2 = st.columns(2)
        with col1:
            patient_email   = st.text_input("Patient Email (required)")
            patient_user_id = st.text_input("Patient User ID (USR-XXXXXX) — leave blank if unknown")
            patient_name    = st.text_input("Patient Name")
            age             = st.number_input("Age", min_value=0, max_value=120, value=0)
            gender          = st.selectbox("Gender", ["Male", "Female", "Other"])
            blood_group     = st.selectbox("Blood Group", ["A+","A-","B+","B-","AB+","AB-","O+","O-"])
            contact         = st.text_input("Contact Number")
        with col2:
            address     = st.text_area("Address")
            symptoms    = st.text_area("Symptoms")
            diagnosis   = st.text_input("Diagnosis")
            treatment   = st.text_input("Treatment")
            sensitivity = st.selectbox("Sensitivity Level", ["Normal", "Confidential", "Restricted"])

        submitted = st.form_submit_button("💾 Save EHR Record")

    if submitted:
        if not patient_name or not patient_email:
            st.error("❌ Patient Name and Email are required!")
        else:
            proceed = True
            if patient_user_id:
                # Validate the provided user_id and email match
                existing_user = db.users.find_one({"user_id": patient_user_id, "role": "Patient"})
                if not existing_user:
                    st.error(f"❌ Invalid User ID: No patient found with ID `{patient_user_id}` in the system.")
                    proceed = False
                elif existing_user.get("email") != patient_email:
                    st.error(f"❌ Mismatch: The User ID `{patient_user_id}` does not match the provided email `{patient_email}`.")
                    proceed = False
                else:
                    st.success("✅ Patient ID and Email matched successfully.")
            else:
                # Try to find patient user_id from email if not provided
                existing_user = db.users.find_one({"email": patient_email, "role": "Patient"})
                if existing_user:
                    patient_user_id = existing_user["user_id"]
                    st.info(f"✅ Patient found in system — Auto-linked User ID: **{patient_user_id}**")
                else:
                    patient_user_id = "PENDING"
                    st.warning("⚠️ Patient not registered yet. Record saved — will auto-link when they signup at this email.")

            if proceed:
                ehr_id = generate_ehr_id()
                record = {
                    "ehr_id":          ehr_id,
                    "patient_user_id": patient_user_id,
                    "patient_email":   patient_email,
                    "patient_name":    patient_name,
                    "age":             age,
                    "gender":          gender,
                    "blood_group":     blood_group,
                    "contact":         contact,
                    "address":         address,
                    "symptoms":        symptoms,
                    "diagnosis":       diagnosis,
                    "treatment":       treatment,
                    "primary_doctor":  st.session_state.get("user_name"),
                    "doctor_user_id":  st.session_state.get("user_id"),
                    "sensitivity":     sensitivity,
                    "encrypted":       True,
                    "status":          "Active",
                    "created_at":      datetime.now().isoformat()
                }
                db.ehr_records.insert_one(record)
                log_audit(action="INSERT", resource=ehr_id, status="Success")
                st.success(f"✅ EHR Record **{ehr_id}** saved successfully!")
                with st.expander(f"✨ Record Details: {ehr_id} — {patient_name}", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Patient:** {patient_name} ({age} yrs, {gender})")
                        st.write(f"**Email:** {patient_email}")
                        st.write(f"**Contact:** {contact}")
                        st.write(f"**Blood Group:** {blood_group}")
                    with col2:
                        st.write(f"**Doctor:** {st.session_state.get('user_name')}")
                        st.write(f"**Status:** {record.get('status')}")
                        st.write(f"**Sensitivity:** {record.get('sensitivity')}")
                    st.divider()
                    st.write(f"**Symptoms:** {symptoms}")
                    st.write(f"**Diagnosis:** {diagnosis}")
                    st.write(f"**Treatment:** {treatment}")
