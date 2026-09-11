from typing import List, Optional
from pydantic import BaseModel

class Trap(BaseModel):
    id: str
    name: str
    commune: str
    department: str
    latitude: float
    longitude: float
    crop: str
    last_count: int
    alert_level: str
    last_updated: str

# Données de démonstration géoréférencées dans les bassins fruitiers du Bénin
BENIN_SAMPLE_TRAPS: List[Trap] = [
    Trap(
        id="TRAP-BJ-001",
        name="Verger Borgou Nord #1",
        commune="Parakou",
        department="Borgou",
        latitude=9.3372,
        longitude=2.6303,
        crop="mangue",
        last_count=18,
        alert_level="critical",
        last_updated="2026-09-11 08:30"
    ),
    Trap(
        id="TRAP-BJ-002",
        name="Verger Atacora Ouest",
        commune="Natitingou",
        department="Atacora",
        latitude=10.3042,
        longitude=1.3796,
        crop="mangue",
        last_count=12,
        alert_level="critical",
        last_updated="2026-09-11 09:15"
    ),
    Trap(
        id="TRAP-BJ-003",
        name="Plantation Zou Sud",
        commune="Bohicon",
        department="Zou",
        latitude=7.1783,
        longitude=2.0667,
        crop="agrumes",
        last_count=4,
        alert_level="medium",
        last_updated="2026-09-10 16:45"
    ),
    Trap(
        id="TRAP-BJ-004",
        name="Bassin Allada Centre",
        commune="Allada",
        department="Atlantique",
        latitude=6.6653,
        longitude=2.1514,
        crop="ananas",
        last_count=2,
        alert_level="low",
        last_updated="2026-09-11 07:00"
    ),
    Trap(
        id="TRAP-BJ-005",
        name="Verger Ouémé Vallée",
        commune="Adjohoun",
        department="Ouémé",
        latitude=6.7028,
        longitude=2.4833,
        crop="mangue",
        last_count=9,
        alert_level="critical",
        last_updated="2026-09-11 11:20"
    ),
]
