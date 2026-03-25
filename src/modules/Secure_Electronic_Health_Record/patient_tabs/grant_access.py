import streamlit as st
from datetime import datetime
from ..db import get_db
from ..utils import log_audit

def render_grant_access():
    db = get_db()
    st.markdown("### Consent Management — Grant or Revoke Doctor Access")
    st.info("💡 Use the modes below to control exactly which records each doctor can see.")

    patient_uid = st.session_state.get("user_id")

    # Fetch this patient's own EHR records for the specific-record dropdown
    my_records = list(db.ehr_records.find(
        {"patient_user_id": patient_uid, "status": "Active"},
        {"ehr_id": 1, "primary_doctor": 1, "diagnosis": 1, "_id": 0}
    ))
    ehr_options = {
        f"{r['ehr_id']} — Dr. {r.get('primary_doctor','?')} | {r.get('diagnosis','?')}": r["ehr_id"]
        for r in my_records
    }

    consent_mode = st.radio(
        "Consent Mode",
        [
            "1️⃣  All Records → All Doctors",
            "2️⃣  All Records → Specific Doctor",
            "3️⃣  Specific Record → Specific Doctor"
        ],
        horizontal=False,
        key="consent_mode_radio"
    )
    st.markdown("---")

    def upsert_consent(doctor_id, doctor_name, ehr_id, status):
        """Insert or update a consent record."""
        filter_q = {"patient_user_id": patient_uid, "doctor_user_id": doctor_id, "ehr_id": ehr_id}
        existing = db.ehr_consent.find_one(filter_q)
        if existing:
            db.ehr_consent.update_one(
                filter_q,
                {"$set": {"status": status, "updated_at": datetime.now().isoformat()}}
            )
        else:
            db.ehr_consent.insert_one({
                "patient_user_id": patient_uid,
                "doctor_user_id":  doctor_id,
                "doctor_name":     doctor_name,
                "ehr_id":          ehr_id,
                "status":          status,
                "created_at":      datetime.now().isoformat()
            })

    # ── MODE 1: All Records → All Doctors ────────────────────────────
    if consent_mode == "1️⃣  All Records → All Doctors":
        st.markdown("#### Grant / Revoke access to **all your records** for **every doctor** who has treated you")
        action = st.selectbox("Action", ["Grant", "Revoke"], key="mode1_action")
        if st.button("✅ Confirm", key="mode1_btn"):
            doctors_on_file = db.ehr_records.distinct("doctor_user_id", {"patient_user_id": patient_uid})
            if not doctors_on_file:
                st.warning("⚠️ No doctors found with records linked to your account.")
            else:
                status = "Granted" if action == "Grant" else "Revoked"
                count = 0
                for doc_uid in doctors_on_file:
                    doc = db.users.find_one({"user_id": doc_uid})
                    doc_name = doc.get("name", doc_uid) if doc else doc_uid
                    upsert_consent(doc_uid, doc_name, "ALL", status)
                    log_audit(action=f"CONSENT-{status.upper()}", resource=doc_uid, status="Success")
                    count += 1
                verb = "Granted to" if status == "Granted" else "Revoked from"
                st.success(f"✅ Access **{verb}** {count} doctor(s) for all your records.")

    # ── MODE 2: All Records → Specific Doctor ─────────────────────────
    elif consent_mode == "2️⃣  All Records → Specific Doctor":
        st.markdown("#### Grant / Revoke access to **all your records** for a **specific doctor**")
        with st.form("mode2_form"):
            doctor_user_id = st.text_input("Doctor's User ID (USR-XXXXXX)")
            action         = st.selectbox("Action", ["Grant", "Revoke"])
            submitted      = st.form_submit_button("✅ Confirm")
        if submitted:
            if not doctor_user_id:
                st.error("❌ Doctor User ID is required!")
            else:
                doctor = db.users.find_one({"user_id": doctor_user_id, "role": "Doctor"})
                if not doctor:
                    st.error("❌ No doctor found with that User ID!")
                else:
                    status = "Granted" if action == "Grant" else "Revoked"
                    upsert_consent(doctor_user_id, doctor.get("name"), "ALL", status)
                    log_audit(action=f"CONSENT-{status.upper()}", resource=doctor_user_id, status="Success")
                    verb = "Granted to" if status == "Granted" else "Revoked from"
                    st.success(f"✅ Access **{verb}** Dr. **{doctor.get('name')}** for all your records.")

    # ── MODE 3: Specific Record → Specific Doctor ──────────────────────
    elif consent_mode == "3️⃣  Specific Record → Specific Doctor":
        st.markdown("#### Grant / Revoke access to a **specific record** for a **specific doctor**")
        if not ehr_options:
            st.warning("⚠️ No active EHR records found on your account to select from.")
        else:
            with st.form("mode3_form"):
                selected_label = st.selectbox("Select EHR Record", list(ehr_options.keys()))
                doctor_user_id = st.text_input("Doctor's User ID (USR-XXXXXX)")
                action         = st.selectbox("Action", ["Grant", "Revoke"])
                submitted      = st.form_submit_button("✅ Confirm")
            if submitted:
                if not doctor_user_id:
                    st.error("❌ Doctor User ID is required!")
                else:
                    doctor = db.users.find_one({"user_id": doctor_user_id, "role": "Doctor"})
                    if not doctor:
                        st.error("❌ No doctor found with that User ID!")
                    else:
                        chosen_ehr = ehr_options[selected_label]
                        status = "Granted" if action == "Grant" else "Revoked"
                        upsert_consent(doctor_user_id, doctor.get("name"), chosen_ehr, status)
                        log_audit(
                            action=f"CONSENT-{status.upper()}",
                            resource=f"{doctor_user_id}:{chosen_ehr}",
                            status="Success"
                        )
                        verb = "Granted to" if status == "Granted" else "Revoked from"
                        st.success(f"✅ Access **{verb}** Dr. **{doctor.get('name')}** for record **{chosen_ehr}**.")

    # ── Current Access Grants ───────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 📋 Current Access Grants")
    consents = list(db.ehr_consent.find({"patient_user_id": patient_uid}, {"_id": 0}))
    if consents:
        for c in consents:
            badge       = "✅" if c.get("status") == "Granted" else "🚫"
            scope       = c.get("ehr_id", "ALL")
            scope_label = "All Records" if (not scope or scope == "ALL") else f"Record `{scope}`"
            st.write(f"{badge} Dr. **{c.get('doctor_name')}** (`{c.get('doctor_user_id')}`) — {scope_label} — **{c.get('status')}**")
    else:
        st.info("You haven't granted access to any doctor yet.")
