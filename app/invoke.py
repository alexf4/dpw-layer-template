"""
Implement this function. It is called by the DPW platform for every case
that reaches your layer. Read the contract in CLAUDE.md before you start.

Args:
    request: Validated request from the DPW platform. Fields are documented
             in CLAUDE.md and in app/models.py.

Returns:
    LayerResponse with:
        - case_id: echo from request (required)
        - status: one of the valid values for your layer (see CLAUDE.md)
        - message: human-readable outcome for caseworkers
        - any layer-specific response fields your layer defines

Do not raise HTTP exceptions for business-logic outcomes — return
status="failed" or status="error" with a descriptive message instead.
"""

from .models import LayerRequest, LayerResponse


async def invoke(request: LayerRequest) -> LayerResponse:
    # TODO: implement your layer logic here
    raise NotImplementedError("implement invoke() in this file")
