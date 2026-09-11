# 🥭 Mouche Sentinel — Surveillance Intelligente de la Mouche des Fruits (*Bactrocera*)

> **Projet Hackathon — Deep Learning IndabaX Bénin 2026**  
> *Défis croisés : Agriculture & Sécurité Alimentaire × IA & Langues Locales*

---

## 📌 Présentation du Projet

En Afrique de l'Ouest et particulièrement au Bénin, la mouche des fruits (**Bactrocera dorsalis** et **Bactrocera zonata**) provoque entre **15% et 70% de pertes** sur la production fruitière (mangues, agrumes, ananas).  
Le système de surveillance traditionnel repose sur des pièges à attractif (méthyl eugénol ou extraits de basilic local), mais le **comptage manuel des mouches** est fastidieux, lent et source d'erreurs.

**Mouche Sentinel** apporte une réponse technologique complète en connectant deux mondes :
1. **Vision par ordinateur (YOLO)** pour le comptage automatisé des individus piégés et le calcul du niveau d'infestation.
2. **Agent IA d'assistance agronomique (Google ADK / Gemini)** doté d'une mémoire conversationnelle, restituant des consignes d'action directement en **langue locale (Fon)** et en **Français** pour les producteurs et techniciens de terrain.

```
 [Photo du piège] 
        │
        ▼
 [Modèle YOLO léger]  ──▶  Comptage (B. dorsalis / B. zonata) + Niveau de gravité
        │
        ▼
 [Base géoréférencée & seuils]
        │
        ▼
 [Agent IA Google ADK à mémoire]  ◀── Requête vocale / texte du producteur
        │                              (Choix culture : Mangue, Agrumes, Ananas)
        ▼
 Conseils contextualisés & Alerte sonore en FON / FRANÇAIS
 (Ramassage, Solarisation, Augmentorium, Pièges au Basilic)
```

---

## 🛠️ Choix d'Architecture & Décisions Techniques

Toutes les décisions techniques ont été pensées pour allier **modularité**, **rapidité d'exécution hackathon** et **expérience démo infaillible devant le jury** :

### 1. Langue Locale : Focus exclusif sur le Fon (`fon`)
- **Constat empirique** : L'analyse des modèles open-source (Meta MMS, NLLB-200, Google Translate) montre que le Goun (`guw`) ne dispose d'aucun checkpoint TTS/ASR stable sur Hugging Face. À l'inverse, le **Fon dispose d'un modèle officiel `facebook/mms-tts-fon`**.
- **Décision** : Ciblage exclusif du **Fon**, parlé très largement dans le centre et le sud du Bénin.
- **Simplicité d'usage** : Aucun système probabiliste fragile de détection de langue. Un sélecteur explicite **[🇫🇷 Français | 🇧🇯 Fon]** permet de basculer instantanément.

### 2. Base de Connaissances Intégrée (Context Window Injection)
- **Choix délibéré** : Pour aller vite et éviter la complexité de bases de données vectorielles (RAG) ou de graphes de connaissances lourds, nous avons fait le choix pragmatique de **générer et injecter l'intégralité du corpus agronomique directement dans le contexte système (System Prompt) de l'agent**.
- **Contenu du contexte agronomique injecté** :
  - Données d'impact au Bénin (15-70% de pertes sur mangue).
  - Seuils de piégeage FTD (*Flies per Trap per Day*) : Faible (<2), Moyen (2-5), Critique (>5).
  - Protocoles de lutte prophylactique : Ramassage 2x/semaine, solarisation 48h en sacs plastiques hermétiques noirs au soleil, enfouissement profond (>50cm) avec chaux.
  - Utilisation d'**augmentoriums** (conservation des micro-guêpes parasitoïdes).
  - Répulsifs et attractifs naturels locaux à base de **basilic (*Ocimum basilicum*)**.

### 3. Agent IA Google ADK avec Mémoire Conversationnelle Native
- Construit avec le framework officiel **Google Agent Development Kit (`google-adk`)** :
  - **`Agent`** configuré avec le modèle **`gemini-3.6-flash`** et les règles de réessai HTTP (`HttpRetryOptions` sur codes 429, 500, 503, 504).
  - **Mémoire de session native via `InMemoryRunner`** : chaque échange est indexé par `session_id` (`runner = InMemoryRunner(agent=adk_agent)`). Le runner maintient l'état conversationnel natif, ce qui permet à l'agent de retenir le contexte, les pièges relevés et de ne plus répéter les formules de salutation lors des relances.
