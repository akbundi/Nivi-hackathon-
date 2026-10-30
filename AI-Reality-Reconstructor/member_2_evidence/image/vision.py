"""Computer vision and object detection functionality for image evidence."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("member_2_evidence.vision")

# Global model cache to avoid re-instantiating heavyweight YOLO models per image
_YOLO_MODEL = None
_YOLO_LOADED = False
_YOLO_ERROR: str | None = None


def get_yolo_model(model_name: str = "yolov8n.pt"):
    """
    Load YOLO model safely with caching.
    Returns (model, error_message).
    """
    global _YOLO_MODEL, _YOLO_LOADED, _YOLO_ERROR

    if _YOLO_LOADED:
        return _YOLO_MODEL, _YOLO_ERROR

    try:
        from ultralytics import YOLO

        _YOLO_MODEL = YOLO(model_name)
        _YOLO_LOADED = True
        _YOLO_ERROR = None
        logger.info("YOLO model '%s' loaded successfully.", model_name)
    except Exception as exc:  # pragma: no cover
        _YOLO_MODEL = None
        _YOLO_LOADED = True
        _YOLO_ERROR = f"Failed to load YOLO model: {exc}"
        logger.warning(_YOLO_ERROR)

    return _YOLO_MODEL, _YOLO_ERROR


def detect_objects(
    image_path: str | Path,
    confidence_threshold: float = 0.25,
    model_name: str = "yolov8n.pt",
) -> dict[str, Any]:
    """
    Detect objects in an image using YOLO.
    
    Returns a dict with:
      - available: bool
      - status: 'completed' | 'unavailable' | 'failed'
      - model: str
      - error: str | None
      - objects: list of dicts with label, confidence, box [x1, y1, x2, y2], status="INFERRED"
    """
    path = Path(image_path)
    if not path.is_file():
        return {
            "available": False,
            "status": "failed",
            "model": model_name,
            "error": f"Image file not found: {path}",
            "objects": [],
        }

    model, load_error = get_yolo_model(model_name)
    if model is None:
        return {
            "available": False,
            "status": "unavailable",
            "model": model_name,
            "error": load_error or "Ultralytics YOLO not available",
            "objects": [],
        }

    try:
        results = model.predict(source=str(path), conf=confidence_threshold, verbose=False)
        detected_objects = []

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue

            for box in boxes:
                cls_id = int(box.cls[0].item()) if box.cls is not None else -1
                label = model.names.get(cls_id, f"class_{cls_id}") if hasattr(model, "names") else f"class_{cls_id}"
                conf = float(box.conf[0].item()) if box.conf is not None else 0.0
                xyxy = [round(float(coord), 2) for coord in box.xyxy[0].tolist()]

                detected_objects.append({
                    "label": label,
                    "confidence": round(conf, 4),
                    "box": xyxy,
                    "status": "INFERRED",
                })

        return {
            "available": True,
            "status": "completed",
            "model": model_name,
            "error": None,
            "objects": detected_objects,
        }

    except Exception as exc:
        logger.exception("Error running YOLO inference on %s: %s", path, exc)
        return {
            "available": False,
            "status": "failed",
            "model": model_name,
            "error": f"Inference error: {exc}",
            "objects": [],
        }
