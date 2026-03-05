def predict_conversion_probability(score: float) -> float:
    """Clamp score into a pseudo probability range [0, 1]."""
    return max(0.0, min(1.0, score / 100.0))
