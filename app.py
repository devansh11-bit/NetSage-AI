"""Streamlit entry point for the NetSage AI frontend."""

import streamlit as st

from src.dashboard import (
    apply_theme,
    render_ai_diagnosis_page,
    load_cases,
    render_about_page,
    render_audit_log_page,
    render_case_review_page,
    render_dashboard_page,
    render_placeholder_page,
)


# Configure the browser tab and default wide dashboard layout before rendering.
st.set_page_config(
    page_title="NetSage AI",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()

# This is navigation only; diagnosis and auditing are intentionally placeholders.
st.sidebar.markdown("## NetSage AI")
st.sidebar.caption("Cisco Virtual Internship")
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Case Review", "AI Diagnosis", "Audit Log", "About"],
    label_visibility="collapsed",
)
st.sidebar.markdown("---")
st.sidebar.caption("Network troubleshooting workspace")

# Case records are read-only frontend data for this stage of the project.
cases = load_cases()

if page == "Dashboard":
    render_dashboard_page(cases)
elif page == "Case Review":
    render_case_review_page(cases)
elif page == "AI Diagnosis":
    render_ai_diagnosis_page(cases)
elif page == "Audit Log":
    render_audit_log_page()
else:
    render_about_page()
