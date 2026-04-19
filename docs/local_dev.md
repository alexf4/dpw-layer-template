# Local Development Guide

## Setup

```bash
# Clone your repo (from "Use this template")
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME

# Copy env file
cp .env.example .env
# Edit .env — set DPW_API_KEY to any value for local dev

# Install dependencies
pip install -r requirements.txt
```

## Running the App

```bash
uvicorn app.main:app --reload
```

App runs at http://localhost:8000. Swagger UI at http://localhost:8000/docs.

## Running with Docker

```bash
docker compose up --build
```

## Running Tests

### Unit tests (no server needed)

```bash
pytest tests/test_invoke.py -v
```

These test `invoke()` directly. Before you implement it, all 4 will fail with
`NotImplementedError` — that's expected.

### Compliance tests (requires running server)

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

The app logs every invocation at INFO level:

```
INFO:app.main:invoke layer=1 case=CASE-TEST-001 state=PA
```

Raise `LOG_LEVEL=DEBUG` in `.env` for more verbose output.

If a compliance test fails unexpectedly, check:
- Is the server running? (`curl http://localhost:8000/health`)
- Is `DPW_API_KEY` set and matching in both `.env` and the test env var?
- Is `LAYER_ID` set correctly in `app/models.py`?
