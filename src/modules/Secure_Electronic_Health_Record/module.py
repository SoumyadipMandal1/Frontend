import streamlit as st
from db import get_db

from doctor_tabs.add_ehr_record import render_add_ehr_record
from doctor_tabs.view_record import render_view_records
from doctor_tabs.update_ehr_record import render_update_ehr_record
from doctor_tabs.delete_archive_ehr import render_delete_archive_ehr
from doctor_tabs.audit_trail import render_audit_trail
from doctor_tabs.security_policy import render_security_policies
from doctor_tabs.break_glass_access import render_break_glass_access

from patient_tabs.my_records import render_my_records
from patient_tabs.grant_access import render_grant_access
from patient_tabs.my_audit_trail import render_my_audit_trail

def show_module_g1():
    db = get_db()
    role = st.session_state.get("role", "Doctor")

    st.markdown("**Category G — Secure EHR & Access Control** › G1")
    st.markdown("# 🔒 Secure Electronic Health Record (EHR) Database")
    st.markdown(f"*Logged in as: **{st.session_state.get('user_name', '')}** | Role: **{role}***")

    total_ehrs    = db.ehr_records.count_documents({})
    total_audits  = db.audit_logs.count_documents({})
    denied_access = db.audit_logs.count_documents({"status": "DENIED"})
    active_ehrs   = db.ehr_records.count_documents({"status": "Active"})

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📂 Total EHRs",    total_ehrs)
    col2.metric("✅ Active EHRs",   active_ehrs)
    col3.metric("📋 Audit Logs",    total_audits)
    col4.metric("🚫 Access Denied", denied_access)

    st.divider()

    if role == "Patient":
        tabs = ["📂 My Records", "🔐 Grant Access", "📋 My Audit Trail"]
    else:
        tabs = [
            "📝 Add EHR Record", "🔍 View Records", "✏️ Update EHR Record",
            "🗑️ Delete/Archive EHR", "📋 Audit Trail", "🛡️ Security Policies",
            "🚨 Break-Glass Access"
        ]

    tab = st.radio("", tabs, horizontal=True, key="g1_tabs")
    st.divider()

    if tab == "📝 Add EHR Record":
        render_add_ehr_record()
    elif tab == "🔍 View Records":
        render_view_records()
    elif tab == "✏️ Update EHR Record":
        render_update_ehr_record()
    elif tab == "🗑️ Delete/Archive EHR":
        render_delete_archive_ehr()
    elif tab == "📋 Audit Trail":
        render_audit_trail()
    elif tab == "🛡️ Security Policies":
        render_security_policies()
    elif tab == "🚨 Break-Glass Access":
        render_break_glass_access()
    elif tab == "📂 My Records":
        render_my_records()
    elif tab == "🔐 Grant Access":
        render_grant_access()
    elif tab == "📋 My Audit Trail":
        render_my_audit_trail()

    st.divider()
    if st.button("⬅ Back to Modules"):
        st.session_state.view = "category"
        st.rerun()