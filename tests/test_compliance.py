"""
DPW Layer App — Contract Compliance Tests

Run these against a live running server before registering your app.

    APP_URL=http://localhost:8000 DPW_API_KEY=test pytest tests/test_compliance.py -v

All 10 tests must pass. Tests 1-3 and 7-9 pass even before you implement
invoke() — the rest require a working implementation.
"""

import os
import pytest
import httpx
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import LAYER_ID, LayerRequest, VALID_STATUSES

APP_URL = os.environ.get("APP_URL", "http://localhost:8000")
DPW_API_KEY = os.environ.get("DPW_API_KEY", "test")
WRONG_KEY = "definitely-wrong-key-xyz"

# ── Minimal valid payloads per layer ──────────────────────────────────────────

_VALID_PAYLOADS = {
    1: {
        "case_id": "CASE-TEST-001",
        "state_code": "PA",
        "layer_id": 1,
        "applicant_identifier": "APPL-test-001",
        "channel": "email",
        "program_codes": ["SNAP"],
    },
    2: {
        "case_id": "CASE-TEST-001",
        "state_code": "PA",
        "layer_id": 2,
        "applicant_identifier": "APPL-test-001",
        "program_codes": ["SNAP"],
        "application_data": {"household_size": 2},
    },
    3: {
        "case_id": "CASE-TEST-001",
        "state_code": "PA",
        "layer_id": 3,
        "application_id": "APP-test-001",
    },
    4: {
        "case_id": "CASE-TEST-001",
        "state_code": "PA",
        "layer_id": 4,
        "exception_type": "test_exception",
        "exception_data": {"reason": "test"},
        "source_layer_id": 2,
    },
    5: {
        "case_id": "CASE-TEST-001",
        "state_code": "PA",
        "layer_id": 5,
        "applicant_identifier": "APPL-test-001",
        "verification_types": ["income"],
        "consent_token": "CONSENT-test-001",
    },
    6: {
        "case_id": "CASE-TEST-001",
        "state_code": "PA",
        "layer_id": 6,
        "data_sources": ["employer_records"],
        "validation_queries": {"employer_id": "EMP-001"},
    },
    7: {
        "case_id": "CASE-TEST-001",
        "state_code": "PA",
        "layer_id": 7,
        "document_type": "pay_stub",
        "document_metadata": {"filename": "stub.pdf", "size_bytes": 1024},
        "upload_url": "https://example.com/presigned/stub.pdf",
    },
    8: {
        "case_id": "CASE-TEST-001",
        "state_code": "PA",
        "layer_id": 8,
        "direction": "outbound",
        "notice_type": "rfi_income",
        "content": {"body": "Please provide income documentation."},
    },
    9: {
        "case_id": "CASE-TEST-001",
        "state_code": "PA",
        "layer_id": 9,
        "program_codes": ["SNAP"],
        "determination_data": {"household_size": 2, "monthly_income": 2000},
    },
    10: {
        "case_id": "CASE-TEST-001",
        "state_code": "PA",
        "layer_id": 10,
        "program_code": "SNAP",
        "distribution_method": "ebt",
        "distribution_period": {"start_date": "2026-05-01", "end_date": "2026-05-31", "frequency": "monthly"},
    },
    11: {
        "case_id": "CASE-TEST-001",
        "state_code": "PA",
        "layer_id": 11,
        "appeal_type": "denial",
        "appealed_layer_id": 9,
        "appeal_grounds": "Incorrectly calculated household income.",
        "supporting_data": {"evidence": "bank_statement_2026_03.pdf"},
    },
}

VALID_PAYLOAD = _VALID_PAYLOADS[LAYER_ID]
VALID_STATUSES_FOR_LAYER = VALID_STATUSES[LAYER_ID]


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_health_returns_ok():
    r = httpx.get(f"{APP_URL}/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_auth_rejects_missing_key():
    r = httpx.post(f"{APP_URL}/invoke", json=VALID_PAYLOAD)
    assert r.status_code == 422  # missing required header → FastAPI validation error


def test_auth_rejects_wrong_key():
    r = httpx.post(
        f"{APP_URL}/invoke",
        json=VALID_PAYLOAD,
        headers={"x-api-key": WRONG_KEY},
    )
    assert r.status_code == 401


def test_valid_request_returns_200():
    r = httpx.post(
        f"{APP_URL}/invoke",
        json=VALID_PAYLOAD,
        headers={"x-api-key": DPW_API_KEY},
    )
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"


def test_response_echoes_case_id():
    r = httpx.post(
        f"{APP_URL}/invoke",
        json=VALID_PAYLOAD,
        headers={"x-api-key": DPW_API_KEY},
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("case_id") == VALID_PAYLOAD["case_id"], (
        f"Response case_id '{body.get('case_id')}' != request case_id '{VALID_PAYLOAD['case_id']}'"
    )


def test_response_status_is_valid():
    r = httpx.post(
        f"{APP_URL}/invoke",
        json=VALID_PAYLOAD,
        headers={"x-api-key": DPW_API_KEY},
    )
    assert r.status_code == 200
    status = r.json().get("status")
    assert status in VALID_STATUSES_FOR_LAYER, (
        f"Status '{status}' not in valid values for layer {LAYER_ID}: {VALID_STATUSES_FOR_LAYER}"
    )


def test_response_has_message():
    r = httpx.post(
        f"{APP_URL}/invoke",
        json=VALID_PAYLOAD,
        headers={"x-api-key": DPW_API_KEY},
    )
    assert r.status_code == 200
    msg = r.json().get("message", "")
    assert isinstance(msg, str) and len(msg) > 0, "message field must be a non-empty string"


def test_missing_required_field_returns_422():
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "case_id"}
    r = httpx.post(
        f"{APP_URL}/invoke",
        json=payload,
        headers={"x-api-key": DPW_API_KEY},
    )
    assert r.status_code == 422, f"Expected 422 for missing case_id, got {r.status_code}"


def test_wrong_layer_id_returns_422():
    payload = {**VALID_PAYLOAD, "layer_id": 99}
    r = httpx.post(
        f"{APP_URL}/invoke",
        json=payload,
        headers={"x-api-key": DPW_API_KEY},
    )
    assert r.status_code == 422, f"Expected 422 for layer_id=99, got {r.status_code}"


def test_repeated_call_same_case_id():
    """Idempotency: calling with the same case_id twice must not cause a 500."""
    for _ in range(2):
        r = httpx.post(
            f"{APP_URL}/invoke",
            json=VALID_PAYLOAD,
            headers={"x-api-key": DPW_API_KEY},
        )
        assert r.status_code != 500, f"Server error on repeated call: {r.text}"