- **Résilience Démo & Architecture de Fallback (Hackathon Safe)** :
  - Pipeline prioritaire : Exécution native de l'agent **Google ADK**.
  - Filet de sécurité automatique : En cas de quota API épuisé, de latence réseau temporaire (ex. code 503 de l'API Google) ou d'absence de clé, le service bascule de manière invisible sur son moteur de repli agronomique bilingue pour garantir 0 crash devant le jury.

### 4. Adaptation à la Culture dès la Prise de Vue
- Trois cultures clés : **🥭 Manguier (par défaut)**, **🍊 Agrumes**, **🍍 Ananas**.
- L'utilisateur sélectionne la culture en 1 clic au moment du scan. Le conseil agronomique délivré s'ajuste immédiatement aux spécificités de la plante.

### 5. Modèle de Vision par Ordinateur : YOLO11n Optimisé Edge
D'après les résultats d'entraînement du projet ([about/modele.md](file:///d:/PROJECT/mouche_sentinelle/about/modele.md) et [Kaggle Notebook](https://www.kaggle.com/code/charmelaffoukou/mouche-sentinel-yolo-notebook)) :
- **Architecture retenue** : **YOLO11n (Nano)**
- **Précision mAP@50** : **0,8653 (86,5%)** — Dépasse la référence historique du papier scientifique sur le dataset Mendeley (qui plafonnait à 83-84% avec un modèle YOLOv5 beaucoup plus lourd).
- **Format de déploiement** : **ONNX (`best.onnx`)**
- **Taille du modèle** : Seulement **10,61 MB** (contre ~364 Mo pour les checkpoints complets PyTorch avec logs).
- **Latence d'inférence CPU** : **74,9 ms par image (~13,4 FPS)** sans aucun GPU nécessaire.
- **Adéquation terrain Bénin** : Le format ONNX ultraléger (10 Mo) permet une inférence quasi-instantanée sur un serveur modeste (CPU gratuit Render) ou un smartphone, parfaitement adapté aux contraintes de connectivité rurale.

### 6. Stratégie de Déploiement : Render + Vercel (Optimisation Mémoire RAM)
- **Problématique Render Free Plan (512 Mo RAM)** : Le runtime PyTorch complet (`torch` + `torchvision` = ~800 Mo de RAM) dépasse la limite de 512 Mo et provoque un crash mémoire (OOM).
- **Solution retenue** :
  1. **Frontend sur Vercel** : Next.js 14/15 déployé sur Vercel Edge.
  2. **Backend Unifié sur Render avec `onnxruntime`** : En utilisant le fichier `best.onnx` (10,61 MB) avec la bibliothèque légère `onnxruntime` (sans installer PyTorch), l'empreinte RAM totale du backend FastAPI + ONNX + Google ADK ne dépasse pas **150 à 200 Mo**, garantissant un fonctionnement fluide et 100% stable sur le plan gratuit de Render sans nécessiter deux services séparés !

---

## 📂 Arborescence du Projet (`Filetree`)

```text
mouche_sentinelle/
├── README.md                              # Documentation de référence, architecture & démo
├── about/
│   ├── projet_mouche_sentinel.tex         # Document scientifique de cadrage IndabaX
│   ├── langue_local_by_claude.md          # Note d'analyse linguistique (Fon vs Goun)
│   ├── day_1b_agent_architectures_43b7a3.py # Référence architecture Google ADK
│   └── data_sample/                       # Échantillons réels d'images de pièges et labels YOLO
├── backend/                               # API FastAPI (Déploiement Render)
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints/                 # Routes : /detect, /alerts, /advisory
│   │   ├── services/
│   │   │   ├── fon_agent.py               # Agent Google ADK à mémoire + contexte agronomique
│   │   │   ├── detector.py                # Wrapper YOLO (stub + chargement automatique poids)
│   │   │   └── alert_engine.py            # Logique de calcul des seuils & sévérité
│   │   └── data/
│   │       └── audio_samples/             # Fichiers audio d'alertes en Fon
│   ├── models/                            # Dépôt des poids entraînés (best.pt / best.onnx)
│   │   └── README.md
│   ├── Dockerfile
│   ├── render.yaml
│   └── requirements.txt
└── frontend/                              # Dashboard Next.js (Déploiement Vercel)
    ├── public/
    │   └── samples/                       # Photos d'exemples pour la démo en live
    └── src/
        ├── app/
        │   ├── page.tsx                   # Dashboard principal (indicateurs, alertes)
        │   ├── scan/page.tsx              # Scanner de piège photo + sélecteur culture
        │   ├── map/page.tsx               # Carte interactive des foyers d'infestation
        │   └── advisor/page.tsx           # Chatbot & agent vocal interactif en Fon
        ├── components/                    # Composants réutilisables (Jauges, Lecteur audio)
        └── lib/                           # Clients API
```

## 📡 Endpoints de l'API Backend (FastAPI / Render)

Documentation interactive Swagger disponible sur `http://localhost:8000/docs` (ou l'URL Render en production) :

| Méthode | Route | Rôle | Paramètres clés |
|---|---|---|---|
| `POST` | `/api/detection/scan` | Upload photo du piège, comptage *Bactrocera* et diagnostic sévérité | `file` (image), `crop` (`mangue`, `agrumes`, `ananas`) |
| `POST` | `/api/advisory/consult` | Consultation de l'agent Google ADK à mémoire conversationnelle | `language` (`fon`, `fr`), `crop`, `trap_count`, `alert_level`, `session_id`, `user_message` |
| `POST` | `/api/tts/generate` | Synthèse vocale native Fon par le modèle Meta MMS-TTS Fon | `text` (texte Fon généré par le LLM) |
| `GET` | `/api/traps/` | Carte et liste géoréférencée des pièges surveillés au Bénin | Filtres géographiques & niveau d'infestation |
| `GET` | `/health` | Healthcheck pour le monitoring Render | - |

---

## 🎙️ Synthèse Vocale Native en Langue Fon (Meta MMS-TTS) & Pipeline Zéro Latence

Contrairement aux solutions classiques qui lisent les langues africaines avec une voix de synthèse française déformée, Mouche Sentinel intègre le modèle officiel **Meta MMS-TTS Fon (`facebook/mms-tts-fon`)** optimisé pour les conditions réelles de terrain :

1. **Génération Dynamique par le LLM** :
   - Le modèle **Gemini 3.6 Flash** reçoit des consignes strictes de prosodie et de rythme (phrases courtes de 8-12 mots, virgules fréquentes pour les pauses de respiration naturelle).
2. **Nettoyage Acoustique & Respect de la Ponctuation** (`backend/app/services/tts_service.py`) :
   - Remplacement des signes de ponctuation par des respirations phonologiques explicites pour forcer le modèle neuronal VITS à respecter les silences naturels entre les propositions.
3. **Préchargement Proactif (Pre-fetching) & Cache Zéro Latence** :
   - Dès que l'agent génère le texte de sa réponse, le frontend déclenche **automatiquement en tâche de fond** la génération du fichier audio sans attendre que l'utilisateur clique sur « Écouter ».
   - L'URL audio est mise en cache localement : lorsque l'utilisateur appuie sur **« Écouter »**, la lecture démarre **instantanément (0 ms de latence perçue)**.
   - Les relectures ultérieures sont immédiatement résolues depuis le cache mémoire sans aucun nouvel appel réseau.

---

## 🧪 Interface de Test & Scénarios de Démonstration (Chat Advisor)

L'interface de chat (`frontend/src/app/advisor/page.tsx`) intègre un bouton **« Tester Détection »** qui ouvre une modale interactive permettant au jury ou aux testeurs d'injecter des résultats simulés du modèle YOLO en direct :

1. **🥭 Scénario 1 : Infestation Critique sur Manguier (Parakou / Borgou)** :
   - Capture de 18 mouches (> 5/jour = Critique).
   - Déclenche l'alerte maximale en **Fon** : ramassage systématique, solarisation en sacs noirs hermétiques et augmentorium.
2. **🥭 Scénario 2 : Pression Modérée sur Manguier (Début véraison)** :
   - Capture de 4 mouches (Seuil 2-5). Surveillance rapprochée et attractifs alternatifs.
3. **🍊 Scénario 3 : Forte Pression sur Agrumes (Zou / Bohicon)** :
   - Capture de 9 mouches sur orangerie/mandariniers. Risque de ponte dans l'écorce et chute précoce.
4. **🍍 Scénario 4 : Situation Saine sur Ananas (Bassin Allada)** :
   - Capture de 1 mouche (< 2). Entretien des parcelles et veille normale.
5. **🌿 Scénario 5 : Alternative Locale au Basilic (*Ocimum basilicum*)** :
   - Capture de 6 mouches. Recommandation de pièges artisanaux au basilic local si rupture de méthyl eugénol.

Chaque réponse de l'agent fournit :
- Le diagnostic et conseil textuel dans la langue choisie (**Fon** ou **Français**).
- La **transcription phonétique** pour faciliter la lecture/écoute.
- Les **actions concrètes à mener aujourd'hui**.
- Un bouton **« Écouter »** pour la vocalisation audio en Fon.

---

## 🔑 Configuration des Clés d'API

| Clé | Service | Obligatoire ? | Rôle |
|---|---|---|---|
| `GOOGLE_API_KEY` | Google AI Studio | **Oui** (pour mode live) | Alimente le raisonnement agronomique et la mémoire conversationnelle de l'agent Gemini 3.6 Flash / Google ADK. *(En cas d'absence, le mode fallback prend le relais).* |
| `HF_TOKEN` | Hugging Face | **Oui** (pour voix Fon) | Accès à l'API d'inférence du modèle Meta MMS-TTS Fon pour la synthèse vocale en langue locale. |

---

*Ce document est mis à jour au fil du développement de chaque brique du prototype.*
