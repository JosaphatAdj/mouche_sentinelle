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

                # Désactiver le thinking budget pour forcer une réponse directe sans tokens de réflexion
                config_kwargs = {
                    "temperature": 0.2,
                    "max_output_tokens": 1500,
                    "response_mime_type": "application/json"
                }

                # Si supporté par la version du SDK, couper le budget de pensée
                try:
                    config = types.GenerateContentConfig(
                        temperature=0.2,
                        max_output_tokens=1500,
                        response_mime_type="application/json",
                        thinking_config=types.ThinkingConfig(thinking_budget=0)
                    )
                except Exception:
                    config = types.GenerateContentConfig(
                        temperature=0.2,
                        max_output_tokens=1500,
                        response_mime_type="application/json"
                    )

                res = await loop.run_in_executor(
                    None,
                    lambda: self.client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=prompt,
                        config=config
                    )
                )

                # Extraire le texte en ignorant les parts non textuelles
                raw_text = ""
                try:
                    if hasattr(res, "candidates") and res.candidates:
                        for part in res.candidates[0].content.parts:
                            if hasattr(part, "text") and part.text:
                                raw_text += part.text
                except Exception:
                    pass

                # Fallback sur res.text si nécessaire
                if not raw_text and hasattr(res, "text") and res.text:
                    raw_text = res.text

                raw_text = raw_text.strip()
                print(f"[FonAgentService] Réponse brute ({len(raw_text)} chars): {raw_text[:200]}")

                parsed = self._extract_json(raw_text)

                if not parsed:
                    print("[FonAgentService] JSON non parseable, bascule fallback contextuel.")
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
        trap_count = req.trap_count if req.trap_count is not None else 0
        is_photo_alert = (trap_count > 0) or (req.alert_level in ["medium", "critical"])

        if req.language == "fon":
            if is_photo_alert:
                if trap_count >= 5 or req.alert_level == "critical":
                    advice = (
                        f"Xɛsi kpo gbigbɔ kpo ɖo {crop_name} towe jí ! Mouche {trap_count} wɛ ɖo hɔntɔn mɛ. "
                        "Bɛ́ atínsínsɛ́n e jɛ ayǐ lɛ́ bǐ bló ɖokpó azɔn we ɖo sɛmɛn ! "
                        "Sɔ́ dó saki wiwi glógló mɛ bo tɛ́ dó hwesivɔ mɛ azǎn we nú larves lɛ́ na kú."
                    )
                    actions = [
                        "Bɛ́ amangà e jɛ ayǐ lɛ́ bǐ azɔn we ɖo sɛmɛn (Ramasser les fruits tombés 2x/semaine)",
                        "Solarisation : Sɔ́ dó saki wiwi mɛ dó hwesivɔ mɛ azǎn we",
                        "Zǎn basilic (késukésu) nú pièges artisanal lɛ́"
                    ]
                else:
                    advice = (
                        f"Mouche kpɛɖé wɛ ɖo hɔntɔn mɛ ({trap_count} mɔ). "
                        f"Nǔ lɛ́ kpo ɖo jlɛ̌jí nú {crop_name} towe, amɔ̌ kpɔ́n atínsínsɛ́n lɛ́ ganji bo bɛ́ nǔ e jɛ ayǐ lɛ́."
                    )
                    actions = [
                        "Kpɔ́n pièges lɛ́ gbè bǐ gbè",
                        "Bɛ́ atínsínsɛ́n e jɛ ayǐ lɛ́"
                    ]
                phonetic = "Xesi kpon kpon ganji. Be amanga le bi."
            else:
                advice = (
                    f"Nú {crop_name} towe, xɛsi ɖěbǔ ɖò finɛ nú mouche ǎ kakɔ̀. "
                    "Nú a jló na glɔ́n ali nú mouche des fruits ɔ, nɔ bɛ́ atínsínsɛ́n e jɛ ayǐ lɛ́ bo nɔ tɛ́n pièges lɛ́ ganji."
                )
                phonetic = "Kpon ganji. Be amanga le bi."
                actions = [
                    "Surveillance régulière des vergers",
                    "Entretien et nettoyage sous les arbres"
                ]
        else:
            if is_photo_alert:
                if trap_count >= 5 or req.alert_level == "critical":
                    advice = (
                        f"Alerte infestation élevée sur vos vergers de {req.crop}s ({trap_count} mouches détectées). "
                        "Appliquez d'urgence la lutte prophylactique : ramassage systématique des fruits tombés au sol au moins 2 fois par semaine, "
                        "puis solarisation immédiate en sacs plastiques noirs hermétiques exposés 48h au soleil pour neutraliser les larves."
                    )
                    actions = [
                        "Ramassage systématique 2 fois par semaine des fruits au sol",
                        "Solarisation 48h en sacs plastiques hermétiques noirs au plein soleil",
                        "Dépose des fruits en augmentorium pour sauver les parasitoïdes utiles",
                        "Installation de pièges d'appoint au basilic local (Ocimum basilicum)"
                    ]
                else:
                    advice = (
                        f"Présence modérée détectée sur vos {req.crop}s ({trap_count} mouches). "
                        "La situation est sous contrôle mais nécessite une vigilance accrue : maintenez la parcelle propre et inspectez vos pièges deux fois par semaine."
                    )
                    actions = [
                        "Inspection rapprochée des pièges 2 fois par semaine",
                        "Ramassage préventif des premiers fruits tombés",
                        "Vérification des bordures de parcelle"
                    ]
            else:
                advice = (
                    f"Surveillance de routine pour vos vergers de {req.crop}s : aucun seuil critique n'est dépassé. "
                    "Pour éviter toute attaque de Bactrocera à l'approche de la récolte, maintenez un ramassage régulier des fruits au sol et assurez-vous que vos pièges sont bien rechargés en attractif."
                )
                actions = [
                    "Surveillance préventive hebdomadaire",
                    "Nettoyage régulier sous la canopée des arbres",
                    "Récolte au stade vert-mûr (physiologique)"
                ]
            phonetic = None

        return AdvisoryResponse(
            language=req.language,
            crop=req.crop,
            alert_level=req.alert_level or ("critical" if trap_count >= 5 else "low"),
            advice_text=advice,
            phonetic_fon=phonetic,
            action_items=actions,
            audio_available=True,
            engine_used="fallback_calibrated"
        )

fon_agent_service = FonAgentService()
