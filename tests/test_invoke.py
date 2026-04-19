"""
Unit tests for invoke() in isolation (no HTTP server needed).

Fill in real assertions when you implement invoke() in app/invoke.py.
Run with: pytest tests/test_invoke.py -v
"""

import sys
import os
import asyncio
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import LAYER_ID, LayerRequest, LayerResponse, VALID_STATUSES

_VALID_PAYLOADS = {
    1: dict(case_id="test-123", state_code="PA", layer_id=1, applicant_identifier="APPL-001", channel="email", program_codes=["SNAP"]),
    2: dict(case_id="test-123", state_code="PA", layer_id=2, applicant_identifier="APPL-001", program_codes=["SNAP"], application_data={}),
    3: dict(case_id="test-123", state_code="PA", layer_id=3, application_id="APP-001"),
    4: dict(case_id="test-123", state_code="PA", layer_id=4, exception_type="test", exception_data={}, source_layer_id=2),
    5: dict(case_id="test-123", state_code="PA", layer_id=5, applicant_identifier="APPL-001", verification_types=["income"], consent_token="CONSENT-001"),
    6: dict(case_id="test-123", state_code="PA", layer_id=6, data_sources=["employer_records"], validation_queries={}),
    7: dict(case_id="test-123", state_code="PA", layer_id=7, document_type="pay_stub", document_metadata={}, upload_url="https://example.com/doc"),
    8: dict(case_id="test-123", state_code="PA", layer_id=8, direction="outbound", notice_type="rfi_income", content={}),
    9: dict(case_id="test-123", state_code="PA", layer_id=9, program_codes=["SNAP"], determination_data={}),
    10: dict(case_id="test-123", state_code="PA", layer_id=10, program_code="SNAP", distribution_method="ebt", distribution_period={}),
    11: dict(case_id="test-123", state_code="PA", layer_id=11, appeal_type="denial", appealed_layer_id=9, appeal_grounds="test", supporting_data={}),
}

SAMPLE_REQUEST = LayerRequest(**_VALID_PAYLOADS[LAYER_ID])


@pytest.mark.asyncio
async def test_invoke_returns_layer_response():
    from app.invoke import invoke
    resp = await invoke(SAMPLE_REQUEST)
    assert isinstance(resp, LayerResponse)


@pytest.mark.asyncio
async def test_invoke_echoes_case_id():
    from app.invoke import invoke
    resp = await invoke(SAMPLE_REQUEST)
    assert resp.case_id == SAMPLE_REQUEST.case_id


@pytest.mark.asyncio
async def test_invoke_returns_valid_status():
    from app.invoke import invoke
    resp = await invoke(SAMPLE_REQUEST)
    assert resp.status in VALID_STATUSES[LAYER_ID], (
        f"Status '{resp.status}' not valid for layer {LAYER_ID}: {VALID_STATUSES[LAYER_ID]}"
    )


@pytest.mark.asyncio
async def test_invoke_returns_nonempty_message():
    from app.invoke import invoke
    resp = await invoke(SAMPLE_REQUEST)
    assert isinstance(resp.message, str) and len(resp.message) > 0
