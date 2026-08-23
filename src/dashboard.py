"""Reusable presentation helpers for the NetSage AI Streamlit frontend.

This module intentionally contains no AI, rule-checking, or audit-log logic.
"""

from pathlib import Path
from html import escape

import pandas as pd
import streamlit as st

from src.checker import validate_case
from src.ai_engine import GeminiDiagnosisError, generate_ai_diagnosis
from src.logger import AUDIT_COLUMNS, get_recent_audit_entries, record_engineer_decision


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CASE_FILE_LOCATIONS = (
    PROJECT_ROOT / "data" / "cases.csv",
    PROJECT_ROOT / "data" / "data" / "cases.csv",
)


def apply_theme() -> None:
    """Apply the Cisco-inspired dark visual style used by every page."""
    st.markdown(
        """
        <style>
        .stApp { background: #071525; color: #e7f1ff; }
        [data-testid="stSidebar"] { background: #0b1f35; border-right: 1px solid #1e4f7c; }
        [data-testid="stSidebar"] .stRadio label { color: #c7ddf5; }
        [data-testid="stSidebar"] .stRadio label:hover { color: #35a7ff; }
        h1, h2, h3 { color: #f2f8ff !important; }
        .subtitle { color: #91b7dc; margin-top: -0.75rem; margin-bottom: 1.5rem; }
        .metric-card, .detail-card {
            background: linear-gradient(145deg, #0d2742, #0a1d32);
            border: 1px solid #1d557f;
            border-radius: 14px;
            padding: 1.15rem;
            height: 100%;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.18);
        }
        .metric-label { color: #9fc5e8; font-size: 0.88rem; }
        .metric-value { color: #39a9ff; font-weight: 700; font-size: 2rem; margin-top: 0.25rem; }
        .detail-label { color: #72bfff; font-size: 0.78rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; }
        .detail-value { color: #ebf5ff; font-size: 1rem; margin-top: 0.45rem; overflow-wrap: anywhere; }
        .severity-badge { border-radius: 999px; display: inline-block; font-size: 0.86rem; font-weight: 700; padding: 0.35rem 0.8rem; }
        .severity-high { background: #5e1b28; border: 1px solid #f1566c; color: #ffd6dc; }
        .severity-medium { background: #5c3a14; border: 1px solid #f4a340; color: #ffe3b8; }
        .severity-low { background: #164a38; border: 1px solid #35bd7a; color: #c6f7dc; }
        .severity-default { background: #26384c; border: 1px solid #7190b1; color: #d8e7f7; }
        .show-output {
            background: #050d17; border: 1px solid #1d557f; border-radius: 10px;
            color: #c8e5ff; font-family: Consolas, "Courier New", monospace;
            max-height: 220px; overflow: auto; padding: 1rem; white-space: pre-wrap;
        }
        [data-testid="stDataFrame"] { border: 1px solid #1d557f; border-radius: 10px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data
def load_cases() -> pd.DataFrame:
    """Load the first available case CSV, returning an empty table if absent."""
    for case_file in CASE_FILE_LOCATIONS:
        if case_file.exists():
            try:
                return pd.read_csv(case_file).fillna("")
            except (OSError, pd.errors.ParserError):
                return pd.DataFrame()
    return pd.DataFrame()


def _field_value(case: pd.Series, *possible_names: str) -> str:
    """Find a field despite small differences in source CSV column spelling."""
    normalized_columns = {
        str(column).strip().lower().replace("_", " "): column for column in case.index
    }
    for name in possible_names:
        column = normalized_columns.get(name.lower().replace("_", " "))
        if column is not None:
            value = case[column]
            return str(value) if value != "" else "Not provided"
    return "Not provided"


def _metric_card(label: str, value: str) -> None:
    """Render one dashboard KPI card."""
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div></div>',
        unsafe_allow_html=True,
    )


def render_dashboard_page(cases: pd.DataFrame) -> None:
    """Render the read-only dashboard overview and placeholder charts."""
    total_cases = len(cases) if not cases.empty else 30
    st.title("Network Operations Dashboard")
    st.markdown('<p class="subtitle">Cisco-inspired troubleshooting overview</p>', unsafe_allow_html=True)

    metric_columns = st.columns(4)
    metrics = [
        ("Total Cases", str(total_cases)),
        ("Cases Reviewed", "0"),
        ("AI Accuracy", "0%"),
        ("Human Approval Rate", "0%"),
    ]
    for column, (label, value) in zip(metric_columns, metrics):
        with column:
            _metric_card(label, value)

    st.markdown("<br>", unsafe_allow_html=True)
    chart_columns = st.columns(2)
    # Static placeholder data keeps the frontend complete before analytics are added.
    with chart_columns[0]:
        st.subheader("Issue Distribution")
        st.bar_chart(pd.DataFrame({"Cases": [0, 0, 0, 0]}, index=["Routing", "Switching", "DNS", "Security"]))
    with chart_columns[1]:
        st.subheader("Severity Distribution")
        st.bar_chart(pd.DataFrame({"Cases": [0, 0, 0, 0]}, index=["Critical", "High", "Medium", "Low"]))


def _detail_card(label: str, value: str) -> None:
    """Render a single read-only case attribute."""
    st.markdown(
        f'<div class="detail-card"><div class="detail-label">{label}</div>'
        f'<div class="detail-value">{escape(value)}</div></div>',
        unsafe_allow_html=True,
    )


def _severity_card(severity: str) -> None:
    """Render a colored severity badge using the case's priority level."""
    severity_name = severity.strip().lower()
    badge_class = {
        "high": "severity-high",
        "medium": "severity-medium",
        "low": "severity-low",
    }.get(severity_name, "severity-default")
    st.markdown(
        '<div class="detail-card"><div class="detail-label">Severity</div>'
        f'<div class="detail-value"><span class="severity-badge {badge_class}">{escape(severity)}</span></div></div>',
        unsafe_allow_html=True,
    )


def _severity_badge(severity: str) -> str:
    """Create the colored severity badge used inside validation result cards."""
    badge_class = {
        "high": "severity-high",
        "medium": "severity-medium",
        "low": "severity-low",
    }.get(severity.strip().lower(), "severity-default")
    return f'<span class="severity-badge {badge_class}">{escape(severity)}</span>'


def _render_validation_results(results: dict) -> None:
    """Show rule-checker findings in expandable cards for engineer review."""
    # The checker contract uses lowercase `status` and `flagged_issues` keys.
    st.markdown(f"**Status:** {escape(results['status'])}")
    if results["status"] == "SUCCESS":
        st.success("✅ No deterministic issues detected.")
        return

    st.success("✅ Validation Completed Successfully")
    st.subheader("Validation Results")
    for finding in results["flagged_issues"]:
        with st.expander(f"{finding['check_id']} · {finding['issue']}", expanded=True):
            st.markdown(f"**Issue:** {escape(finding['issue'])}")
            st.markdown(f"**OSI Layer:** {escape(finding['osi_layer'])}")
            st.markdown(f"**Severity:** {_severity_badge(finding['severity'])}", unsafe_allow_html=True)
            st.markdown("**Evidence from show output**")
            st.code(finding["evidence"], language="text")
            st.markdown(f"**Recommended Fix:** {escape(finding['recommended_fix'])}")


def _show_outputs_card(show_outputs: str) -> None:
    """Render Cisco command output in a vertically scrollable, code-style panel."""
    st.markdown(
        '<div class="detail-card"><div class="detail-label">Captured Show Outputs</div>'
        f'<pre class="show-output">{escape(show_outputs)}</pre></div>',
        unsafe_allow_html=True,
    )


def render_case_review_page(cases: pd.DataFrame) -> None:
    """Render selectable case details without performing diagnosis or validation."""
    st.title("Case Review")
    st.markdown('<p class="subtitle">Review provided network cases and supporting information.</p>', unsafe_allow_html=True)

    if cases.empty or "case_id" not in cases.columns:
        st.info("No case records are available yet. Add rows with a `case_id` column to `data/cases.csv`.")
        return

    case_ids = cases["case_id"].astype(str).tolist()
    selected_id = st.selectbox("Select Case ID", case_ids)
    selected_case = cases.loc[cases["case_id"].astype(str) == selected_id].iloc[0]

    # Present the textual case fields in cards; diagnostics are deliberately not run here.
    fields = [
        ("Case ID", _field_value(selected_case, "case_id", "case id")),
        ("Symptom", _field_value(selected_case, "symptom", "description")),
        ("Topology Note", _field_value(selected_case, "topology_note", "topology note")),
        ("Expected Fault", _field_value(selected_case, "expected_fault", "expected fault")),
        ("OSI Layer", _field_value(selected_case, "osi_layer", "osi layer")),
        ("Concept Tag", _field_value(selected_case, "concept_tag", "concept tag")),
    ]
    for start in range(0, len(fields), 2):
        row = st.columns(2)
        for column, (label, value) in zip(row, fields[start : start + 2]):
            with column:
                _detail_card(label, value)
        st.markdown("<div style='height: 0.75rem'></div>", unsafe_allow_html=True)

    output_and_severity = st.columns([3, 1])
    with output_and_severity[0]:
        _show_outputs_card(_field_value(selected_case, "show_outputs", "show outputs"))
        # This visual-only trigger remains available for every selected case.
        validation_requested = st.button(
            "🔍 Run Validation",
            type="primary",
            key=f"run_validation_{selected_id}",
        )
    with output_and_severity[1]:
        _severity_card(_field_value(selected_case, "severity", "status"))

    # Rule validation is deterministic and local; no Gemini or external AI is called.
    if validation_requested:
        with st.spinner("Running deterministic rule validation..."):
            validation_result = validate_case(_field_value(selected_case, "show_outputs", "show outputs"))
        # Print the complete JSON-compatible result for development debugging.
        print(validation_result)
        _render_validation_results(validation_result)


def _render_ai_diagnosis(diagnosis: dict) -> None:
    """Present a completed Gemini diagnosis without offering any apply action."""
    st.subheader("AI Diagnosis")
    summary_columns = st.columns(2)
    with summary_columns[0]:
        _detail_card("Root Cause", str(diagnosis["root_cause"]))
    with summary_columns[1]:
        _detail_card("Confidence", f"{float(diagnosis['confidence']):.0%}")

    st.markdown("<div style='height: 0.75rem'></div>", unsafe_allow_html=True)
    _detail_card("Reasoning", str(diagnosis["reasoning"]))
    st.markdown("<div style='height: 0.75rem'></div>", unsafe_allow_html=True)

    detail_columns = st.columns(2)
    with detail_columns[0]:
        with st.expander("Evidence", expanded=True):
            for item in diagnosis["evidence"]:
                st.markdown(f"- {item}")
        with st.expander("Next Commands", expanded=True):
            st.code("\n".join(diagnosis["next_commands"]), language="text")
    with detail_columns[1]:
        with st.expander("Recommended Fix (Review Only)", expanded=True):
            st.code("\n".join(diagnosis["recommended_fix"]), language="text")
        approval_text = "Human approval required" if diagnosis["human_approval_required"] else "No approval flag returned"
        st.warning(f"⚠️ {approval_text}. No configuration changes are applied by NetSage AI.")


def _render_engineer_review(case_id: str, diagnosis: dict) -> None:
    """Render and persist the human engineer's review of an AI diagnosis."""
    st.markdown("---")
    st.subheader("👨‍💻 Engineer Review")
    decision_key = f"engineer_decision_{case_id}"
    decision_columns = st.columns(3)

    # These buttons select a decision; saving happens only through Submit Decision.
    with decision_columns[0]:
        if st.button("✅ Approve", key=f"approve_{case_id}", use_container_width=True):
            st.session_state[decision_key] = "Approve"
    with decision_columns[1]:
        if st.button("✏️ Edit Recommendation", key=f"edit_{case_id}", use_container_width=True):
            st.session_state[decision_key] = "Edit Recommendation"
    with decision_columns[2]:
        if st.button("❌ Reject", key=f"reject_{case_id}", use_container_width=True):
            st.session_state[decision_key] = "Reject"

    selected_decision = st.session_state.get(decision_key)
    if selected_decision:
        st.caption(f"Selected decision: {selected_decision}")

    engineer_notes = st.text_area("Engineer Notes", key=f"engineer_notes_{case_id}")
    if st.button("Submit Decision", type="primary", key=f"submit_review_{case_id}"):
        if not selected_decision:
            st.warning("Select Approve, Edit Recommendation, or Reject before submitting.")
        else:
            record_engineer_decision(case_id, diagnosis, selected_decision, engineer_notes)
            st.success("✅ Decision recorded successfully.")

    st.markdown("#### Recent Audit Entries")
    recent_entries = get_recent_audit_entries()
    st.dataframe(recent_entries[AUDIT_COLUMNS], use_container_width=True, hide_index=True)


def render_ai_diagnosis_page(cases: pd.DataFrame) -> None:
    """Render the opt-in Gemini diagnosis workflow for a selected troubleshooting case."""
    st.title("AI Diagnosis")
    st.markdown('<p class="subtitle">Generate an advisory diagnosis for human engineering review.</p>', unsafe_allow_html=True)

    if cases.empty or "case_id" not in cases.columns:
        st.info("No case records are available yet. Add rows with a `case_id` column to `data/cases.csv`.")
        return

    case_ids = cases["case_id"].astype(str).tolist()
    selected_id = st.selectbox("Select Case ID", case_ids, key="ai_diagnosis_case")
    selected_case = cases.loc[cases["case_id"].astype(str) == selected_id].iloc[0]
    symptom = _field_value(selected_case, "symptom", "description")
    topology_note = _field_value(selected_case, "topology_note", "topology note")
    show_outputs = _field_value(selected_case, "show_outputs", "show outputs")
    rule_checker_result = validate_case(show_outputs)

    st.caption("Uses the selected case and its deterministic rule-checker result. Recommendations are never applied automatically.")
    if st.button("🤖 Generate AI Diagnosis", type="primary", key=f"generate_ai_{selected_id}"):
        with st.spinner("Generating Gemini diagnosis..."):
            try:
                diagnosis = generate_ai_diagnosis(symptom, topology_note, show_outputs, rule_checker_result)
            except GeminiDiagnosisError as error:
                st.error(f"Unable to generate an AI diagnosis right now. {error}")
                return

        st.session_state["ai_diagnosis_result"] = diagnosis
        st.session_state["ai_diagnosis_result_case"] = selected_id

    if st.session_state.get("ai_diagnosis_result_case") == selected_id:
        diagnosis = st.session_state["ai_diagnosis_result"]
        _render_ai_diagnosis(diagnosis)
        _render_engineer_review(selected_id, diagnosis)


def render_placeholder_page() -> None:
    """Render the AI page placeholder requested for this frontend-only stage."""
    st.title("AI Diagnosis")
    st.info("AI Diagnosis will be available after integrating the Gemini API.")


def render_audit_log_page() -> None:
    """Render a non-persistent audit log placeholder table."""
    st.title("Audit Log")
    st.markdown('<p class="subtitle">Decision history will appear here once audit logging is implemented.</p>', unsafe_allow_html=True)
    st.dataframe(
        pd.DataFrame(columns=["Timestamp", "Case ID", "AI Diagnosis", "Engineer Decision", "Notes"]),
        use_container_width=True,
        hide_index=True,
    )


def render_about_page() -> None:
    """Render a short introduction to NetSage AI."""
    st.title("About NetSage AI")
    st.write("NetSage AI is a Cisco Virtual Internship project for structured network troubleshooting.")
    st.write("It brings case review, guided diagnosis, and future engineering feedback into one workspace.")
    st.write("The dashboard is designed around a clear, Cisco-inspired network operations experience.")
    st.write("AI-assisted diagnosis and decision auditing will be added in later development stages.")
