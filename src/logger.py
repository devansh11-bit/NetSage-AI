"""CSV audit-log helpers for recorded engineer review decisions."""

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUDIT_LOG_PATH = PROJECT_ROOT / "data" / "audit_log.csv"
AUDIT_COLUMNS = [
    "timestamp",
    "case_id",
    "ai_root_cause",
    "confidence",
    "engineer_decision",
    "engineer_notes",
    "final_status",
]


def _audit_dataframe() -> pd.DataFrame:
    """Read the audit CSV and add required columns without discarding prior records."""
    if not AUDIT_LOG_PATH.exists() or AUDIT_LOG_PATH.stat().st_size == 0:
        return pd.DataFrame(columns=AUDIT_COLUMNS)

    try:
        audit_entries = pd.read_csv(AUDIT_LOG_PATH)
    except pd.errors.EmptyDataError:
        audit_entries = pd.DataFrame(columns=AUDIT_COLUMNS)

    # A header-only legacy placeholder contains no decisions and can adopt the new schema.
    if audit_entries.empty:
        return pd.DataFrame(columns=AUDIT_COLUMNS)

    for column in AUDIT_COLUMNS:
        if column not in audit_entries.columns:
            audit_entries[column] = pd.NA
    return audit_entries


def _final_status(decision: str) -> str:
    """Map an engineer's review choice to a clear stored final status."""
    return {
        "Approve": "APPROVED",
        "Edit Recommendation": "PENDING_RECOMMENDATION_EDIT",
        "Reject": "REJECTED",
    }[decision]


def record_engineer_decision(
    case_id: str,
    ai_diagnosis: dict[str, Any],
    engineer_decision: str,
    engineer_notes: str,
) -> None:
    """Append one engineer decision while retaining all existing audit-log records."""
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing_entries = _audit_dataframe()
    new_entry = pd.DataFrame(
        [{
            "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
            "case_id": case_id,
            "ai_root_cause": ai_diagnosis["root_cause"],
            "confidence": ai_diagnosis["confidence"],
            "engineer_decision": engineer_decision,
            "engineer_notes": engineer_notes,
            "final_status": _final_status(engineer_decision),
        }]
    )
    combined_entries = pd.concat([existing_entries, new_entry], ignore_index=True)
    combined_entries.to_csv(AUDIT_LOG_PATH, index=False)


def get_recent_audit_entries(limit: int = 10) -> pd.DataFrame:
    """Return the most recent audit rows for display in the Streamlit interface."""
    audit_entries = _audit_dataframe()
    return audit_entries.tail(limit).iloc[::-1]
