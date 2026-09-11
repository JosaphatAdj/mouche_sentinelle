# 🥭 Mouche Sentinel — Surveillance Intelligente de la Mouche des Fruits (*Bactrocera*)

> **Projet Hackathon — Deep Learning IndabaX Bénin 2026**  
> *Défis croisés : Agriculture & Sécurité Alimentaire × IA & Langues Locales*

---

## 🚀 Démarrage Rapide

### Prérequis

- **Python 3.11+**
- **Node.js 18+** & **npm 9+**
- Un fichier `.env` dans `backend/` (voir section Configuration)

---

### 1. Cloner le dépôt

```bash
git clone https://github.com/JosaphatAdj/mouche_sentinelle.git
cd mouche_sentinelle
```

---

### 2. Backend (FastAPI)

```bash
# Créer et activer l'environnement virtuel
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

# Installer les dépendances
pip install -r backend/requirements.txt

# Créer le fichier de configuration des clés API
cp backend/.env.example backend/.env
# Éditer backend/.env et renseigner vos clés (voir section Configuration)

# Lancer le serveur
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Le backend est accessible sur **http://localhost:8000**  
Documentation Swagger interactive : **http://localhost:8000/docs**

---

### 3. Frontend (Next.js)

```bash
cd frontend

# Installer les dépendances
npm install

# Lancer le serveur de développement
npm run dev
```

L'application est accessible sur **http://localhost:3000**

---

### 4. Configuration des clés API (`backend/.env`)

Créez le fichier `backend/.env` avec le contenu suivant :

```env
GOOGLE_API_KEY=votre_cle_google_ai_studio
HF_TOKEN=votre_token_hugging_face
```

| Variable | Service | Rôle |
|---|---|---|
| `GOOGLE_API_KEY` | [Google AI Studio](https://aistudio.google.com) | Agent Gemini 3.6 Flash — raisonnement agronomique & mémoire conversationnelle |
| `HF_TOKEN` | [Hugging Face](https://huggingface.co/settings/tokens) | Synthèse vocale Meta MMS-TTS Fon (`facebook/mms-tts-fon`) |

> **Note** : Sans ces clés, le backend démarre en mode fallback — les réponses sont pré-calibrées et la vocalisation utilise la synthèse du navigateur.

---

### 5. Modèle YOLO11n (`backend/models/best.onnx`)

Le modèle est inclus dans le dépôt (`backend/models/best.onnx`, 10,6 MB).  
Il est chargé automatiquement au démarrage du backend via `onnxruntime` (sans PyTorch).

Pour tester l'inférence manuellement :

```bash
python -c "
import onnxruntime as ort
sess = ort.InferenceSession('backend/models/best.onnx')
print('Modèle OK — Inputs:', [i.name for i in sess.get_inputs()])
"
```

---

## 📌 Présentation du Projet

En Afrique de l'Ouest et particulièrement au Bénin, la mouche des fruits (**Bactrocera dorsalis** et **Bactrocera zonata**) provoque entre **15% et 70% de pertes** sur la production fruitière (mangues, agrumes, ananas).

**Mouche Sentinel** connecte deux technologies :
1. **Vision par ordinateur (YOLO11n ONNX)** — comptage automatique des mouches piégées, 74,9 ms CPU, 10,6 MB.
2. **Agent IA Gemini 3.6 Flash** — conseils agronomiques contextualisés avec mémoire de session, en **Fon** et en **Français**.

```
[Photo du piège]
      │
      ▼
[YOLO11n ONNX]  ──▶  Comptage (B. dorsalis / B. zonata) + Niveau de gravité
      │
      ▼
[Agent Gemini + mémoire]  ◀── Question / message du producteur
      │
      ▼
Conseil contextuel + Audio TTS Fon (Meta MMS)
```

---

## 📡 API Backend

| Méthode | Route | Rôle |
|---|---|---|
| `POST` | `/api/detection/scan` | Upload photo → inférence YOLO11n → comptage + niveau d'alerte |
| `POST` | `/api/advisory/consult` | Consultation agent Gemini avec mémoire de session |
| `POST` | `/api/tts/generate` | Synthèse vocale Meta MMS-TTS Fon |
| `GET` | `/api/traps/` | Liste des pièges géoréférencés |
| `GET` | `/health` | Healthcheck Render |

---

## 🛠️ Stack Technique

| Couche | Technologie |
|---|---|
| Frontend | Next.js 15, Tailwind CSS, Lucide React |
| Backend | FastAPI, Python 3.12 |
| Détection | YOLO11n ONNX (`onnxruntime`, sans PyTorch) |
| Agent IA | Google Gemini 3.6 Flash (`google-genai`) |
| TTS Fon | Meta MMS-TTS (`facebook/mms-tts-fon`) via Gradio Space |
| Déploiement | Vercel (frontend) + Render (backend) |

---

## 🧪 Scénarios de Démonstration

L'interface intègre un bouton **« Tester Détection »** avec 5 scénarios pré-configurés :

| # | Culture | Capture | Niveau |
|---|---|---|---|
| 1 | 🥭 Manguier (Borgou/Parakou) | 18 mouches | 🔴 Critique |
| 2 | 🥭 Manguier (début véraison) | 4 mouches | 🟡 Modéré |
| 3 | 🍊 Agrumes (Zou/Bohicon) | 9 mouches | 🔴 Critique |
| 4 | 🍍 Ananas (Bassin Allada) | 1 mouche | 🟢 Faible |
| 5 | 🌿 Alternative basilic local | 6 mouches | 🔴 Critique |

---

## 🎙️ Synthèse Vocale Fon (Zéro Latence)

- L'audio est pré-généré en arrière-plan dès réception de la réponse de l'agent.
- **Latence perçue = 0 ms** au clic sur « Écouter » (lecture depuis le cache).

---

## 📊 Performances du Modèle YOLO11n

| Métrique | Valeur |
|---|---|
| mAP@50 | **86,53%** |
| Taille ONNX | **10,61 MB** |
| Latence CPU | **74,9 ms / image** |
| Dataset | Mendeley — 2000 images *Bactrocera* |

> Dépasse la référence publiée (YOLOv5, 83-84% mAP) avec un modèle 4× plus léger.

Notebook d'entraînement : [Kaggle — Mouche Sentinel YOLO](https://www.kaggle.com/code/charmelaffoukou/mouche-sentinel-yolo-notebook)

---

*Projet IndabaX Bénin 2026 — Développé avec ❤️ pour les producteurs du Bénin*
