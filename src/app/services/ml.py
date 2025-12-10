from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency for fallback
    SentenceTransformer = None

from ..config import get_settings
from ..models.incident import IncidentCategory

logger = logging.getLogger(__name__)

# Model exported from modeling notebook: LightGBM classifier fed with MiniLM sentence embeddings.
MINILM_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
# Reconstructed label encoder classes (LabelEncoder sorts alphabetically).
LABEL_ENCODER_CLASSES: List[str] = [
    "KNC - Kejadian Nyaris Cedera",
    "KPC - Kejadian Potensial Cedera",
    "KTC - Kejadian Tidak Cedera",
    "KTD - Kejadian Tidak Diharapkan",
    "SENTINEL - Insiden KTD dengan dampak sedang - berat",
]

# Abbreviation map taken from modeling notebook.
MED_ABBREVIATIONS = {
    "dx": "diagnosis",
    "tx": "terapi",
    "k/u": "kondisi umum",
    "ku": "kondisi umum",
    "td": "tekanan darah",
    "tensi": "tekanan darah",
    "hr": "nadi",
    "rr": "respirasi",
    "px": "pasien",
    "os": "orang sakit",
    "tth": "tertawa terbahak",
    "yg": "yang",
    "dg": "dengan",
    "dr": "dokter",
    "tn": "tuan",
    "ny": "nyonya",
    "an": "anak",
}


