import os
import sys
import json
import asyncio
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from pathlib import Path

# Chargement des variables d'environnement
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

AGRONOMIC_SYSTEM_CONTEXT = """
Tu es "Mouche Sentinel Advisor", un assistant agronomique expert déployé au Bénin pour lutter contre la mouche des fruits (Bactrocera dorsalis et Bactrocera zonata).
Tu dialogues directement avec les producteurs de fruits (mangues, agrumes, ananas) et les agents de vulgarisation agricole.

CONNAISSANCES AGRONOMIQUES FONDAMENTALES (BÉNIN & AFRIQUE DE L'OUEST) :
1. RAVAGEUR :
   - Bactrocera dorsalis (mouche orientale) et Bactrocera zonata attaquent les mangues (15-70% de perte au Bénin), les agrumes et l'ananas.
   - Les femelles perforent les fruits pour y pondre. Les larves provoquent la décomposition interne et la chute prématurée des fruits.

2. SEUILS DE PIÉGEAGE (Captures de mouches par piège/jour - FTD) :
   - FAIBLE (< 2) : Surveillance continue. Maintenir l'attractif propre.
   - MOYEN (2 à 5) : Risque émergent. Inspection renforcée au verger.
   - CRITIQUE (> 5) : Danger immédiat ! Déclencher la lutte intégrée d'urgence.

3. MESURES DE LUTTE SELON LA CULTURE :
   A. MANGUIER (Culture prioritaire n°1 au Bénin) :
      - Ramassage obligatoire au sol au moins 2 fois par semaine.
      - Traitement des fruits piqués : Les enfermer dans des sacs plastiques hermétiques noirs exposés 48h en plein soleil (solarisation thermique tue les larves), ou enfouissement à > 50 cm avec chaux vive.
      - Augmentorium : Déposer les fruits ramassés dans une cage/tente à maille fine : elle emprisonne les mouches adultes émergentes mais laisse s'échapper les micro-guêpes parasitoïdes utiles.
      - Alternative locale : Utiliser des extraits de basilic local (Ocimum basilicum) comme répulsif/attractif alternatif si le méthyl eugénol fait défaut.
      - Récolte précoce au stade vert-mûr (physiologique).

   B. AGRUMES :
      - Surveillance accrue dès le début de changement de couleur des fruits.
      - Assainissement strict au sol (ne jamais laisser les fruits pourrir au pied des arbres).

   C. ANANAS :
      - Nettoyage des bordures de parcelle et des résidus de récolte.

GESTION DU FLUX CONVERSATIONNEL & DES QUESTIONS LIBRES :
- Si l'utilisateur pose une question libre (ex: "je crains de grande perte ?", "comment faire ?", etc.), réponds précisément et directement à son inquiétude selon les connaissances agronomiques ci-dessus.
- S'il n'y a pas eu de piège infesté signalé (> 0 mouches), NE LUI PARLE PAS d'une fausse alerte de 0 mouche ! Reste factuel et rassurant ou donne les conseils préventifs.
- Si c'est une suite de discussion, NE RÉPÈTE PAS les salutations ("Kú àbɔ̀ !").
- Phrases bien découpées avec ponctuation claire pour la vocalisation.

FORMAT DE RÉPONSE OBLIGATOIRE (JSON STRICT) :
{
  "advice_text": "Le conseil complet et direct rédigé dans la langue demandée",
  "phonetic_fon": "Guide de prononciation ou résumé court (uniquement si Fon, sinon laisser vide)",
  "action_items": [
     "Consigne d'action 1 concrète et immédiate",
     "Consigne d'action 2",
     "Consigne d'action 3"
  ]
}
"""

class AdvisoryRequest(BaseModel):
    session_id: str = "default_session"
    language: str = "fon"  # "fon" ou "fr"
    crop: str = "mangue"   # "mangue", "agrumes", "ananas"
    trap_count: Optional[int] = 0
    alert_level: Optional[str] = "low"
    user_message: Optional[str] = None

class AdvisoryResponse(BaseModel):
    language: str
    crop: str
    alert_level: str
    advice_text: str
    phonetic_fon: Optional[str] = None
    action_items: list[str]
    audio_available: bool = True
    engine_used: str = "gemini_live"

