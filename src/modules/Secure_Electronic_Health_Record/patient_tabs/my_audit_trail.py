import streamlit as st
from src.modules.Secure_Electronic_Health_Record.db import get_db

def render_my_audit_trail():
    db = get_db()
    st.markdown("### My Activity Log")
    patient_uid = st.session_state.get("user_id")
    logs = list(db.audit_logs.find(
        {"user_id": patient_uid}, {"_id": 0}
    ).sort("timestamp", -1))

    if logs:
        total   = len(logs)
        success = sum(1 for l in logs if l.get("status") == "Success")
        denied  = total - success

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Events",  total)
        col2.metric("✅ Successful", success)
        col3.metric("🚫 Denied",     denied)
        st.markdown("---")

        for log in logs:
            badge = "🔴" if log.get("status") == "DENIED" else "🟢"
            with st.expander(f"{badge} {log.get('action')} | {log.get('timestamp')}"):
                st.write(f"**Action:** {log.get('action')}")
                st.write(f"**Resource:** {log.get('resource')}")
                st.write(f"**Status:** {log.get('status')}")
                if log.get("reason"):
                    st.write(f"**Reason:** {log.get('reason')}")
    else:
        st.info("No activity recorded yet.")
