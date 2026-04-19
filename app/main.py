import logging
from fastapi import FastAPI, HTTPException, Header
from .models import LayerRequest, LayerResponse, LAYER_ID
from .invoke import invoke
from .config import settings

logging.basicConfig(level=settings.LOG_LEVEL)
log = logging.getLogger(__name__)

app = FastAPI(title=f"DPW Layer {LAYER_ID} App")


@app.post("/invoke", response_model=LayerResponse)
async def invoke_endpoint(
    request: LayerRequest,
    x_api_key: str = Header(...),
):
    if x_api_key != settings.DPW_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    log.info("invoke layer=%d case=%s state=%s", LAYER_ID, request.case_id, request.state_code)
    return await invoke(request)


@app.get("/health")
async def health():
    return {"status": "ok"}
