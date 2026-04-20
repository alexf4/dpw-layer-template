# DPW Layer App — Agent & Developer Context

## What This Is

The **DPW Open Platform** is nonprofit infrastructure for state benefit systems. It solves a
structural problem: every US state rebuilds the same benefits technology from scratch. DPW breaks
that cycle by letting 3rd party developers build a tool once and deploy it to every state with a
config change.

**Your job**: implement `app/invoke.py` — a single async function. The platform calls it when a
case reaches your layer. Everything else (auth, routing, error formatting, retries) is pre-built.

A registered app covers one **layer** of the benefit stack. There are 11 layers:

| # | Layer | Direction | What it does |
|---|---|---|---|
| 1 | Awareness | State → Applicant | Pull catalog — returns state-specific benefit programs so Benne can present them to applicants |
| 2 | Application | Applicant → State | Receives and validates benefit applications |
| 3 | Case Initiation | Internal | Opens a case, assigns a worker |
| 4 | Exception Handling | Internal | Routes irregularities for resolution |
| 5 | Verification | Applicant → State | Verifies identity, income, residency, household |
| 6 | External Validation | Internal | Cross-checks against employer records, IRS, wage DBs |
| 7 | Document Upload | Applicant → State | Receives document metadata (file bytes via pre-signed URL) |
| 8 | Notice + RFI | Bidirectional | Sends notices and receives responses |
| 9 | Eligibility + Enrollment | Internal | Determines eligibility and enrolls applicants |
| 10 | Benefit Distribution | State → Applicant | Schedules and issues benefit payments |
| 11 | Appeals | Bidirectional | Handles appeal filings; `overturned` re-triggers the appealed layer |

---

## Your Task

1. Open `app/models.py` and set `LAYER_ID` to your layer number (1–11)
2. Implement `async def invoke(request, db) -> LayerResponse` in `app/invoke.py`
3. Run the compliance tests: `APP_URL=http://localhost:8000 DPW_API_KEY=test pytest tests/test_compliance.py -v`
4. Deploy your app and register at https://portal-production-162a.up.railway.app

---

## The Contract (Read This Before Writing Code)

### Layer 1 — Awareness

**What it does**: Acts as a state-specific benefit program catalog. When Benne starts a new
session, it calls this layer to find out what programs exist in the applicant's state — so it
can present accurate, live information rather than relying on training data.

**How it fits in the platform**

```
Applicant → Benne
               │
               │  awareness(case_id, state_code="IA", program_filter=[])
               ▼
         Platform API
               │
               ├──► Iowa Outreach Platform   (registered for IA, MN, WI)
               │      returns: [SNAP, Medicaid, hawk-i, ...]
               │
               └──► Ohio Benefits Notifier   (registered for OH, IN, KY)
                      returns: [SNAP, Medicaid, CHIP, ...]
```

Each registered app owns a catalog of programs for the states it covers. The platform routes
to the right app based on `state_code`. Multiple apps serve different states — they never
overlap on the same state.

**Request fields**
| Field | Type | Required | Description |
|---|---|---|---|
| case_id | string | ✓ | Threading key — echo in every response |
| state_code | string | ✓ | Two-letter state code, e.g. "IA" |
| layer_id | integer | ✓ | Always `1` for this layer |
| program_filter | string[] | — | If present, return only these program codes; if empty, return all |
| context | object | — | Optional hints: `household_size`, `has_children`, `approximate_income`, `age_range` |

**Response fields**
| Field | Type | Required | Description |
|---|---|---|---|
| case_id | string | ✓ | Echo from request |
| status | enum | ✓ | `found` / `not_found` / `error` |
| message | string | ✓ | Human-readable summary (e.g. "Found 3 programs in Iowa") |
| programs | object[] | ✓ | List of benefit programs (empty array when `not_found` or `error`) |

**Program object fields**
| Field | Type | Required | Description |
|---|---|---|---|
| code | string | ✓ | Program code, e.g. `"SNAP"` — used in downstream layers |
| name | string | ✓ | Full program name, e.g. `"Supplemental Nutrition Assistance Program"` |
| description | string | ✓ | Plain-language description — Benne reads this to applicants |
| eligibility_hint | string | — | Brief eligibility summary (informational only — Layer 9 does the real check) |
| how_to_apply | string | — | Instructions or URL |
| program_url | string | — | Official state program page URL |

