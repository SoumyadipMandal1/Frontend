import streamlit as st
from ..db import get_db
from ..utils import log_audit

def render_my_records():
    db = get_db()
    st.markdown("### My EHR Records")
    st.success(f"🪪 Your User ID: **{st.session_state.get('user_id')}** — Share this with your doctor to link your records.")

    patient_uid = st.session_state.get("user_id")
    records     = list(db.ehr_records.find(
        {"patient_user_id": patient_uid, "status": "Active"},
        {"_id": 0}
    ))

    if records:
        st.caption(f"You have **{len(records)}** active EHR record(s)")
        for rec in records:
            sens_icon = {"Normal": "🟢", "Confidential": "🟠", "Restricted": "🔴"}.get(rec.get("sensitivity"), "⚪")
            with st.expander(f"{sens_icon} {rec.get('ehr_id')} | Dr. {rec.get('primary_doctor')} | {rec.get('created_at', '')[:10]}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Diagnosis:** {rec.get('diagnosis')}")
                    st.write(f"**Treatment:** {rec.get('treatment')}")
                    st.write(f"**Symptoms:** {rec.get('symptoms')}")
                with col2:
                    st.write(f"**Doctor:** {rec.get('primary_doctor')}")
                    st.write(f"**Blood Group:** {rec.get('blood_group')}")
                    st.write(f"**Sensitivity:** {rec.get('sensitivity')}")

                # Display Emergency Notes if any exist
                emergency_notes = rec.get("emergency_notes", [])
                if emergency_notes:
                    st.markdown("---")
                    st.markdown("🚨 **Emergency Updates**")
                    for note in emergency_notes:
                        st.warning(f"**{note['timestamp'][:16].replace('T', ' ')}** (by {note['added_by']}):\n{note['note']}")
        log_audit(action="READ", resource="MY_RECORDS", status="Success")
    else:
        st.info("No active EHR records found. Your doctor will add records after your visit.")
