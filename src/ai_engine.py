"""
Google Gemini integration for advisory NetSage AI diagnoses.
"""

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Load .env from the project root
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


DIAGNOSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "root_cause": {"type": "string"},
        "confidence": {"type": "number"},
        "reasoning": {"type": "string"},
        "evidence": {
            "type": "array",
            "items": {"type": "string"}
        },
        "next_commands": {
            "type": "array",
            "items": {"type": "string"}
        },
        "recommended_fix": {
            "type": "array",
            "items": {"type": "string"}
        },
        "human_approval_required": {"type": "boolean"},
    },
    "required": [
        "root_cause",
        "confidence",
        "reasoning",
        "evidence",
        "next_commands",
        "recommended_fix",
        "human_approval_required",
    ],
}


class GeminiDiagnosisError(Exception):
    """Custom exception for Gemini failures."""


def _build_prompt(
    symptom: str,
    topology_note: str,
    show_outputs: str,
    rule_checker_result: dict[str, Any],
) -> str:
    """Build the prompt sent to Gemini."""

    context = {
        "symptom": symptom,
        "topology_note": topology_note,
        "show_outputs": show_outputs,
        "rule_checker_result": rule_checker_result,
    }

    return f"""
You are an expert Cisco Network Engineer.

Analyze the following troubleshooting case.

Return ONLY valid JSON matching this schema.

Case:

{json.dumps(context, indent=2)}

Rules:
- Never execute changes.
- Only recommend fixes.
- Always require human approval.
"""


def _validate_response(data: dict[str, Any]) -> dict[str, Any]:
    """Validate Gemini response."""

    required = DIAGNOSIS_SCHEMA["required"]

    for key in required:
        if key not in data:
            raise GeminiDiagnosisError(f"Missing field: {key}")

    return data


def generate_ai_diagnosis(
    symptom: str,
    topology_note: str,
    show_outputs: str,
    rule_checker_result: dict[str, Any],
) -> dict[str, Any]:
    """Generate AI diagnosis using Gemini."""

    api_key = os.getenv("GEMINI_API_KEY")

    print("=" * 50)
    print("DEBUG")
    print("Working Directory:", os.getcwd())
    print("API KEY FOUND:", api_key is not None)
    print("API KEY:", api_key)
    print("=" * 50)

    if not api_key:
        raise GeminiDiagnosisError(
            "Gemini is not configured.\n\nCreate a .env file with:\n\nGEMINI_API_KEY=YOUR_API_KEY"
        )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=_build_prompt(
                symptom,
                topology_note,
                show_outputs,
                rule_checker_result,
            ),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=DIAGNOSIS_SCHEMA,
            ),
        )

        if not response.text:
            raise GeminiDiagnosisError("Gemini returned an empty response.")

        diagnosis = json.loads(response.text)

        return _validate_response(diagnosis)

    except json.JSONDecodeError as e:
        raise GeminiDiagnosisError(
            f"Invalid JSON returned by Gemini:\n{e}"
        )

    except Exception as e:
        raise GeminiDiagnosisError(
            f"Gemini API Error:\n\n{e}"
        )