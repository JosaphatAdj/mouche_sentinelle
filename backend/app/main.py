import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.endpoints import detection, advisory, traps, tts

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

@app.get("/")
def root():
    return {
        "project": "Mouche Sentinel",
        "status": "online",
        "edition": "IndabaX Bénin 2026",
        "docs_url": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
