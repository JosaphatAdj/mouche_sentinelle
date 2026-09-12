import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Permettre l'import quel que soit le répertoire d'exécution (Render racine ou sous-dossier backend)
current_file = Path(__file__).resolve()
backend_dir = current_file.parent.parent
project_root = backend_dir.parent

for p in [str(project_root), str(backend_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from backend.app.api.endpoints import detection, advisory, traps, tts
except ModuleNotFoundError:
    from app.api.endpoints import detection, advisory, traps, tts

app = FastAPI(
    title="Mouche Sentinel API",
    description="API de surveillance intelligente de la mouche des fruits (Bactrocera) - IndabaX Bénin 2026",
    version="1.0.0"
)

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://mouche-sentinelle-indabax-50vbsq9ug.vercel.app",
]

# CORS avec regex pour couvrir toutes les URLs preview et production de Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routes
app.include_router(detection.router, prefix="/api")
app.include_router(advisory.router, prefix="/api")
app.include_router(traps.router, prefix="/api")
app.include_router(tts.router, prefix="/api")

@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {
        "project": "Mouche Sentinel",
        "status": "online",
        "edition": "IndabaX Bénin 2026",
        "docs_url": "/docs"
    }

@app.api_route("/health", methods=["GET", "HEAD"])
def health_check():
    return {"status": "healthy"}