class FonAgentService:
    def __init__(self):
        self.api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        self.client = None
        self.sessions: Dict[str, List[Dict[str, str]]] = {}
        self._init_client()

    def _init_client(self):
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                print("[FonAgentService] ✅ Google GenAI Client connecté (gemini-3.6-flash).")
            except Exception as e:
                print(f"[FonAgentService] Erreur init GenAI: {e}")
        else:
            print("[FonAgentService] Mode simulation active (Clé absente)")

    async def get_advisory(self, req: AdvisoryRequest) -> AdvisoryResponse:
        """Appel direct et fiable du modèle avec mémoire par session."""
        session_id = req.session_id or "default_session"
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        history = self.sessions[session_id]

        if not self.client and (os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")):
            self.api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
            self._init_client()

        if self.client:
            history_context = ""
            if history:
                history_context = "HISTORIQUE RÉCENT DE CETTE DISCUSSION :\n"
                for turn in history[-4:]:
                    history_context += f"- Utilisateur : {turn['user']}\n- Toi : {turn['agent']}\n"

            prompt = f"""
{AGRONOMIC_SYSTEM_CONTEXT}

{history_context}

CONTEXTE ACTUEL DU PRODUCTEUR :
- Langue demandée : {req.language}
- Culture ciblée : {req.crop}
- Nombre de mouches dans le piège : {req.trap_count if req.trap_count and req.trap_count > 0 else 'Aucun relevé signalé pour le moment'}
- Question / Message de l'utilisateur : {req.user_message}

Réponds uniquement en JSON valide (sans code markdown ```json).
"""
            try:
                from google.genai import types
                loop = asyncio.get_event_loop()

                res = await loop.run_in_executor(
                    None,
                    lambda: self.client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.3,
                            max_output_tokens=1200,  # Assez pour JSON complet
                            response_mime_type="application/json"
                        )
                    )
                )

                # Extraire le texte en ignorant les thought_signature (tokens de réflexion)
                raw_text = ""
                try:
                    candidate = res.candidates[0]
                    for part in candidate.content.parts:
                        if hasattr(part, "text") and part.text:
                            raw_text += part.text
                except Exception:
                    pass

                # Fallback sur res.text si les parts n'ont rien donné
                if not raw_text and hasattr(res, "text") and res.text:
                    raw_text = res.text

                raw_text = raw_text.strip()
                print(f"[FonAgentService] Réponse brute ({len(raw_text)} chars): {raw_text[:150]}")

                parsed = self._extract_json(raw_text)

                if not parsed:
                    print("[FonAgentService] JSON non parseable, bascule fallback.")
                    return self._generate_fallback(req)

                advice = parsed.get("advice_text", "").strip()
                phonetic = parsed.get("phonetic_fon", "").strip() or None
                actions = parsed.get("action_items", [])

                if not advice:
                    return self._generate_fallback(req)

                # Sauvegarde dans l'historique de session
                self.sessions[session_id].append({
                    "user": req.user_message or "",
                    "agent": advice
                })

                return AdvisoryResponse(
                    language=req.language,
                    crop=req.crop,
                    alert_level=req.alert_level or "low",
                    advice_text=advice,
                    phonetic_fon=phonetic if req.language == "fon" else None,
                    action_items=actions,
                    audio_available=True,
                    engine_used="gemini-3.6-flash-live"
                )
            except Exception as e:
                print(f"[FonAgentService] Erreur appel Gemini: {e}. Bascule sur fallback.")

        return self._generate_fallback(req)

    def _extract_json(self, text: str) -> Optional[Dict]:
        """Parse JSON robustement en retirant les éventuels backticks markdown de Gemini."""
        try:
            # Retirer les blocs ```json ... ``` ou ``` ... ```
            cleaned = text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                # Supprimer la première et dernière ligne (les ``` fences)
                inner = lines[1:] if lines[0].startswith("```") else lines
                inner = inner[:-1] if inner and inner[-1].strip() == "```" else inner
                cleaned = "\n".join(inner).strip()

            # Trouver le premier { et le dernier }
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(cleaned[start:end])
        except Exception as e:
            print(f"[FonAgentService] Erreur parsing JSON: {e}")
        return None

    def _generate_fallback(self, req: AdvisoryRequest) -> AdvisoryResponse:
        crop_names_fon = {"mangue": "Amangà", "agrumes": "Klémantíni kpo Klé kpo", "ananas": "Agonké"}
        crop_name = crop_names_fon.get(req.crop.lower(), "Atinsínsɛ́n")
        has_trap = req.trap_count and req.trap_count > 0

        if req.language == "fon":
            if has_trap:
                advice = (
                    f"Xɛsi ɖo gbeji nú {crop_name} towe ! "
                    f"Mouche sukpɔ́ ɖo hɔntɔn mɛ ({req.trap_count} mɔ). "
                    "Bɛ́ amangà e jɛ ayǐ lɛ́ bǐ bló ɖokpó ! Sɔ́ dó saki wiwi mɛ dó hwesivɔ mɛ azǎn we !"
                )
            else:
                advice = (
                    f"Nú amangà towe ma kɔn mouche sukpɔ́ à, xɛsi ɖěbǔ ɖò finɛ ǎ. "
                    "Kpɔ́n atínsínsɛ́n lɛ́ bó bɛ́ nǔ e jɛ ayǐ lɛ́ bló ɖokpó."
                )
            phonetic = "Xesi kpon kpon ganji. Be amanga le bi."
            actions = [
                "Bɛ́ amangà e jɛ ayǐ lɛ́ bǐ (Ramasser tous les fruits tombés)",
                "Sɔ́ dó saki wiwi mɛ (Solariser dans sacs plastiques noirs étanches)"
            ]
        else:
            if has_trap:
                advice = (
                    f"Alerte pour vos {req.crop}s ({req.trap_count} mouches détectées). "
                    "Ramassez immédiatement tous les fruits tombés et isolez-les en sacs hermétiques."
                )
            else:
                advice = (
                    f"Les pertes peuvent atteindre 15 à 70% si le verger de {req.crop}s n'est pas surveillé. "
                    "Effectuez un ramassage régulier 2 fois par semaine et surveillez vos pièges pour éviter toute prolifération."
                )
            phonetic = None
            actions = [
                "Ramassage systématique 2 fois par semaine des fruits au sol",
                "Solarisation 48h en sacs plastiques hermétiques noirs au soleil"
            ]

        return AdvisoryResponse(
            language=req.language,
            crop=req.crop,
            alert_level=req.alert_level or "low",
            advice_text=advice,
            phonetic_fon=phonetic,
            action_items=actions,
            audio_available=True,
            engine_used="fallback_calibrated"
        )

fon_agent_service = FonAgentService()