**Valid statuses**
- `found` — one or more programs returned
- `not_found` — no programs match (return empty `programs` array)
- `error` — internal error; return this instead of HTTP 500

**Example request**
```json
{
  "case_id": "CASE-2026-IA-00041872",
  "state_code": "IA",
  "layer_id": 1,
  "program_filter": [],
  "context": {
    "household_size": 3,
    "has_children": true
  }
}
```

**Example response**
```json
{
  "case_id": "CASE-2026-IA-00041872",
  "status": "found",
  "message": "Found 3 benefit programs available in Iowa.",
  "programs": [
    {
      "code": "SNAP",
      "name": "Supplemental Nutrition Assistance Program",
      "description": "Helps low-income households pay for groceries through an EBT card.",
      "eligibility_hint": "Generally available to households earning below 130% of the federal poverty level.",
      "how_to_apply": "Apply online at dhs.iowa.gov or call 1-877-347-5678.",
      "program_url": "https://dhs.iowa.gov/food-assistance"
    },
    {
      "code": "MEDICAID",
      "name": "Iowa Health & Wellness Plan",
      "description": "Free or low-cost health coverage for adults and families.",
      "eligibility_hint": "Available to adults aged 19-64 earning up to 133% of the federal poverty level.",
      "how_to_apply": "Apply at dhs.iowa.gov or through Healthcare.gov.",
      "program_url": "https://dhs.iowa.gov/ime/members/medicaid-a-to-z/hh"
    }
  ]
}
```

---

### Layer 2 — Application

**What it does**: Receives and persists a benefit application submitted by or on behalf of an applicant.

**Request fields**
| Field | Type | Required | Description |
|---|---|---|---|
| case_id | string | ✓ | Threading key |
| state_code | string | ✓ | Two-letter state code |
| layer_id | integer | ✓ | Always `2` |
| applicant_identifier | string | ✓ | Opaque platform token |
| program_codes | string[] | ✓ | Programs being applied for |
| application_data | object | ✓ | State-specific form fields (flexible dict) |

**Response fields**
| Field | Type | Required | Description |
|---|---|---|---|
| case_id | string | ✓ | Echo from request |
| status | enum | ✓ | `submitted` / `draft` / `error` |
| message | string | ✓ | Human-readable outcome |
| application_id | string | — | Your internal application ID |
| confirmation_number | string | — | Human-readable confirmation for the applicant |

**Valid statuses**: `submitted`, `draft`, `error`

**Example request**
```json
{
  "case_id": "CASE-2026-PA-00041872",
  "state_code": "PA",
  "layer_id": 2,
  "applicant_identifier": "APPL-88f3a2c1-4d9b-4e10-a1a0-2f4b5c6d7e8f",
  "program_codes": ["SNAP"],
  "application_data": {"household_size": 3, "monthly_income": 2400}
}
```

**Example response**
```json
{
  "case_id": "CASE-2026-PA-00041872",
  "status": "submitted",
  "message": "Application received for SNAP. Confirmation #PA-2026-88291.",
  "application_id": "APP-88291",
  "confirmation_number": "PA-2026-88291"
}
```

---

### Layer 3 — Case Initiation

**What it does**: Opens a case in the state system, optionally assigns it to a worker.

**Request fields**
| Field | Type | Required | Description |
|---|---|---|---|
| case_id | string | ✓ | Threading key |
| state_code | string | ✓ | Two-letter state code |
| layer_id | integer | ✓ | Always `3` |
| application_id | string | ✓ | The application being initiated |
| worker_id | string | — | Preferred caseworker (platform may not provide one) |

**Response fields**
| Field | Type | Required | Description |
|---|---|---|---|
| case_id | string | ✓ | Echo from request |
| status | enum | ✓ | `initiated` / `duplicate` / `error` |
| message | string | ✓ | Human-readable outcome |
| assigned_worker_id | string | — | Worker assigned to this case |

**Valid statuses**: `initiated`, `duplicate`, `error`

**Example request**
```json
{
  "case_id": "CASE-2026-PA-00041872",
  "state_code": "PA",
  "layer_id": 3,
  "application_id": "APP-88291"
}
```

