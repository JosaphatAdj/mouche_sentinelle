from typing import List
from fastapi import APIRouter
from backend.app.services.trap_data import BENIN_SAMPLE_TRAPS, Trap

router = APIRouter(prefix="/traps", tags=["Traps"])

@router.get("/", response_model=List[Trap])
async def list_traps():
    """Retourne l'état géoréférencé des pièges et le niveau d'infestation au Bénin."""
    return BENIN_SAMPLE_TRAPS
