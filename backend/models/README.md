# 📦 Modèle YOLO11n Détection Bactrocera (IndabaX Bénin)

D'après les résultats d'entraînement du notebook Kaggle :
- **Architecture** : YOLO11n (Nano)
- **mAP@50** : **0.8653 (86.5%)**
- **Fichier de production recommandé** : `best.onnx` (**10.61 MB**)
- **Latence CPU** : **74.9 ms / image**

### Instructions de déploiement :
1. Téléchargez le fichier `best.onnx` (10.61 MB) depuis les artefacts du notebook Kaggle.
2. Placez-le directement dans ce dossier : `backend/models/best.onnx`.
3. Le service `detector.py` détecte et charge automatiquement le fichier avec `onnxruntime` pour une inférence ultralégère compatible avec les 512 Mo de RAM du plan gratuit de Render.
