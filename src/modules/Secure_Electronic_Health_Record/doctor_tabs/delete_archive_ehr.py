import streamlit as st
from datetime import datetime
from db import get_db
from utils import log_audit, has_patient_granted_access

def render_delete_archive_ehr():
    db = get_db()
    st.markdown("### Delete / Archive EHR Record")
    st.warning("⚠️ Records are **never hard deleted**. They are archived for compliance with data retention policies.")

    ehr_id_input = st.text_input("Enter EHR ID to archive (e.g. EHR-123456)")

    if st.button("🔍 Find Record"):
        record = db.ehr_records.find_one({"ehr_id": ehr_id_input}, {"_id": 0})
        if record:
            patient_uid = record.get("patient_user_id")
            doctor_uid  = st.session_state.get("user_id")
            if has_patient_granted_access(patient_uid, doctor_uid, ehr_id_input):
                st.session_state["delete_record"] = record
                st.success("✅ Record found!")
            else:
                log_audit(action="DELETE-ATTEMPT", resource=ehr_id_input,
                          status="DENIED", reason="Patient has not granted access")
                st.error("🚫 Access Denied — Patient has not granted you access.")
        else:
            st.error("❌ No record found with that EHR ID.")

    if "delete_record" in st.session_state:
        rec = st.session_state["delete_record"]

        st.markdown("#### Record to Archive:")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**EHR ID:** {rec.get('ehr_id')}")
            st.write(f"**Patient:** {rec.get('patient_name')}")
            st.write(f"**Diagnosis:** {rec.get('diagnosis')}")
        with col2:
            st.write(f"**Doctor:** {rec.get('primary_doctor')}")
            st.write(f"**Status:** {rec.get('status')}")
            st.write(f"**Created:** {rec.get('created_at')}")

        reason = st.text_input("Reason for archiving (required)")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📦 Confirm Archive"):
                if not reason:
                    st.error("❌ Please provide a reason for archiving.")
                else:
                    # Soft delete — move to archive collection
                    archive_record = dict(rec)
                    archive_record["archived_at"] = datetime.now().isoformat()
                    archive_record["archived_by"] = st.session_state.get("user_name")
                    archive_record["archive_reason"] = reason
                    db.ehr_archive.insert_one(archive_record)

                    # Update status to Archived
                    db.ehr_records.update_one(
                        {"ehr_id": rec.get("ehr_id")},
                        {"$set": {
                            "status":      "Archived",
                            "archived_at": datetime.now().isoformat(),
                            "archived_by": st.session_state.get("user_name")
                        }}
                    )
                    log_audit(action="ARCHIVE", resource=rec.get("ehr_id"),
                              status="Success", reason=reason)
                    st.success(f"✅ EHR **{rec.get('ehr_id')}** archived successfully!")
                    del st.session_state["delete_record"]

        with col2:
            if st.button("❌ Cancel"):
                del st.session_state["delete_record"]
                st.rerun()