**Example response**
```json
{
  "case_id": "CASE-2026-PA-00041872",
  "status": "initiated",
  "message": "Case opened and assigned to worker W-2041.",
  "assigned_worker_id": "W-2041"
}
```

---

### Layer 4 — Exception Handling

**What it does**: Routes and resolves benefit irregularities that fall outside normal processing.

**Request fields**
| Field | Type | Required | Description |
|---|---|---|---|
| case_id | string | ✓ | Threading key |
| state_code | string | ✓ | Two-letter state code |
| layer_id | integer | ✓ | Always `4` |
| exception_type | string | ✓ | Type of irregularity (e.g. "duplicate_application", "fraud_flag") |
| exception_data | object | ✓ | Details about the irregularity |
| source_layer_id | integer | ✓ | Which layer triggered this exception |

**Response fields**
| Field | Type | Required | Description |
|---|---|---|---|
| case_id | string | ✓ | Echo from request |
| status | enum | ✓ | `resolved` / `escalated` / `pending` |
| message | string | ✓ | Human-readable outcome |
| resolution_notes | string | — | Details on how it was resolved or why escalated |

**Valid statuses**: `resolved`, `escalated`, `pending`

**Example request**
```json
{
  "case_id": "CASE-2026-PA-00041872",
  "state_code": "PA",
  "layer_id": 4,
  "exception_type": "duplicate_application",
  "exception_data": {"duplicate_case_id": "CASE-2026-PA-00039100"},
  "source_layer_id": 3
}
```

**Example response**
```json
{
  "case_id": "CASE-2026-PA-00041872",
  "status": "resolved",
  "message": "Duplicate detected and merged with existing case.",
  "resolution_notes": "Merged into CASE-2026-PA-00039100. Original case closed."
}
```

---

### Layer 5 — Verification

**What it does**: Verifies applicant identity, income, residency, and/or household composition
using your data sources. This is the most complex layer — it involves consent tokens and may
call external APIs (e.g., state wage records, IRS, Equifax).

**Request fields**
| Field | Type | Required | Description |
|---|---|---|---|
| case_id | string | ✓ | Threading key |
| state_code | string | ✓ | Two-letter state code |
| layer_id | integer | ✓ | Always `5` |
| applicant_identifier | string | ✓ | Opaque platform token |
| verification_types | enum[] | ✓ | One or more of: `identity`, `income`, `residency`, `household` |
| consent_token | string | ✓ | Applicant consent for data access — pass to external APIs |

**Response fields**
| Field | Type | Required | Description |
|---|---|---|---|
| case_id | string | ✓ | Echo from request |
| status | enum | ✓ | `verified` / `partial` / `failed` / `pending` |
| message | string | ✓ | Human-readable outcome |
| verification_results | object | — | Per-type results keyed by verification type |

**Valid statuses**
- `verified` — all requested types verified successfully
- `partial` — some types verified, others failed or unavailable
- `failed` — verification failed for all requested types
- `pending` — verification initiated but awaiting async response (e.g. IRS query)

