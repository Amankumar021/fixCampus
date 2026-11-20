import numpy as np
import importlib.util
from pathlib import Path
import sys
from typing import Dict, Any
from app.ml.loader import load_model
from app.ml.preprocessor import clean_text
from app.core.logging import logger
from app.core.config import settings


def _load_semantic_predictor():
    ml_root = Path(__file__).resolve().parents[3] / "ml"
    predictor_path = ml_root / "semantic" / "predictor.py"
    if str(ml_root) not in sys.path:
        sys.path.insert(0, str(ml_root))
    spec = importlib.util.spec_from_file_location("campusfix_semantic_predictor", predictor_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Semantic predictor not found at {predictor_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.predict_category


try:
    predict_category = _load_semantic_predictor()
except (ImportError, ModuleNotFoundError, FileNotFoundError) as e:
    predict_category = None
    logger.info(f"Semantic predictor unavailable; local classifier will be used: {e}")

# Keyword-based robust heuristics fallback in case model is absent or input is ambiguous
KEYWORD_RULES = {
    "Electrical": ["light", "fan", "switch", "ac", "air conditioner", "wire", "power", "electricity", "socket", "cooler"],
    "IT": ["wifi", "internet", "computer", "lab", "portal", "system", "router", "login", "printer", "projector", "network"],
    "Plumbing": ["leak", "tap", "pipe", "drain", "water", "sink", "flush", "basin"],
    "Cleanliness": ["dust", "dirty", "trash", "garbage", "waste", "clean", "sweep", "mop", "litter"],
    "Security": ["theft", "stolen", "guard", "gate", "cctv", "camera", "unauthorized", "trespass", "fight"],
    "Furniture": ["chair", "desk", "bench", "table", "board", "broken leg", "podium"],
    "Civil Maintenance": ["wall", "crack", "ceiling", "door", "window", "stair", "floor", "masonry", "plaster"],
    "Sanitation": ["toilet", "washroom", "bathroom", "sewage", "smell", "urinal"],
    "Cafeteria": ["food", "canteen", "lunch", "cafeteria", "mess", "meal", "stale"]
}


def rule_based_predict(text: str) -> Dict[str, Any]:
    cleaned = clean_text(text)
    scores = {}
    for cat, keywords in KEYWORD_RULES.items():
        match_count = sum(1 for kw in keywords if kw in cleaned)
        scores[cat] = match_count

    best_cat = max(scores, key=scores.get)
    max_score = scores[best_cat]

    if max_score > 0:
        confidence = min(0.65 + (max_score * 0.1), 0.95)
        return {
            "predicted_category": best_cat,
            "confidence": round(confidence, 2),
            "is_confident": True,
            "method": "heuristic_rule_fallback",
        }
    return {
        "predicted_category": "Other",
        "confidence": 0.30,
        "is_confident": False,
        "method": "default_fallback",
    }


def predict_complaint_category(description: str) -> Dict[str, Any]:
    if not description or not description.strip():
        return {
            "predicted_category": "Other",
            "confidence": 0.0,
            "is_confident": False,
            "method": "empty_input",
        }

    cleaned = clean_text(description)

    model = load_model()

    if model is not None:
        try:
            # Predict with model pipeline
            prediction = model.predict([cleaned])[0]
            confidence = 0.85

            if hasattr(model, "predict_proba"):
                probs = model.predict_proba([cleaned])[0]
                confidence = float(np.max(probs))
                is_confident = confidence >= settings.ML_CONFIDENCE_THRESHOLD
            elif hasattr(model, "decision_function"):
                decision = model.decision_function([cleaned])[0]
                # SVM decision margin is a ranking signal, not a calibrated probability.
                ordered = np.sort(np.atleast_1d(decision))
                margin = float(ordered[-1] - ordered[-2]) if len(ordered) > 1 else 0.0
                # This score is an uncalibrated ranking signal. Do not present a sigmoid
                # transform of the margin as a probability to users or store it as one.
                confidence = min(max(margin / 2.0, 0.0), 1.0)
                is_confident = margin >= settings.ML_CONFIDENCE_THRESHOLD
                if not is_confident:
                    return {
                        "predicted_category": "Other",
                        "confidence": round(confidence, 2),
                        "is_confident": False,
                        "method": "svm_low_margin_abstention",
                    }
            else:
                is_confident = True

            return {
                "predicted_category": str(prediction),
                "confidence": round(max(0.0, min(confidence, 1.0)), 2),
                "is_confident": is_confident,
                "method": "svm_ml_pipeline",
            }
        except Exception as e:
            logger.error(f"Error during ML inference: {e}")

    if predict_category is not None:
        try:
            semantic_result = predict_category(description)
            confidence = float(semantic_result["similarity_score"])
            return {
                "predicted_category": semantic_result["predicted_category"],
                "confidence": round(max(0.0, min(confidence, 1.0)), 2),
                "is_confident": confidence >= settings.ML_CONFIDENCE_THRESHOLD,
                "method": "semantic_sentence_transformer",
            }
        except Exception as e:
            logger.warning(f"Semantic prediction failed; using keyword rules: {e}")

    # Fallback if model fails or unavailable
    return rule_based_predict(description)
