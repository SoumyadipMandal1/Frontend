import streamlit as st
from src.modules.secure_ehr.db import get_db
from src.modules.secure_ehr.utils import log_audit

def render_view_records():
    db = get_db()
    st.markdown("### View EHR Records")
    view_mode = st.radio(
        "",
        ["Search by EHR ID", "Search by Name", "Search by Email", "Search by Patient User ID", "View All"],
        horizontal=True
    )

    doctor_uid = st.session_state.get("user_id")

    # ── Build two access sets ─────────────────────────────────────────
    # 1. Broad consent: patient granted access to ALL their records
    broad_consents = list(db.ehr_consent.find(
        {"doctor_user_id": doctor_uid, "status": "Granted",
         "$or": [{"ehr_id": {"$exists": False}}, {"ehr_id": "ALL"}]},
        {"patient_user_id": 1, "_id": 0}
    ))
    broad_patient_ids = {c["patient_user_id"] for c in broad_consents}

    # 2. Specific-record consent: patient granted access to individual EHR IDs
    specific_consents = list(db.ehr_consent.find(
        {"doctor_user_id": doctor_uid, "status": "Granted",
         "ehr_id": {"$exists": True, "$ne": "ALL"}},
        {"ehr_id": 1, "_id": 0}
    ))
    specific_ehr_ids = {c["ehr_id"] for c in specific_consents}

    def is_accessible(record):
        """Return True if this doctor has broad or specific-record consent."""
        return (
            record.get("patient_user_id") in broad_patient_ids
            or record.get("ehr_id") in specific_ehr_ids
        )

    def display_accessible_record(record):
        log_audit(action="READ", resource=record.get("ehr_id"), status="Success")
        sens_icon = {"Normal": "🟢", "Confidential": "🟠", "Restricted": "🔴"}.get(record.get("sensitivity"), "⚪")
        status_icon = "✅" if record.get("status") == "Active" else "📦"
        with st.expander(f"{sens_icon} {record.get('ehr_id')} — {record.get('patient_name')} | {status_icon} {record.get('status')}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Email:** {record.get('patient_email')}")
                st.write(f"**Age:** {record.get('age')}")
                st.write(f"**Gender:** {record.get('gender')}")
                st.write(f"**Blood Group:** {record.get('blood_group')}")
                st.write(f"**Diagnosis:** {record.get('diagnosis')}")
            with col2:
                st.write(f"**Treatment:** {record.get('treatment')}")
                st.write(f"**Doctor:** {record.get('primary_doctor')}")
                st.write(f"**Sensitivity:** {record.get('sensitivity')}")
                st.write(f"**Status:** {record.get('status')}")
                st.write(f"**Created:** {record.get('created_at')}")
            st.write(f"**Symptoms:** {record.get('symptoms')}")

            # Display Emergency Notes if any exist
            emergency_notes = record.get("emergency_notes", [])
            if emergency_notes:
                st.markdown("---")
                st.markdown("🚨 **Emergency Updates**")
                for note in emergency_notes:
                    st.warning(f"**{note['timestamp'][:16].replace('T', ' ')}** (by {note['added_by']}):\n{note['note']}")

    if view_mode == "Search by EHR ID":
        ehr_id_input = st.text_input("Enter EHR ID (e.g. EHR-123456)")
        if st.button("🔍 Search"):
            record = db.ehr_records.find_one({"ehr_id": ehr_id_input}, {"_id": 0})
            if record and is_accessible(record):
                display_accessible_record(record)
            else:
                st.error("❌ No record found with that EHR ID.")

    elif view_mode == "Search by Name":
        name_input = st.text_input("Enter Patient Name (partial name works)")
        if st.button("🔍 Search"):
            all_records = list(db.ehr_records.find(
                {"patient_name": {"$regex": name_input, "$options": "i"}},
                {"_id": 0}
            ))
            records = [r for r in all_records if is_accessible(r)]
            if records:
                st.caption(f"Found **{len(records)}** accessible record(s)")
                for rec in records:
                    display_accessible_record(rec)
            else:
                st.error("❌ No records found with that name.")

    elif view_mode == "Search by Email":
        email_input = st.text_input("Enter Patient Email")
        if st.button("🔍 Search"):
            all_records = list(db.ehr_records.find(
                {"patient_email": email_input},
                {"_id": 0}
            ))
            records = [r for r in all_records if is_accessible(r)]
            if records:
                st.caption(f"Found **{len(records)}** accessible record(s)")
                for rec in records:
                    display_accessible_record(rec)
            else:
                st.error("❌ No records found with that email.")

    elif view_mode == "Search by Patient User ID":
        uid_input = st.text_input("Enter Patient User ID (USR-XXXXXX)")
        if st.button("🔍 Search"):
            all_records = list(db.ehr_records.find(
                {"patient_user_id": uid_input},
                {"_id": 0}
            ))
            records = [r for r in all_records if is_accessible(r)]
            if records:
                st.caption(f"Found **{len(records)}** accessible record(s)")
                for rec in records:
                    display_accessible_record(rec)
            else:
                st.error("❌ No records found for that User ID.")

    else:  # View All
        conditions = []
        if broad_patient_ids:
            conditions.append({"patient_user_id": {"$in": list(broad_patient_ids)}})
        if specific_ehr_ids:
            conditions.append({"ehr_id": {"$in": list(specific_ehr_ids)}})
        if conditions:
            query = {"$or": conditions} if len(conditions) > 1 else conditions[0]
            records = list(db.ehr_records.find(query, {"_id": 0}))
        else:
            records = []
        if records:
            st.caption(f"Total accessible records: **{len(records)}**")
            for rec in records:
                display_accessible_record(rec)
        else:
            st.info("No accessible records found. Patients need to grant you access first.")
