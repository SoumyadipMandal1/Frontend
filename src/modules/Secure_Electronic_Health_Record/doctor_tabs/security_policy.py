import streamlit as st
from utils import SECURITY_POLICIES

def render_security_policies():
    st.markdown("### Security & Compliance Policies")
    st.info("📋 These are the security policies governing this EHR system. All policies are read-only.")

    compliance_filter = st.selectbox(
        "Filter by Compliance Standard",
        ["All", "HIPAA", "GDPR", "ISO 27001", "Local"]
    )

    filtered_policies = SECURITY_POLICIES if compliance_filter == "All" else [
        p for p in SECURITY_POLICIES if compliance_filter in p["compliance"]
    ]

    st.caption(f"Showing **{len(filtered_policies)}** of **{len(SECURITY_POLICIES)}** policies")
    st.markdown("---")

    for pol in filtered_policies:
        compliance_badges = " ".join([f"`{c}`" for c in pol["compliance"]])
        with st.expander(f"🛡️ {pol['policy_id']} — {pol['name']} | {compliance_badges}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Type:** {pol['type']}")
                st.write(f"**Status:** ✅ {pol['status']}")
            with col2:
                st.write(f"**Compliance:** {', '.join(pol['compliance'])}")
            st.write(f"**Description:** {pol['description']}")