**Example request**
```json
{
  "case_id": "CASE-2026-PA-00041872",
  "state_code": "PA",
  "layer_id": 5,
  "applicant_identifier": "APPL-88f3a2c1-4d9b-4e10-a1a0-2f4b5c6d7e8f",
  "verification_types": ["income", "residency"],
  "consent_token": "CONSENT-a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Example response**
```json
{
  "case_id": "CASE-2026-PA-00041872",
  "status": "partial",
  "message": "Income verified via wage records. Residency pending utility bill review.",
  "verification_results": {
    "income": {"verified": true, "source": "state_wage_db", "verified_amount": 2400},
    "residency": {"verified": false, "reason": "address mismatch — RFI required"}
  }
}
```

---

### Layer 6 — External Validation

**What it does**: Cross-references case data against external government data sources
(employer records, IRS, state wage databases) to validate reported information.

**Request fields**
| Field | Type | Required | Description |
|---|---|---|---|
| case_id | string | ✓ | Threading key |
| state_code | string | ✓ | Two-letter state code |
| layer_id | integer | ✓ | Always `6` |
| data_sources | string[] | ✓ | e.g. `["employer_records", "irs_data", "state_wage_db"]` |
| validation_queries | object | ✓ | Source-specific query parameters |

**Response fields**
| Field | Type | Required | Description |
|---|---|---|---|
| case_id | string | ✓ | Echo from request |
| status | enum | ✓ | `validated` / `discrepancy` / `unavailable` |
| message | string | ✓ | Human-readable outcome |
| validation_results | object | — | Per-source results |

**Valid statuses**: `validated`, `discrepancy`, `unavailable`

**Example response**
```json
{
  "case_id": "CASE-2026-PA-00041872",
  "status": "discrepancy",
  "message": "Reported income $2,400/mo; employer records show $3,100/mo.",
  "validation_results": {
    "employer_records": {"match": false, "reported": 2400, "found": 3100}
  }
}
```

---

### Layer 7 — Document Upload

**What it does**: Receives document metadata from the platform. The file bytes arrive via
pre-signed URL — your service downloads or processes them from that URL, not from the platform.

**Request fields**
| Field | Type | Required | Description |
|---|---|---|---|
| case_id | string | ✓ | Threading key |
| state_code | string | ✓ | Two-letter state code |
| layer_id | integer | ✓ | Always `7` |
| document_type | string | ✓ | e.g. `pay_stub`, `bank_statement`, `lease` |
| document_metadata | object | ✓ | Filename, size, mime_type, etc. |
| upload_url | string | ✓ | Pre-signed URL — fetch the file from here |

**Response fields**
| Field | Type | Required | Description |
|---|---|---|---|
| case_id | string | ✓ | Echo from request |
| status | enum | ✓ | `received` / `rejected` / `pending_review` |
| message | string | ✓ | Human-readable outcome |
| document_id | string | — | Your internal document ID |

**Valid statuses**: `received`, `rejected`, `pending_review`

---

### Layer 8 — Notice + RFI

**What it does**: Sends notices to applicants (outbound) and receives responses (inbound). Both
directions use the same endpoint — the `direction` field distinguishes them.

**Request fields**
| Field | Type | Required | Description |
|---|---|---|---|
| case_id | string | ✓ | Threading key |
| state_code | string | ✓ | Two-letter state code |
| layer_id | integer | ✓ | Always `8` |
| direction | enum | ✓ | `outbound` (platform → applicant) or `inbound` (applicant → platform) |
| notice_type | string | ✓ | e.g. `rfi_income`, `denial_notice`, `approval_notice` |
| content | object | ✓ | Notice body and metadata |
| response_deadline | string | — | ISO8601 datetime (for outbound RFIs) |
| applicant_reference | string | — | Links inbound response to original outbound `notice_id` |

**Response fields**
| Field | Type | Required | Description |
|---|---|---|---|
| case_id | string | ✓ | Echo from request |
| status | enum | ✓ | `sent` / `received` / `acknowledged` |
| message | string | ✓ | Human-readable outcome |
| notice_id | string | — | Your internal notice ID |

**Valid statuses**: `sent`, `received`, `acknowledged`

---

### Layer 9 — Eligibility + Enrollment

**What it does**: Determines benefit eligibility based on household and income data, then
enrolls eligible applicants. The response must list which programs are eligible and why
others are not (used for adverse action notices).

**Request fields**
| Field | Type | Required | Description |
|---|---|---|---|
| case_id | string | ✓ | Threading key |
| state_code | string | ✓ | Two-letter state code |
| layer_id | integer | ✓ | Always `9` |
| program_codes | string[] | ✓ | Programs to determine eligibility for |
| determination_data | object | ✓ | Household, income, and residency data |

**Response fields**
| Field | Type | Required | Description |
|---|---|---|---|
| case_id | string | ✓ | Echo from request |
| status | enum | ✓ | `eligible` / `ineligible` / `pending` / `partial` |
| message | string | ✓ | Human-readable outcome |
| eligible_programs | string[] | — | Programs approved (used by Layer 10) |
| ineligible_reasons | object | — | `{program_code: reason}` for adverse action notices |
| enrollment_details | object | — | Enrollment metadata per program (passed to Layer 10) |

**Valid statuses**: `eligible`, `ineligible`, `pending`, `partial`

---

### Layer 10 — Benefit Distribution

**What it does**: Schedules and issues benefit payments. One invocation per program.

**Request fields**
| Field | Type | Required | Description |
|---|---|---|---|
| case_id | string | ✓ | Threading key |
| state_code | string | ✓ | Two-letter state code |
| layer_id | integer | ✓ | Always `10` |
| program_code | string | ✓ | One program per invocation |
| distribution_method | enum | ✓ | `eft` / `ebt` / `check` / `voucher` |
| benefit_amount | float | — | Dollar amount (may be set by eligibility layer) |
| distribution_period | object | ✓ | `{start_date, end_date, frequency}` |

**Response fields**
| Field | Type | Required | Description |
|---|---|---|---|
| case_id | string | ✓ | Echo from request |
| status | enum | ✓ | `scheduled` / `issued` / `failed` |
| message | string | ✓ | Human-readable outcome |
| distribution_id | string | — | Your internal distribution/payment ID |

**Valid statuses**: `scheduled`, `issued`, `failed`

---

### Layer 11 — Appeals

**What it does**: Handles appeal filings, reviews, and decisions. **Critical**: if `status` is
`overturned`, the platform automatically re-invokes the `appealed_layer_id` layer. You must echo
`appealed_layer_id` in the response when overturning.

**Request fields**
| Field | Type | Required | Description |
|---|---|---|---|
| case_id | string | ✓ | Threading key |
| state_code | string | ✓ | Two-letter state code |
| layer_id | integer | ✓ | Always `11` |
| appeal_type | enum | ✓ | `denial` / `reduction` / `termination` |
| appealed_layer_id | integer | ✓ | Which layer's decision is being appealed |
| appeal_grounds | string | ✓ | Narrative explanation |
| supporting_data | object | ✓ | Evidence and documentation references |

**Response fields**
| Field | Type | Required | Description |
|---|---|---|---|
| case_id | string | ✓ | Echo from request |
| status | enum | ✓ | `filed` / `under_review` / `upheld` / `overturned` / `withdrawn` |
| message | string | ✓ | Human-readable outcome |
| appeal_id | string | — | Your internal appeal ID |
| hearing_date | string | — | ISO8601 datetime when hearing is scheduled |
| appealed_layer_id | integer | — | **Required when status=`overturned`** — triggers re-invocation |

**Valid statuses**: `filed`, `under_review`, `upheld`, `overturned`, `withdrawn`

---

## What's Already Built (Don't Touch)

| File | What it does |
|---|---|
| `app/main.py` | FastAPI app, `POST /invoke`, `GET /health`, auth middleware |
| `app/models.py` | Pydantic request/response models for all 11 layers |
| `app/config.py` | Settings from env vars (`DPW_API_KEY`, `PORT`, `LOG_LEVEL`) |
| `tests/test_compliance.py` | 10 compliance tests — run these before registering |

**Your only job**: implement `app/invoke.py`.

The platform calls `POST /invoke` with a JSON body matching your layer's request schema.
Your app must respond with HTTP 200 and a body matching the response schema.

---

## Implementation Guide

### Step 1 — Set your layer

In `app/models.py`, change:
```python
LAYER_ID = 1  # Change this to your layer number (1-11)
```

### Step 2 — Implement invoke()

Open `app/invoke.py`. The signature is:

```python
async def invoke(request: LayerRequest) -> LayerResponse:
```

The `request` object is already validated against your layer's schema before this function
is called. You don't need to re-validate it.

**Template for a catalog lookup (Layer 1 — Awareness):**
```python
async def invoke(request: LayerRequest) -> LayerResponse:
    try:
        programs = fetch_programs_for_state(
            state=request.state_code,
            program_filter=request.program_filter,
            context=request.context,
        )
        if not programs:
            return LayerResponse(
                case_id=request.case_id,
                status="not_found",
                message=f"No programs found for {request.state_code}.",
                programs=[],
            )
        return LayerResponse(
            case_id=request.case_id,
            status="found",
            message=f"Found {len(programs)} programs in {request.state_code}.",
            programs=programs,
        )
    except Exception as e:
        return LayerResponse(
            case_id=request.case_id,
            status="error",
            message=f"Catalog lookup failed: {e}",
            programs=[],
        )
