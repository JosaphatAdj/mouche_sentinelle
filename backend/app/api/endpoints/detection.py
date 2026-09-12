from fastapi import APIRouter, File, UploadFile, Form
try:
    from backend.app.services.detector import detector_service, DetectionResult
except ModuleNotFoundError:
    from app.services.detector import detector_service, DetectionResult

router = APIRouter(prefix="/detection", tags=["Detection"])

@router.post("/scan", response_model=DetectionResult)
async def scan_trap_image(
    file: UploadFile = File(...),
    crop: str = Form("mangue")
):
    """
    Reçoit la photo du piège, compte les mouches Bactrocera (dorsalis/zonata)
    et évalue le niveau de gravité selon la culture.
    """
    image_bytes = await file.read()
    return detector_service.detect_image(image_bytes=image_bytes, crop=crop)