class IncidentClassifier:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.model = None
        self.model_version = self.settings.model_fallback_version
        self.embedder: SentenceTransformer | None = None
        self.label_decoder = {idx: label for idx, label in enumerate(LABEL_ENCODER_CLASSES)}
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

    def _ensure_embedder(self) -> None:
        """Load the MiniLM encoder lazily to avoid start-up lag."""
        if self.embedder is None:
            if SentenceTransformer is None:
                logger.warning("sentence_transformers not installed. Using fallback prediction.")
                return
            try:
                self.embedder = SentenceTransformer(MINILM_MODEL_NAME)
            except Exception as exc:  # pragma: no cover - best effort
                logger.exception("Failed to load sentence transformer %s", MINILM_MODEL_NAME, exc_info=exc)
                self.embedder = None

    def _preprocess_for_bert(self, text: str) -> str:
        """Preprocessing pipeline used during training for MiniLM embeddings."""
        if not isinstance(text, str):
            return ""
        text = text.lower()
        text = text.replace("<.>", ".")
        text = re.sub(r"<\s*[a-zA-Z0-9]+\s*>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        words = text.split()
        words = [MED_ABBREVIATIONS.get(w, w) for w in words]
        text = " ".join(words)

        text = re.sub(r"([.,!?])", r" \1 ", text)
        return re.sub(r"\s+", " ", text).strip()

    def _label_to_category(self, label: Optional[str]) -> Optional[IncidentCategory]:
        if not label:
            return None

        normalized = label.upper()
        if normalized.startswith("KTD"):
            return IncidentCategory.KTD
        if normalized.startswith("KTC"):
            return IncidentCategory.KTC
        if normalized.startswith("KNC"):
            return IncidentCategory.KNC
        if normalized.startswith("KPC"):
            return IncidentCategory.KPCS
        if normalized.startswith("SENTINEL"):
            return IncidentCategory.Sentinel
        return None

    def _fallback_prediction(self, text: str) -> Dict[str, Any]:
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

    def predict(self, text: str, metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
        if self.model is None:
            print("[ML] Model missing, using fallback", flush=True)
            return self._fallback_prediction(text)

        print("[ML] Ensuring embedder", flush=True)
        self._ensure_embedder()
        if self.embedder is None:
            print("[ML] Embedder failed to load, using fallback", flush=True)
            return self._fallback_prediction(text)

        print("[ML] Preprocessing text", flush=True)
        processed = self._preprocess_for_bert(text)
        print("[ML] Encoding with MiniLM", flush=True)
        embeddings = self.embedder.encode([processed], convert_to_numpy=True).astype(np.float32)

        print("[ML] Running classifier", flush=True)
        class_idx = int(self.model.predict(embeddings)[0])
        proba_fn = getattr(self.model, "predict_proba", None)
        confidence = (
            float(proba_fn(embeddings)[0][class_idx])
            if callable(proba_fn)
            else 1.0
        )

        print(f"[ML] Decoding class index {class_idx}", flush=True)
        label = self.label_decoder.get(class_idx)
        category = self._label_to_category(label)
        if category is None:
            print("[ML] Unknown label, using fallback", flush=True)
            return self._fallback_prediction(text)

        print(f"[ML] Prediction complete: {category.value} (conf={confidence:.3f})", flush=True)
        return {
            "category": category,
            "confidence": confidence,
            "model_version": self.model_version,
        }


classifier = IncidentClassifier()


def predict_incident(text: str, metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return classifier.predict(text, metadata)


# -------- SKP/MDP predictor --------

_skp_mdp_artifacts: Optional[dict] = None


def _load_skp_mdp_artifacts() -> Optional[dict]:
    global _skp_mdp_artifacts
    if _skp_mdp_artifacts is not None:
        return _skp_mdp_artifacts
    settings = get_settings()
    model_path = Path(settings.skp_mdp_model_path)
    if not model_path.exists():
        logger.warning("SKP/MDP model %s not found. Skipping SKP/MDP prediction.", model_path)
        _skp_mdp_artifacts = None
        return None
    try:
        logger.info("Loading SKP/MDP model from %s", model_path)
        _skp_mdp_artifacts = joblib.load(model_path)
    except Exception as exc:  # pragma: no cover - best effort
        logger.exception("Failed to load SKP/MDP model %s", model_path, exc_info=exc)
        _skp_mdp_artifacts = None
    return _skp_mdp_artifacts


def predict_skp_mdp(text: str) -> Dict[str, Optional[str]]:
    artifacts = _load_skp_mdp_artifacts()
    if artifacts is None:
        return {"skp": None, "mdp": None}
    try:
        logger.info("[SKP/MDP] Predicting for text length=%s", len(text) if text else 0)
        pipeline = artifacts["model_pipeline"]
        encoders = artifacts["label_encoders"]
        targets = artifacts["target_columns"]
        pred_indices = pipeline.predict([str(text)])
        logger.info("[SKP/MDP] Raw pred indices: %s", pred_indices)
        result = {}
        for i, col_name in enumerate(targets):
            idx = pred_indices[0][i]
            label = encoders[col_name].inverse_transform([idx])[0]
            result[col_name] = label
        def normalize(label: Any, is_skp: bool) -> str | None:
            if label is None:
                return None
            raw = str(label).strip().lower()
            tokens = re.split(r"[:\s]+", raw)
            digits = re.findall(r"\d+", raw)
            if digits:
                return digits[0]
            for tok in tokens:
                if is_skp and tok.startswith("skp"):
                    num = re.findall(r"\d+", tok)
                    return num[0] if num else tok.replace(" ", "").replace("skp", "skp")
                if not is_skp and tok.startswith("mdp"):
                    num = re.findall(r"\d+", tok)
                    return num[0] if num else tok.replace(" ", "").replace("mdp", "mdp")
            # fallback: strip spaces
            return raw.replace(" ", "")

        skp_key = next((k for k in result.keys() if k.lower().startswith("skp")), None)
        mdp_key = next((k for k in result.keys() if "mdp" in k.lower()), None)

        return {
            "skp": normalize(result.get(skp_key), True) if skp_key else None,
            "mdp": normalize(result.get(mdp_key), False) if mdp_key else None,
        }
    except Exception as exc:  # pragma: no cover - best effort
        logger.exception("Failed SKP/MDP prediction", exc_info=exc)
        return {"skp": None, "mdp": None}
