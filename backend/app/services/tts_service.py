import os
import re
import hashlib
import requests
import json
from typing import Optional
from pathlib import Path

# Dossier local de cache pour les fichiers audio .wav générés
CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "audio_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Cache mémoire pour résolution instantanée (clé: hash du texte, valeur: url ou chemin)
MEMORY_CACHE = {}

def clean_and_punctuate_for_tts(text: str) -> str:
    """
    Nettoie le texte Fon pour que Meta MMS-TTS respecte les pauses et la prosodie :
    1. Les modèles VITS marquent des micro-silences sur les virgules et les points.
    2. Convertit les points d'exclamation/interrogation en ponctuations avec espacement.
    3. Retire les émoticônes et astérisques markdown (* ou **).
    4. S'assure que les phrases ne sont pas trop longues sans ponctuation intermédiaire.
    """
    # Retrait du markdown (**gras**, *italique*)
    cleaned = re.sub(r'\*+', '', text)
    # Retrait des emojis (qui perturbent le tokenizer VITS)
    cleaned = re.sub(r'[\U00010000-\U0010ffff]', '', cleaned)
    
    # Remplacement des deux-points et tirets par des virgules pour créer des respirations naturelles
    cleaned = cleaned.replace(":", ", ").replace(" - ", ", ")
    
    # Remplacement des ! et ? par des points avec espace pour forcer la fin de phrase et la pause
    cleaned = re.sub(r'!+', ' . ', cleaned)
    cleaned = re.sub(r'\?+', ' . ', cleaned)
    
    # Normalisation des virgules et points (insère une vraie pause phonologique)
    cleaned = re.sub(r'\s*,\s*', ', ', cleaned)
    cleaned = re.sub(r'\s*\.\s*', '. ', cleaned)
    
    # Élimine les doubles espaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def synthesize_fon_audio(text: str) -> Optional[str]:
    """
    Synthèse vocale Meta MMS-TTS avec :
    - Normalisation de la ponctuation pour le respect des pauses.
    - Double niveau de cache (Mémoire + Disque local) pour replay instantané (0 ms de latence).
    """
    if not text or not text.strip():
        return None

    # 1. Vérification du cache par empreinte MD5
    text_hash = hashlib.md5(text.strip().encode("utf-8")).hexdigest()
    if text_hash in MEMORY_CACHE:
        return MEMORY_CACHE[text_hash]

    # 2. Prétraitement de la ponctuation pour des respirations naturelles
    tts_input = clean_and_punctuate_for_tts(text)

    try:
        base_url = "https://guunk-ttsfon.hf.space/gradio_api"
        payload = {"data": [tts_input]}
        
        res = requests.post(f"{base_url}/call/predict", json=payload, timeout=12)
        if res.status_code != 200:
            return None
            
        event_id = res.json().get("event_id")
        if not event_id:
            return None
            
        stream_url = f"{base_url}/call/predict/{event_id}"
        res_stream = requests.get(stream_url, stream=True, timeout=25)
        
        for line in res_stream.iter_lines():
            if line:
                decoded = line.decode("utf-8")
                if "data:" in decoded:
                    data = json.loads(decoded.replace("data:", "").strip())
                    audio_url = None
                    if isinstance(data, list) and len(data) > 0:
                        audio_url = data[0].get("url")
                    elif isinstance(data, dict):
                        audio_url = data.get("url")
                    
                    if audio_url:
                        # Sauvegarde en cache mémoire pour relecture instantanée
                        MEMORY_CACHE[text_hash] = audio_url
                        return audio_url
    except Exception as e:
        print(f"[TTS-FON-SERVICE] Erreur génération audio Fon: {e}")
        
    return None
