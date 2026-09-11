from fastapi import APIRouter
from backend.app.services.fon_agent import fon_agent_service, AdvisoryRequest, AdvisoryResponse

router = APIRouter(prefix="/advisory", tags=["Advisory"])

@router.post("/consult", response_model=AdvisoryResponse)
async def consult_advisor(request: AdvisoryRequest):
    """
    Consulte l'agent Google ADK à mémoire conversationnelle pour obtenir
    des recommandations agronomiques en langue Fon ou en Français.
    """
    return await fon_agent_service.get_advisory(request)
