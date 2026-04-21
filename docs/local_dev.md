# Local Development Guide

## Prerequisites

- Python 3.11+
- `pip` or a virtual environment manager of your choice

## Setup

```bash
# Clone your repo (from "Use this template")
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME

# Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure env
cp .env.example .env
# .env only needs DPW_API_KEY — set it to any string for local dev:
#   DPW_API_KEY=test
```

## Running the App

```bash
DPW_API_KEY=test uvicorn app.main:app --reload
```

- App: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Running with Docker

```bash
# Requires .env to exist with DPW_API_KEY set
docker compose up --build
```

## Running Tests

### Unit tests — no server needed

These test `invoke()` in isolation.

```bash
DPW_API_KEY=test pytest tests/test_invoke.py -v
```

Before you implement `invoke()`, all 4 will fail with `NotImplementedError` — that's expected.

Expected output after implementing `invoke()`:

```
tests/test_invoke.py::test_invoke_returns_layer_response PASSED
tests/test_invoke.py::test_invoke_echoes_case_id PASSED
tests/test_invoke.py::test_invoke_returns_valid_status PASSED
tests/test_invoke.py::test_invoke_returns_nonempty_message PASSED
```

### Compliance tests — requires a running server

These test the full HTTP stack against a live server.

```bash
# Terminal 1: start the server
DPW_API_KEY=test uvicorn app.main:app --reload

# Terminal 2: run compliance tests
APP_URL=http://localhost:8000 DPW_API_KEY=test pytest tests/test_compliance.py -v
```

Expected before implementing `invoke()`:
- PASS: health, auth rejection (×2), missing field, wrong layer ID (5 tests)
- FAIL: valid request, case_id echo, valid status, message, idempotency (5 tests)

Expected after implementing `invoke()`: all 10 pass.

## Trying It Manually

Basic invocation (replace field values for your layer):

```bash
curl -s -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -H "x-api-key: test" \
  -d '{
    "case_id": "CASE-2026-XX-00000001",
    "state_code": "PA",
    "layer_id": 1
  }' | python -m json.tool
```

Trigger the `not_found` / no-match path by passing a filter your app doesn't cover:

```bash
curl -s -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -H "x-api-key: test" \
  -d '{
    "case_id": "CASE-2026-XX-00000002",
    "state_code": "PA",
    "layer_id": 1,
    "program_filter": ["UNKNOWN_CODE"]
  }' | python -m json.tool
```

## Switching Layers

1. Open `app/models.py`
2. Change `LAYER_ID = 1` to your layer number (1–11)
3. Implement `invoke()` in `app/invoke.py` for the new layer's contract
4. Re-run compliance tests

## Development Workflow

1. Set `LAYER_ID` in `app/models.py`
2. Implement `invoke()` in `app/invoke.py`
3. Run unit tests: `pytest tests/test_invoke.py -v`
4. Start server, run compliance tests: `pytest tests/test_compliance.py -v`
5. All 10 compliance tests pass → deploy → register

## Debugging

The app logs every invocation:

```
INFO:app.main:invoke layer=1 case=CASE-2026-XX-00000001 state=PA
```

Set `LOG_LEVEL=DEBUG` in `.env` for more verbose output.

| Symptom | Fix |
|---|---|
| `422 Unprocessable Entity` on `/invoke` | Missing or malformed `x-api-key` header or request body field |
| `401 Unauthorized` | `x-api-key` header value doesn't match `DPW_API_KEY` in your env |
| `ValidationError` on startup | `DPW_API_KEY` not set — check your `.env` file |
| Tests fail with `Connection refused` | Server isn't running; start it with `uvicorn app.main:app --reload` |
