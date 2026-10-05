import hashlib
import pandas as pd
import joblib
import os
from app.core.config import settings
from app.core.logging_config import security_logger

BREED_PRIOR_YIELD_L = {
    "ankole": 2.5,
    "ankole_friesian_cross": 7.0,
    "holstein_friesian": 13.0,
    "other": 7.5,
}
FEATURE_COLUMNS = ["breed", "feed", "milking_times", "recent_avg_yield"]


def _sha256_of_file(path: str) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


class MLService:
    """
    Wraps the trained sklearn pipeline. Falls back to a breed-calibrated
    heuristic if the model file isn't present OR fails an integrity check,
    so the app never blindly trusts a file that may have been tampered
    with (joblib/pickle files can execute arbitrary code on load if
    replaced maliciously -- this check is a real defense, not a formality).
    """

    def __init__(self, model_path: str | None = None):
        self.model_path = model_path or settings.ml_model_path
        self.model = self._load_model()

    def _load_model(self):
        if not os.path.exists(self.model_path):
            return None

        expected_hash = settings.ml_model_sha256
        if expected_hash:
            actual_hash = _sha256_of_file(self.model_path)
            if actual_hash != expected_hash:
                security_logger.warning(
                    f"ML model integrity check FAILED for {self.model_path}. "
                    f"Expected {expected_hash}, got {actual_hash}. "
                    f"Refusing to load -- falling back to heuristic."
                )
                return None
        else:
            security_logger.info(
                "ML_MODEL_SHA256 not set -- model integrity check skipped. "
                "Set this in .env to enable it."
            )

        return joblib.load(self.model_path)

    @property
    def is_loaded(self) -> bool:
        return self.model is not None

    def predict_expected_yield(self, feed, milking_times, breed, recent_avg_yield=None):
        breed_key = breed if breed in BREED_PRIOR_YIELD_L else "other"
        effective_recent_avg = recent_avg_yield if recent_avg_yield is not None else BREED_PRIOR_YIELD_L[breed_key]

        if self.model is not None:
            row = pd.DataFrame([{
                "breed": breed_key, "feed": feed, "milking_times": milking_times,
                "recent_avg_yield": effective_recent_avg,
            }])[FEATURE_COLUMNS]
            return round(float(self.model.predict(row)[0]), 1)

        return round(effective_recent_avg, 1)


ml_service = MLService()