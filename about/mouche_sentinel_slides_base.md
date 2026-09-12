<!--
Base markdown pour slides — Mouche Sentinelle (Équipe Agriwatch - Groupe 25)
Compatible Marp / reveal.md / Google Slides / PowerPoint (chaque "---" sépare une diapo)
-->

# Slide 1 — Titre

## 🥭 Mouche Sentinelle
### Surveillance intelligente des mouches des fruits au Bénin

**Équipe Agriwatch — Groupe 25** | Deep Learning IndabaX Bénin 2026  
*Défis croisés : Agriculture & Sécurité alimentaire × IA & Langues locales*

---

# Slide 2 — Le problème au Bénin

## Un ravageur destructeur, une surveillance manuelle saturée

- **15% à 70% de pertes** documentées sur les mangues dans le Borgou/Atacora (*Bactrocera dorsalis*), touchant aussi agrumes et ananas.
- **Dispositif de terrain existant** : Réseau de piégeage actif depuis 2004 coordonné par l'**IITA (Cotonou)** et le Projet Régional CIRAD/WAFFI.
- **Le goulot d'étranglement** : Le comptage manuel hebdomadaire par les agents et gardiens de vergers est long, fastidieux et source d'erreurs face à des insectes collés ou superposés.

---

# Slide 3 — Notre solution

## Du piège au conseil agronomique en un flux unifié

1. 📸 **Prise de vue directe** : Le producteur ou l'agent envoie la photo du piège directement dans l'interface de discussion (façon WhatsApp).
2. 🔍 **Comptage automatique (YOLO)** : Détection et décompte des mouches (*Bactrocera dorsalis* vs *Bactrocera zonata*).
3. 🚨 **Calcul d'indice d'alerte** : Évaluation du seuil FTD (Faible <2, Moyen 2-5, Critique >5).
4. 🗣️ **Conseil vocal bilingue** : L'agent IA contextualise les mesures de lutte intégrée (solarisation, augmentorium, basilic) et répond en **Français** ou en **Fon** avec vocalisation instantanée.

*Ne remplace pas le technicien agricole : un outil d'aide à la décision pour prioriser les visites de terrain.*

---

# Slide 4 — Architecture technique

## Frugale, légère et pensée pour les contraintes du terrain

- **Vision Edge (YOLO11n)** : Entraîné sur 2 000 images de référence (Mendeley), exporté en **ONNX (10,6 Mo)**, tourne à 100% sur CPU sans GPU.
- **Agent IA & Mémoire** : Google Gemini 3.6 Flash avec historique de session, corpus agronomique béninois injecté (prophylaxie, seuils, alternatives locales).
- **Voix locale Fon** : Synthèse vocale neuronale via **Meta MMS-TTS Fon** (`facebook/mms-tts-fon`) avec préchargement zéro latence.
- **Déploiement Cloud Découplé** : Frontend Next.js sur Vercel Edge + Backend FastAPI léger sur Render (<200 Mo RAM).

---

# Slide 5 — Résultats mesurés

## Performance de pointe avec un modèle ultraléger

| Métrique | Valeur mesurée | Référence papier (YOLOv5) |
|---|---|---|
| **mAP@50 (test)** | **0,8653 (86,5%)** | 83–84% (modèle lourd) |
| **Vitesse CPU** | **74,9 ms / image** (~13,4 FPS) | Inférence quasi instantanée |
| **Taille modèle** | **10,61 Mo (ONNX)** | Empreinte minimale pour smartphone/serveur |

- ✅ Pipeline complet interconnecté et opérationnel en direct.
- ✅ Mécanisme de repli bilingue anti-crash pour garantir 0 interruption pendant la démo.

---

# Slide 6 — Démonstration Live

## L'application en action

- **Interface web responsive** (desktop & mobile) : `https://mouche-sentinelle-indabax...vercel.app`
- **Démo 1** : Analyse d'une photo de piège avec comptage instantané des mouches et classification d'espèce.
- **Démo 2** : Bascule instantanée de langue **Fon 🇧🇯 / Français 🇫🇷**.
- **Démo 3** : Écoute du conseil vocal en Fon avec restitution fluide des consignes de solarisation.

---

# Slide 7 — Rigueur scientifique & Validation

## Une démarche honnête et responsable

- ⚠️ **Validation locale impérative** : Valider le modèle sur un jeu d'images issues des pièges réels du Bénin (hors dataset public).
- ⚠️ **Calibration participative** : Ajuster les seuils de criticité avec les chercheurs et agents de terrain de l'IITA et du CIRAD.
- ⚠️ **Gestion des cas difficiles** : Signaler les images dégradées (insectes écrasés, poussière) pour demander une vérification humaine plutôt qu'afficher une fausse certitude.

---

# Slide 8 — Perspectives & Évolutions futures

## Vers une sentinelle autonome et prédictive

1. 📡 **Pièges connectés autonomes (Smart Traps)** :
   - Embarquer des micro-capteurs photo solaires (type ESP32-CAM ou Raspberry Pi Zero) directement dans les vergers.
   - Exécuter le modèle **YOLO11n ONNX directement on-device (Edge AI)** sur le capteur avec transmission périodique basse consommation (LoRa / GSM).
2. 📈 **Modélisation prédictive des infestations (Early Warning)** :
   - Coupler les historiques de captures aux données météo (température, humidité relative, pluviométrie).
   - Développer un modèle temporel (LSTM / régression) pour **prédire le pic d'émergence des populations à 7–14 jours** et alerter avant que les dégâts ne surviennent.

---

# Slide 9 — Impact & Bénéficiaires

## Accélérer la veille phytosanitaire sans surcoût

- **Producteurs de fruits** : Alertés plus tôt, conseils immédiats et compréhensibles dans leur langue maternelle.
- **Agents agricoles & IITA** : Vue d'ensemble centralisée, ciblage prioritaire des vergers à risque critique.
- **Filière fruitière béninoise** : Réduction des pertes post-récolte et valorisation des méthodes agroécologiques (lutte intégrée).

---

# Slide 10 — Conclusion

## Mouche Sentinelle

> **Transformer une simple photo de piège en diagnostic agronomique fiable, prédictif et actionnable en langue locale.**

**Équipe Agriwatch — Groupe 25**  
*Merci pour votre attention ! Place à la démonstration.*
