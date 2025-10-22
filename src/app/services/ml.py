from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

import joblib

from ..config import get_settings
from ..models.incident import IncidentCategory

logger = logging.getLogger(__name__)


class IncidentClassifier:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.model = None
        self.model_version = self.settings.model_fallback_version
        self._load_model()

    def _load_model(self) -> None:
        model_path = Path(self.settings.model_path)
        if model_path.exists():
            try:
                self.model = joblib.load(model_path)
                self.model_version = getattr(self.model, "version", model_path.stem)
                logger.info("Loaded ML model from %s", model_path)
            except Exception as exc:  # pragma: no cover - best effort
                logger.exception("Failed to load model %s. Falling back to heuristic", exc_info=exc)
                self.model = None
        else:
            logger.warning("Model file %s not found. Using fallback heuristic.", model_path)

    def predict(self, text: str, metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
        if self.model is not None:
            prediction = self.model.predict([text])[0]
            confidence = max(getattr(self.model, "predict_proba", lambda _: [[1.0]])([text])[0])  # type: ignore[arg-type]
            category = IncidentCategory(prediction)
            return {
                "category": category,
                "confidence": float(confidence),
                "model_version": self.model_version,
            }
        # fallback heuristic
        lower = text.lower()
        if "jatuh" in lower or "fall" in lower:
            category = IncidentCategory.KTD
            confidence = 0.6
        elif "med" in lower or "obat" in lower:
            category = IncidentCategory.KNC
            confidence = 0.55
        else:
            category = IncidentCategory.KTC
            confidence = 0.5
        return {
            "category": category,
            "confidence": confidence,
            "model_version": self.model_version,
        }


classifier = IncidentClassifier()


def predict_incident(text: str, metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return classifier.predict(text, metadata)
