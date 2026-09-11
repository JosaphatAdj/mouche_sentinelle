Modèle retenu : yolo11n
Test mAP50 : 0.8653
Latence CPU : 74.9 ms/image
Taille ONNX : 10.61 MB
Environ 13.4 FPS

AVIS CLAUDE

Ces chiffres sont bons — vraiment bons, même :

- **mAP50 = 0,8653** : ça dépasse la référence publiée sur ce même type de tâche (le papier associé au dataset Mendeley obtenait 83-84% avec YOLOv5). Toi tu es à 86,5% avec un modèle **beaucoup plus léger** (nano). C'est un argument fort à mettre en avant dans le pitch — pas juste "on a reproduit un résultat", mais "on a fait mieux avec moins de ressources".
- **10,61 MB en ONNX** : très léger, déployable facilement sur mobile ou serveur modeste — cohérent avec un contexte terrain béninois où l'accès à du matériel puissant n'est pas garanti.
- **74,9 ms/image sur CPU (~13,4 FPS)** : pour ton cas d'usage réel (le producteur prend une photo du piège, pas un flux vidéo continu), c'est **largement suffisant** — quasi instantané à l'usage. Attention juste à la formulation "temps réel" dans le pitch : 13,4 FPS est correct pour du streaming vidéo basique, mais reste modeste comparé aux standards "temps réel" habituels (30+ FPS). Pour rester rigoureux, je formulerais plutôt "inférence quasi-instantanée sur CPU, sans GPU" plutôt que "temps réel" si le jury est pointilleux sur le vocabulaire — ça évite qu'on te challenge sur un mot alors que la perf réelle est très bonne pour l'usage prévu.


