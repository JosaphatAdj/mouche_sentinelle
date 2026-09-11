import os
import io
import numpy as np
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from PIL import Image

class BoundingBox(BaseModel):
    class_id: int          # 0: Bactrocera dorsalis, 1: Bactrocera zonata
    class_name: str        # "Bactrocera dorsalis" ou "Bactrocera zonata"
    confidence: float
    x_center: float        # Normalisé [0, 1]
    y_center: float
    width: float
    height: float

class DetectionResult(BaseModel):
    total_count: int
    count_dorsalis: int
    count_zonata: int
    alert_level: str       # "low", "medium", "critical"
    alert_message_fr: str
    alert_message_fon: str
    boxes: List[BoundingBox]
    model_source: str      # "real_yolo_onnx" ou "mock_calibrated"

class DetectorService:
    def __init__(self, models_dir: str = "backend/models"):
        self.models_dir = models_dir
        self.onnx_session = None
        self.model_loaded = False
        self._try_load_model()

    def _try_load_model(self):
        """Charge prioritairement best.onnx avec onnxruntime (léger, ~180 Mo RAM)."""
        onnx_path = os.path.join(self.models_dir, "best.onnx")
        if os.path.exists(onnx_path):
            try:
                import onnxruntime as ort
                self.onnx_session = ort.InferenceSession(onnx_path)
                self.model_loaded = True
                print(f"[DetectorService] ✅ Modèle ONNX YOLO11n chargé avec succès depuis {onnx_path} !")
                return
            except Exception as e:
                print(f"[DetectorService] Erreur chargement ONNX {onnx_path}: {e}")

        print("[DetectorService] Mode simulation calibré actif.")

    def detect_image(self, image_bytes: bytes, crop: str = "mangue") -> DetectionResult:
        """Exécute l'inférence ONNX réelle du modèle YOLO11n ou le fallback calibré."""
        if self.model_loaded and self.onnx_session:
            try:
                return self._run_onnx_inference(image_bytes, crop)
            except Exception as e:
                print(f"[DetectorService] Erreur inférence ONNX réelle: {e}. Bascule sur simulation.")

        return self._run_calibrated_mock(crop)

    def _run_onnx_inference(self, image_bytes: bytes, crop: str) -> DetectionResult:
        """Inférence native avec preprocessing 640x640 et NMS."""
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        orig_w, orig_h = img.size

        # Redimensionnement 640x640 pour YOLO11
        img_resized = img.resize((640, 640))
        img_data = np.array(img_resized, dtype=np.float32) / 255.0
        # HWC -> CHW -> NCHW
        img_data = np.transpose(img_data, (2, 0, 1))
        input_tensor = np.expand_dims(img_data, axis=0)

        # Inférence ONNX
        input_name = self.onnx_session.get_inputs()[0].name
        outputs = self.onnx_session.run(None, {input_name: input_tensor})
        raw_preds = outputs[0]  # Shape: (1, 6, 8400)

        # Décodage (1, 6, 8400) -> (8400, 6)
        predictions = raw_preds[0].T  # (8400, 6) : cx, cy, w, h, score_cls0, score_cls1
        boxes_xywh = predictions[:, :4]
        class_scores = predictions[:, 4:]

        max_scores = np.max(class_scores, axis=1)
        pred_classes = np.argmax(class_scores, axis=1)

        # Seuil de confiance (0.35)
        conf_mask = max_scores > 0.35
        filtered_boxes = boxes_xywh[conf_mask]
        filtered_scores = max_scores[conf_mask]
        filtered_classes = pred_classes[conf_mask]

        # NMS simple pour éliminer les doublons
        boxes_to_keep = self._simple_nms(filtered_boxes, filtered_scores, iou_threshold=0.45)

        detected_boxes: List[BoundingBox] = []
        c_dorsalis = 0
        c_zonata = 0

        for idx in boxes_to_keep:
            cx, cy, w, h = filtered_boxes[idx]
            conf = float(filtered_scores[idx])
            cls_id = int(filtered_classes[idx])
            cls_name = "Bactrocera dorsalis" if cls_id == 0 else "Bactrocera zonata"

            if cls_id == 0:
                c_dorsalis += 1
            else:
                c_zonata += 1

            detected_boxes.append(BoundingBox(
                class_id=cls_id,
                class_name=cls_name,
                confidence=round(conf, 2),
                x_center=round(float(cx / 640.0), 4),
                y_center=round(float(cy / 640.0), 4),
                width=round(float(w / 640.0), 4),
                height=round(float(h / 640.0), 4),
            ))

        total = len(detected_boxes)
        level, msg_fr, msg_fon = self._evaluate_risk(total, crop)

        return DetectionResult(
            total_count=total,
            count_dorsalis=c_dorsalis,
            count_zonata=c_zonata,
            alert_level=level,
            alert_message_fr=msg_fr,
            alert_message_fon=msg_fon,
            boxes=detected_boxes,
            model_source="real_yolo_onnx"
        )

    def _simple_nms(self, boxes: np.ndarray, scores: np.ndarray, iou_threshold: float = 0.45) -> List[int]:
        """Suppression des non-maximaux pour fusionner les détections multiples."""
        if len(boxes) == 0:
            return []

        # Convertir cx, cy, w, h en x1, y1, x2, y2
        x1 = boxes[:, 0] - boxes[:, 2] / 2
        y1 = boxes[:, 1] - boxes[:, 3] / 2
        x2 = boxes[:, 0] + boxes[:, 2] / 2
        y2 = boxes[:, 1] + boxes[:, 3] / 2
        areas = (x2 - x1) * (y2 - y1)

        order = scores.argsort()[::-1]
        keep = []

        while order.size > 0:
            i = order[0]
            keep.append(i)

            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])

            w = np.maximum(0.0, xx2 - xx1)
            h = np.maximum(0.0, yy2 - yy1)
            inter = w * h

            iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)
            inds = np.where(iou <= iou_threshold)[0]
            order = order[inds + 1]

        return keep

    def _run_calibrated_mock(self, crop: str) -> DetectionResult:
        """Simulation basée sur les annotations du dataset Mendeley Data."""
        sample_boxes = [
            BoundingBox(class_id=0, class_name="Bactrocera dorsalis", confidence=0.89, x_center=0.4897, y_center=0.6577, width=0.0908, height=0.0947),
            BoundingBox(class_id=1, class_name="Bactrocera zonata", confidence=0.86, x_center=0.6259, y_center=0.7104, width=0.0976, height=0.1025),
            BoundingBox(class_id=0, class_name="Bactrocera dorsalis", confidence=0.91, x_center=0.6621, y_center=0.1772, width=0.0703, height=0.0771),
            BoundingBox(class_id=1, class_name="Bactrocera zonata", confidence=0.84, x_center=0.5214, y_center=0.4345, width=0.0839, height=0.0722),
            BoundingBox(class_id=0, class_name="Bactrocera dorsalis", confidence=0.88, x_center=0.7353, y_center=0.5219, width=0.1074, height=0.0830),
            BoundingBox(class_id=1, class_name="Bactrocera zonata", confidence=0.82, x_center=0.6254, y_center=0.6000, width=0.0947, height=0.0791),
            BoundingBox(class_id=0, class_name="Bactrocera dorsalis", confidence=0.93, x_center=0.8105, y_center=0.7280, width=0.1308, height=0.0908),
            BoundingBox(class_id=1, class_name="Bactrocera zonata", confidence=0.87, x_center=0.9272, y_center=0.5078, width=0.0771, height=0.0781),
            BoundingBox(class_id=0, class_name="Bactrocera dorsalis", confidence=0.85, x_center=0.7050, y_center=0.6279, width=0.0761, height=0.0839),
        ]
        
        c_dorsalis = sum(1 for b in sample_boxes if b.class_id == 0)
        c_zonata = sum(1 for b in sample_boxes if b.class_id == 1)
        total = len(sample_boxes)
        level, msg_fr, msg_fon = self._evaluate_risk(total, crop)

        return DetectionResult(
            total_count=total,
            count_dorsalis=c_dorsalis,
            count_zonata=c_zonata,
            alert_level=level,
            alert_message_fr=msg_fr,
            alert_message_fon=msg_fon,
            boxes=sample_boxes,
            model_source="mock_calibrated"
        )

    def _evaluate_risk(self, count: int, crop: str):
        if count <= 2:
            return "low", "Infestation faible. Maintenir la surveillance.", "Nu le do te ganji. Kpon atin le azan we dokpo."
        elif count <= 5:
            return "medium", f"Risque modéré pour vos {crop}s. Contrôler les fruits piqués.", f"Xɛsi kpon kpon do {crop} ji. Be atinsinsen e gble le."
        else:
            return "critical", f"Alerte Maximale ! Forte pression ({count} mouches). Perte de 15-70% imminente.", f"Xɛsi ɖo gbeji nú {crop} towe ! Mouche {count} wɛ ɖo hɔntɔn mɛ !"

detector_service = DetectorService()
