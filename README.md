# DPW Layer App Template

Template for building a compliant [DPW Open Platform](https://github.com/alexf4/dpw-open-platform) layer app.

## Quick Start

1. Click **Use this template** → create your repo
2. Open `CLAUDE.md` — it has everything you need
3. Set `LAYER_ID` in `app/models.py`
4. Implement `invoke()` in `app/invoke.py`
5. Run compliance tests → deploy → register

## The Short Version

```bash
cp .env.example .env          # set DPW_API_KEY to any test value
uvicorn app.main:app --reload  # start the app

# run compliance tests (in a second terminal)
APP_URL=http://localhost:8000 DPW_API_KEY=test pytest tests/test_compliance.py -v
```

All 10 tests pass → register at https://portal-production-162a.up.railway.app

## What You Build

One function in `app/invoke.py`:

```python
async def invoke(request: LayerRequest) -> LayerResponse:
    # your business logic here
```

Everything else is pre-built: FastAPI routing, auth validation, error handling, health endpoint.

## Docs

- `CLAUDE.md` — full platform context + all 11 layer contracts inline (start here)
- `docs/local_dev.md` — local setup and test commands
- `docs/registration_guide.md` — how to deploy and register

## The 11 Layers

| # | Layer | Direction |
|---|---|---|
| 1 | Awareness | State → Applicant |
| 2 | Application | Applicant → State |
| 3 | Case Initiation | Internal |
| 4 | Exception Handling | Internal |
| 5 | Verification | Applicant → State |
| 6 | External Validation | Internal |
| 7 | Document Upload | Applicant → State |
| 8 | Notice + RFI | Bidirectional |
| 9 | Eligibility + Enrollment | Internal |
| 10 | Benefit Distribution | State → Applicant |
| 11 | Appeals | Bidirectional |
