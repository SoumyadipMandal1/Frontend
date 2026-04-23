import streamlit as st
from datetime import datetime
from db import get_db
from utils import log_audit, has_patient_granted_access

def render_update_ehr_record():
    db = get_db()
    st.markdown("### Update Existing EHR Record")
    st.info("💡 You can only update records where patient has granted you access.")

    ehr_id_input = st.text_input("Enter EHR ID to update (e.g. EHR-123456)")

    if st.button("🔍 Find Record"):
        record = db.ehr_records.find_one({"ehr_id": ehr_id_input}, {"_id": 0})
        if record:
            patient_uid = record.get("patient_user_id")
            doctor_uid  = st.session_state.get("user_id")
            if has_patient_granted_access(patient_uid, doctor_uid, ehr_id_input):
                st.session_state["update_record"] = record
                st.success("✅ Record found! Update the fields below.")
            else:
                log_audit(action="UPDATE-ATTEMPT", resource=ehr_id_input,
                          status="DENIED", reason="Patient has not granted access")
                st.error("🚫 Access Denied — Patient has not granted you access to update this record.")
        else:
            st.error("❌ No record found with that EHR ID.")

    if "update_record" in st.session_state:
        rec = st.session_state["update_record"]
        st.markdown(f"**Updating:** `{rec.get('ehr_id')}` — {rec.get('patient_name')}")

        with st.form("update_ehr_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_symptoms  = st.text_area("Symptoms",    value=rec.get("symptoms", ""))
                new_diagnosis = st.text_input("Diagnosis",  value=rec.get("diagnosis", ""))
                new_treatment = st.text_input("Treatment",  value=rec.get("treatment", ""))
            with col2:
                new_sensitivity = st.selectbox(
                    "Sensitivity Level",
                    ["Normal", "Confidential", "Restricted"],
                    index=["Normal", "Confidential", "Restricted"].index(rec.get("sensitivity", "Normal"))
                )
                new_status = st.selectbox(
                    "Status",
                    ["Active", "Archived"],
                    index=["Active", "Archived"].index(rec.get("status", "Active"))
                )
            submitted = st.form_submit_button("💾 Save Updates")

        if submitted:
            db.ehr_records.update_one(
                {"ehr_id": rec.get("ehr_id")},
                {"$set": {
                    "symptoms":     new_symptoms,
                    "diagnosis":    new_diagnosis,
                    "treatment":    new_treatment,
                    "sensitivity":  new_sensitivity,
                    "status":       new_status,
                    "updated_at":   datetime.now().isoformat(),
                    "updated_by":   st.session_state.get("user_name")
                }}
            )
            log_audit(action="UPDATE", resource=rec.get("ehr_id"), status="Success")
            st.success(f"✅ EHR Record **{rec.get('ehr_id')}** updated successfully!")
            del st.session_state["update_record"]
