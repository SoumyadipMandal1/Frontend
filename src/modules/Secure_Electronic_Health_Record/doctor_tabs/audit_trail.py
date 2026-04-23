import streamlit as st
from db import get_db

def render_audit_trail():
    db = get_db()
    st.markdown("### Audit Trail — My Access Events")
    logs = list(db.audit_logs.find(
        {"user_id": st.session_state.get("user_id")},
        {"_id": 0}
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

        filter_status = st.selectbox("Filter by Status", ["All", "Success", "DENIED"])
        filtered = logs if filter_status == "All" else [l for l in logs if l.get("status") == filter_status]

        for log in filtered:
            badge = "🔴" if log.get("status") == "DENIED" else "🟢"
            with st.expander(f"{badge} {log.get('log_id')} | {log.get('action')} | {log.get('user')} | {log.get('timestamp')}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**User:** {log.get('user')}")
                    st.write(f"**User ID:** {log.get('user_id')}")
                    st.write(f"**Role:** {log.get('role')}")
                    st.write(f"**Action:** {log.get('action')}")
                with col2:
                    st.write(f"**Resource:** {log.get('resource')}")
                    st.write(f"**Status:** {log.get('status')}")
                    if log.get("reason"):
                        st.write(f"**Reason:** {log.get('reason')}")
    else:
        st.info("No audit logs yet.")
