"""
Vendored Pydantic models for all 11 DPW layer contracts.

Change LAYER_ID to your layer number (1-11) before implementing invoke().
CONTRACT_VERSION matches the platform contract version this was vendored from.
"""

from pydantic import BaseModel
from typing import Literal

# ── Configuration ──────────────────────────────────────────────────────────────

LAYER_ID = 1  # Change this to your layer number (1-11)

CONTRACT_VERSION = "2.0"  # Sync date: 2026-04-19


# ── Layer 1 — Awareness ────────────────────────────────────────────────────────

class AwarenessContext(BaseModel):
    household_size: int | None = None
    has_children: bool | None = None
    approximate_income: str | None = None
    age_range: str | None = None

    model_config = {"extra": "allow"}


class Layer1Request(BaseModel):
    case_id: str
    state_code: str
    layer_id: Literal[1] = 1
    program_filter: list[str] = []
    context: AwarenessContext | None = None


class BenefitProgram(BaseModel):
    code: str
    name: str
    description: str
    eligibility_hint: str | None = None
    how_to_apply: str | None = None
    program_url: str | None = None


class Layer1Response(BaseModel):
    case_id: str
    status: Literal["found", "not_found", "error"]
    message: str
    programs: list[BenefitProgram] = []


# ── Layer 2 — Application ──────────────────────────────────────────────────────

class Layer2Request(BaseModel):
    case_id: str
    state_code: str
    layer_id: Literal[2] = 2
    applicant_identifier: str
    program_codes: list[str]
    application_data: dict


class Layer2Response(BaseModel):
    case_id: str
    status: Literal["submitted", "draft", "error"]
    message: str
    application_id: str | None = None
    confirmation_number: str | None = None


# ── Layer 3 — Case Initiation ──────────────────────────────────────────────────

class Layer3Request(BaseModel):
    case_id: str
    state_code: str
    layer_id: Literal[3] = 3
    application_id: str
    worker_id: str | None = None


class Layer3Response(BaseModel):
    case_id: str
    status: Literal["initiated", "duplicate", "error"]
    message: str
    assigned_worker_id: str | None = None


# ── Layer 4 — Exception Handling ───────────────────────────────────────────────

class Layer4Request(BaseModel):
    case_id: str
    state_code: str
    layer_id: Literal[4] = 4
    exception_type: str
    exception_data: dict
    source_layer_id: int


class Layer4Response(BaseModel):
    case_id: str
    status: Literal["resolved", "escalated", "pending"]
    message: str
    resolution_notes: str | None = None


# ── Layer 5 — Verification ─────────────────────────────────────────────────────

class Layer5Request(BaseModel):
    case_id: str
    state_code: str
    layer_id: Literal[5] = 5
    applicant_identifier: str
    verification_types: list[Literal["identity", "income", "residency", "household"]]
    consent_token: str


class Layer5Response(BaseModel):
    case_id: str
    status: Literal["verified", "partial", "failed", "pending"]
    message: str
    verification_results: dict | None = None


# ── Layer 6 — External Validation ─────────────────────────────────────────────

class Layer6Request(BaseModel):
    case_id: str
    state_code: str
    layer_id: Literal[6] = 6
    data_sources: list[str]
    validation_queries: dict


class Layer6Response(BaseModel):
    case_id: str
    status: Literal["validated", "discrepancy", "unavailable"]
    message: str
    validation_results: dict | None = None


# ── Layer 7 — Document Upload ──────────────────────────────────────────────────

class Layer7Request(BaseModel):
    case_id: str
    state_code: str
    layer_id: Literal[7] = 7
    document_type: str
    document_metadata: dict
    upload_url: str


class Layer7Response(BaseModel):
    case_id: str
    status: Literal["received", "rejected", "pending_review"]
    message: str
    document_id: str | None = None


# ── Layer 8 — Notice + RFI ─────────────────────────────────────────────────────

class Layer8Request(BaseModel):
    case_id: str
    state_code: str
    layer_id: Literal[8] = 8
    direction: Literal["outbound", "inbound"]
    notice_type: str
    content: dict
    response_deadline: str | None = None
    applicant_reference: str | None = None


class Layer8Response(BaseModel):
    case_id: str
    status: Literal["sent", "received", "acknowledged"]
    message: str
    notice_id: str | None = None


# ── Layer 9 — Eligibility + Enrollment ────────────────────────────────────────

class Layer9Request(BaseModel):
    case_id: str
    state_code: str
    layer_id: Literal[9] = 9
    program_codes: list[str]
    determination_data: dict


class Layer9Response(BaseModel):
    case_id: str
    status: Literal["eligible", "ineligible", "pending", "partial"]
    message: str
    eligible_programs: list[str] = []
    ineligible_reasons: dict = {}
    enrollment_details: dict = {}


# ── Layer 10 — Benefit Distribution ───────────────────────────────────────────

class Layer10Request(BaseModel):
    case_id: str
    state_code: str
    layer_id: Literal[10] = 10
    program_code: str
    distribution_method: Literal["eft", "ebt", "check", "voucher"]
    benefit_amount: float | None = None
    distribution_period: dict


class Layer10Response(BaseModel):
    case_id: str
    status: Literal["scheduled", "issued", "failed"]
    message: str
    distribution_id: str | None = None


# ── Layer 11 — Appeals ─────────────────────────────────────────────────────────

class Layer11Request(BaseModel):
    case_id: str
    state_code: str
    layer_id: Literal[11] = 11
    appeal_type: Literal["denial", "reduction", "termination"]
    appealed_layer_id: int
    appeal_grounds: str
    supporting_data: dict


class Layer11Response(BaseModel):
    case_id: str
    status: Literal["filed", "under_review", "upheld", "overturned", "withdrawn"]
    message: str
    appeal_id: str | None = None
    hearing_date: str | None = None
    appealed_layer_id: int | None = None


# ── Auto-select based on LAYER_ID ──────────────────────────────────────────────

_REQUEST_MODELS = [
    Layer1Request, Layer2Request, Layer3Request, Layer4Request,
    Layer5Request, Layer6Request, Layer7Request, Layer8Request,
    Layer9Request, Layer10Request, Layer11Request,
]
_RESPONSE_MODELS = [
    Layer1Response, Layer2Response, Layer3Response, Layer4Response,
    Layer5Response, Layer6Response, Layer7Response, Layer8Response,
    Layer9Response, Layer10Response, Layer11Response,
]

LayerRequest = _REQUEST_MODELS[LAYER_ID - 1]
LayerResponse = _RESPONSE_MODELS[LAYER_ID - 1]

VALID_STATUSES = {
    1: ["found", "not_found", "error"],
    2: ["submitted", "draft", "error"],
    3: ["initiated", "duplicate", "error"],
    4: ["resolved", "escalated", "pending"],
    5: ["verified", "partial", "failed", "pending"],
    6: ["validated", "discrepancy", "unavailable"],
    7: ["received", "rejected", "pending_review"],
    8: ["sent", "received", "acknowledged"],
    9: ["eligible", "ineligible", "pending", "partial"],
    10: ["scheduled", "issued", "failed"],
    11: ["filed", "under_review", "upheld", "overturned", "withdrawn"],
}
