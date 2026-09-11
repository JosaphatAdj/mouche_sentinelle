from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from backend.app.services.tts_service import synthesize_fon_audio

router = APIRouter(prefix="/tts", tags=["TTS"])

class TTSRequest(BaseModel):
    text: str

class TTSResponse(BaseModel):
    audio_url: Optional[str] = None
    status: str

@router.post("/generate", response_model=TTSResponse)
async def generate_fon_audio_endpoint(req: TTSRequest):
    """Prend n'importe quel texte généré en Fon et retourne l'URL de l'audio natif Fon généré par Meta MMS-TTS."""
    url = synthesize_fon_audio(req.text)
    if url:
        return TTSResponse(audio_url=url, status="success")
    return TTSResponse(audio_url=None, status="error")
