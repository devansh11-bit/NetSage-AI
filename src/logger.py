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


def ensure_audit_log() -> None:
    """Create the audit CSV with its required header when it does not yet exist."""
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not AUDIT_LOG_PATH.exists() or AUDIT_LOG_PATH.stat().st_size == 0:
        pd.DataFrame(columns=AUDIT_COLUMNS).to_csv(AUDIT_LOG_PATH, index=False)
        return

    try:
        existing_entries = pd.read_csv(AUDIT_LOG_PATH)
    except pd.errors.EmptyDataError:
        pd.DataFrame(columns=AUDIT_COLUMNS).to_csv(AUDIT_LOG_PATH, index=False)
        return
    except (OSError, pd.errors.ParserError) as error:
        raise ValueError("The existing audit log cannot be read safely.") from error
    if existing_entries.empty and list(existing_entries.columns) != AUDIT_COLUMNS:
        # Header-only placeholder files contain no reviews and may safely adopt this schema.
        pd.DataFrame(columns=AUDIT_COLUMNS).to_csv(AUDIT_LOG_PATH, index=False)
    elif not set(AUDIT_COLUMNS).issubset(existing_entries.columns):
        raise ValueError("The existing audit log has an incompatible schema and cannot be appended safely.")


def _audit_dataframe() -> pd.DataFrame:
    """Read audit records without changing any already stored decision rows."""
    ensure_audit_log()
    audit_entries = pd.read_csv(AUDIT_LOG_PATH)
    return audit_entries.dropna(how="all")


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
    ensure_audit_log()
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
    # Append mode protects all previous records from replacement on repeated submissions.
    new_entry.to_csv(AUDIT_LOG_PATH, mode="a", header=False, index=False)


def get_recent_audit_entries(limit: int = 10) -> pd.DataFrame:
    """Return the most recent audit rows for display in the Streamlit interface."""
    try:
        audit_entries = _audit_dataframe()
    except ValueError:
        return pd.DataFrame(columns=AUDIT_COLUMNS)
    return audit_entries.tail(limit).iloc[::-1]


def get_audit_log_download() -> bytes:
    """Return the complete audit CSV as downloadable UTF-8 bytes."""
    try:
        ensure_audit_log()
    except ValueError:
        return pd.DataFrame(columns=AUDIT_COLUMNS).to_csv(index=False).encode("utf-8")
    try:
        return AUDIT_LOG_PATH.read_bytes()
    except OSError:
        return pd.DataFrame(columns=AUDIT_COLUMNS).to_csv(index=False).encode("utf-8")
