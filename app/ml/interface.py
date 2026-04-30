"""
Clean ML interface. Real models should be loaded from app/ml/artifacts/ and
implement the same predict() signature.
"""
from dataclasses import dataclass, field
from pathlib import Path
import pickle
import random

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"


@dataclass
class PredictionResult:
    value: float
    confidence: float
    lower_bound: float
    upper_bound: float
    model_name: str
    metadata: dict = field(default_factory=dict)


def _load_model(name: str):
    """Load a pickled model from artifacts/. Returns None if not found."""
    path = ARTIFACTS_DIR / f"{name}.pkl"
    if path.exists():
        with open(path, "rb") as f:
            return pickle.load(f)
    return None


def predict(input: dict) -> PredictionResult:
    """
    Entry point for all model inference.

    input keys:
      - model  (str): which model to run. Falls back to 'stub' if not found.
      - domain (str): 'sports' | 'business'
      - subject (str): human-readable description
      - features (dict): model-specific feature dict
    """
    model_name = input.get("model", "stub")
    model = _load_model(model_name)

    if model is not None:
        raw = model.predict([list(input["features"].values())])[0]
        value = float(raw)
        confidence = float(input.get("confidence_override", 0.75))
        spread = value * 0.08
        return PredictionResult(
            value=value,
            confidence=confidence,
            lower_bound=round(value - spread, 4),
            upper_bound=round(value + spread, 4),
            model_name=model_name,
        )

    return _stub_predict(input)


def _stub_predict(input: dict) -> PredictionResult:
    """Realistic-looking dummy output for UI development."""
    domain = input.get("domain", "sports")
    rng = random.Random(str(input.get("subject", "")))

    if domain == "sports":
        value = rng.uniform(85, 130)
        confidence = rng.uniform(0.55, 0.82)
    else:
        value = rng.uniform(-0.15, 0.25)
        confidence = rng.uniform(0.60, 0.88)

    spread = abs(value) * 0.07
    return PredictionResult(
        value=round(value, 4),
        confidence=round(confidence, 4),
        lower_bound=round(value - spread, 4),
        upper_bound=round(value + spread, 4),
        model_name="stub-v0.1",
        metadata={"note": "Placeholder — wire a real model artifact to replace this."},
    )
