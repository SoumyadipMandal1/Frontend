import streamlit as st
from datetime import datetime
# Updated imports to match new project structure
from ..db import get_db
from ..utils import log_audit

def render_break_glass_access():
    db = get_db()
    st.markdown("### Break-Glass Emergency Access")
    st.warning("⚠️ Break-Glass access is for **emergencies only**. All access is **session-based** — it expires when you log out. Access is fully audited.")

    bg_mode = st.radio("", ["Request Emergency Access", "Emergency Update (Append Note)", "View Break-Glass Logs"], horizontal=True)

    # Session store: { ehr_id: { reason, granted_at } }
    if "bg_session" not in st.session_state:
        st.session_state["bg_session"] = {}

    # ── Request Emergency Access ──────────────────────────────────────
    if bg_mode == "Request Emergency Access":
        st.info("🔑 Access granted here is **valid for this session only**. If you log out, you must Break-Glass again.")
        with st.form("break_glass_form"):
            col1, col2 = st.columns(2)
            with col1:
                target_ehr = st.text_input("Target EHR ID")
            with col2:
                reason = st.text_area("Emergency Reason (required)")
            submitted = st.form_submit_button("🚨 Request Emergency Access")

        if submitted:
            if not target_ehr or not reason:
                st.error("❌ EHR ID and reason are required!")
            else:
                record = db.ehr_records.find_one({"ehr_id": target_ehr}, {"_id": 0})
                if record:
                    # Store in session_state ONLY — never touches ehr_consent
                    st.session_state["bg_session"][target_ehr] = {
                        "reason":     reason,
                        "granted_at": datetime.now().isoformat()
                    }
                    log_audit(action="BREAK-GLASS", resource=target_ehr,
                              status="Success", reason=reason)
                    st.success(f"✅ Emergency access granted to **{target_ehr}** for this session.")
                    st.warning("⚠️ This access is logged, will be reviewed, and expires when you log out.")
                    
                    # Display nicely formatted record, maintaining data masking rules
                    with st.expander(f"🚨 Emergency View: {target_ehr} — {record.get('patient_name')}", expanded=True):
                        c1, c2 = st.columns(2)
                        with c1:
                            st.write(f"**Patient:** {record.get('patient_name')} ({record.get('age')} yrs, {record.get('gender')})")
                            st.write(f"**Blood Group:** {record.get('blood_group')}")
                            st.markdown("*(Contact & Address hidden for emergency view)*")
                        with c2:
                            st.write(f"**Primary Doctor:** {record.get('primary_doctor')}")
                            st.write(f"**Status:** {record.get('status')}")
                            st.write(f"**Sensitivity:** {record.get('sensitivity')}")
                        st.divider()
                        st.write(f"**Symptoms:** {record.get('symptoms')}")
                        st.write(f"**Diagnosis:** {record.get('diagnosis')}")
                        st.write(f"**Treatment:** {record.get('treatment')}")
                        
                        emergency_notes = record.get("emergency_notes", [])
                        if emergency_notes:
                            st.markdown("---")
                            st.markdown("🚨 **Previous Emergency Updates**")
                            for note in emergency_notes:
                                st.warning(f"**{note['timestamp'][:16].replace('T', ' ')}** (by {note['added_by']}):\n{note['note']}")
                else:
                    st.error("❌ EHR record not found.")

        # Show all currently active Break-Glass records this session
        if st.session_state["bg_session"]:
            st.markdown("---")
            st.markdown("#### 🔓 Active Emergency Access This Session")
            for eid, meta in st.session_state["bg_session"].items():
                st.info(f"🚨 **{eid}** — Reason: _{meta['reason']}_ | Granted at: {meta['granted_at']}")

    # ── Emergency Update (Append Note) ───────────────────────────────
    elif bg_mode == "Emergency Update (Append Note)":
        st.info("📝 You can **append** an emergency note to any record you have active Break-Glass access to. Original data is **never overwritten**.")

        active_eids = list(st.session_state.get("bg_session", {}).keys())
        if not active_eids:
            st.error("🚫 You have no active Break-Glass session access. Request emergency access first.")
        else:
            with st.form("bg_update_form"):
                selected_ehr = st.selectbox("Select EHR Record (active Break-Glass sessions only)", active_eids)
                emergency_note = st.text_area("Emergency Note (treatment given, observations, allergic reaction, etc.)")
                submitted = st.form_submit_button("💾 Append Emergency Note")

            if submitted:
                if not emergency_note:
                    st.error("❌ Note cannot be empty.")
                else:
                    note_entry = {
                        "note":      emergency_note,
                        "added_by":  st.session_state.get("user_name"),
                        "doctor_id": st.session_state.get("user_id"),
                        "timestamp": datetime.now().isoformat(),
                        "type":      "EMERGENCY"
                    }
                    # $push appends to emergency_notes array — never overwrites existing fields
                    db.ehr_records.update_one(
                        {"ehr_id": selected_ehr},
                        {"$push": {"emergency_notes": note_entry}}
                    )
                    log_audit(
                        action="EMERGENCY_UPDATE",
                        resource=selected_ehr,
                        status="Success",
                        reason=st.session_state["bg_session"][selected_ehr]["reason"]
                    )
                    st.success(f"✅ Emergency note appended to **{selected_ehr}** and logged as **EMERGENCY_UPDATE**.")

    # ── View Break-Glass Logs ─────────────────────────────────────────
    elif bg_mode == "View Break-Glass Logs":
        st.markdown("#### Break-Glass Access History")
        bg_logs = list(db.audit_logs.find(
            {"action": "BREAK-GLASS"}, {"_id": 0}
        ).sort("timestamp", -1))

        if bg_logs:
            st.caption(f"Total emergency access events: **{len(bg_logs)}**")
            for log in bg_logs:
                with st.expander(f"🚨 {log.get('log_id')} | {log.get('user')} | {log.get('timestamp')}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**User:** {log.get('user')}")
                        st.write(f"**User ID:** {log.get('user_id')}")
                        st.write(f"**Role:** {log.get('role')}")
                    with col2:
                        st.write(f"**EHR Accessed:** {log.get('resource')}")
                        st.write(f"**Status:** {log.get('status')}")
                        st.write(f"**Reason:** {log.get('reason')}")
        else:
            st.info("No break-glass access events recorded yet.")
