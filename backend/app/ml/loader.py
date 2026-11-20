from pathlib import Path
import json
from hashlib import sha256
import joblib
from app.core.logging import logger
from app.core.config import settings

_model = None

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def _model_search_paths():
    configured_path = Path(settings.ML_MODEL_PATH).expanduser()
    return [
        configured_path if configured_path.is_absolute() else Path.cwd() / configured_path,
        REPOSITORY_ROOT / configured_path,
        REPOSITORY_ROOT / "ml" / "models" / "campusfix_category_model.joblib",
        Path("/app/ml/models/campusfix_category_model.joblib"),
    ]


def load_model():
    global _model
    if _model is not None:
        return _model

    for path in dict.fromkeys(_model_search_paths()):
        if path.exists():
            try:
                artifact_path = path
                if path.suffix.lower() == ".json":
                    manifest = json.loads(path.read_text(encoding="utf-8"))
                    artifact_name = manifest.get("artifact")
                    if not artifact_name or Path(artifact_name).name != artifact_name:
                        raise ValueError("Invalid model artifact name in active manifest")
                    artifact_path = path.parent / artifact_name
                    if not artifact_path.is_file():
                        raise FileNotFoundError(f"Active model artifact is missing: {artifact_path}")
                    expected_hash = manifest.get("sha256")
                    if expected_hash and sha256(artifact_path.read_bytes()).hexdigest() != expected_hash:
                        raise ValueError("Active model artifact hash does not match the manifest")
                _model = joblib.load(str(artifact_path))
                logger.info(f"Loaded ML model successfully from {artifact_path}")
                return _model
            except Exception as e:
                logger.warning(f"Failed loading model from {path}: {e}")

    logger.warning("No serialized ML model artifact found. Prediction fallback will be active.")
    return None