```

**Template for a synchronous integration (most layers):**
```python
async def invoke(request: LayerRequest) -> LayerResponse:
    try:
        result = call_your_data_source(state=request.state_code)
        return LayerResponse(
            case_id=request.case_id,
            status="submitted",  # use your layer's valid status
            message=f"Processed successfully for case {request.case_id}.",
        )
    except YourExternalAPIError as e:
        return LayerResponse(
            case_id=request.case_id,
            status="error",
            message=f"External API error: {e}",
        )
```

### Step 3 — Run compliance tests

```bash
# Terminal 1: start your app
DPW_API_KEY=test uvicorn app.main:app --reload

# Terminal 2: run tests
APP_URL=http://localhost:8000 DPW_API_KEY=test pytest tests/test_compliance.py -v
```

All 10 tests must pass before you register.

---

## Common Mistakes

1. **Returning HTTP 500 for business errors** — Don't. Return HTTP 200 with `status="failed"`
   or `status="error"`. The platform treats 5xx as routing failures and surfaces them as 502.

2. **Not echoing case_id** — Every response must include `case_id` copied verbatim from the
   request. The platform uses it to thread the case.

3. **Ignoring consent_token (Layer 5)** — The consent token must be passed to external data
   APIs. Calling data sources without it violates the applicant's consent grant.

4. **Hardcoding state_code** — Your app may be registered for multiple states. Use
   `request.state_code` to dispatch to state-specific logic, not a hardcoded "PA".

5. **Raising NotImplementedError** — This causes a 500 response. The compliance test
   `test_valid_request_returns_200` will fail.

6. **Not echoing appealed_layer_id on overturned (Layer 11)** — The platform reads this field
   to know which layer to re-invoke. If it's missing, the denial loop breaks.

---

## Compliance Tests

Run these before registering your app. They test against a live running server.

```bash
APP_URL=http://localhost:8000 DPW_API_KEY=test pytest tests/test_compliance.py -v
```

| Test | What it checks |
|---|---|
| `test_health_returns_ok` | GET /health → 200 |
| `test_auth_rejects_missing_key` | POST /invoke with no key → 401 |
| `test_auth_rejects_wrong_key` | POST /invoke with wrong key → 401 |
| `test_valid_request_returns_200` | Well-formed request → 200 (your invoke() must not raise) |
| `test_response_echoes_case_id` | response.case_id == request.case_id |
| `test_response_status_is_valid` | status is in the layer's valid values |
| `test_response_has_message` | message is a non-empty string |
| `test_missing_required_field_returns_422` | Missing case_id → 422 |
| `test_wrong_layer_id_returns_422` | layer_id=99 → 422 |
| `test_repeated_call_same_case_id` | Idempotency — no 500 on repeated call |

**Expected before you implement invoke():** tests 1–3 and 7–9 pass; tests 4–6 and 10 fail
(that's correct — invoke() raises NotImplementedError).

**Expected after you implement invoke():** all 10 pass.

---

## Registration

Once all compliance tests pass:

1. Deploy your app (Railway, Fly.io, any public HTTPS URL)
2. Go to https://portal-production-162a.up.railway.app
3. Create an account → your DPW API key is shown once — save it
4. "Register App" → fill in: layer number, state(s), your `/invoke` endpoint URL, your app's API key
5. Status will be **PENDING** — DPW reviews activation (usually < 24h)
6. Once **ACTIVE** — your app receives live traffic from the platform

---

## Platform Guarantees (Things You Don't Need to Build)

The DPW platform handles these so your app doesn't have to:

- **Auth of inbound calls** — the platform calls your `/invoke` with an `X-Api-Key` header.
  You validate it against `DPW_API_KEY`. That's the only auth you need.
- **Case threading** — case_id is assigned by the platform. You just echo it.
- **CaseEvent logging** — the platform logs every invocation to an audit trail.
- **Retry logic** — the platform retries on 5xx with exponential backoff.
- **Rate limiting** — the platform rate-limits callers before they reach your app.
- **Appeals loop** — on `overturned`, the platform re-invokes the appealed layer.
  You just set the status and echo `appealed_layer_id`.
- **PII encryption** — applicant PII is encrypted by the platform. You receive opaque tokens.

---

## Environment Variables

| Variable | Description |
|---|---|
| `DPW_API_KEY` | The key the platform uses to call your app. Set to any value for local dev. |
| `PORT` | HTTP port (default: 8000) |
| `LOG_LEVEL` | Logging level (default: INFO) |

Copy `.env.example` to `.env` and set `DPW_API_KEY` before running locally.
