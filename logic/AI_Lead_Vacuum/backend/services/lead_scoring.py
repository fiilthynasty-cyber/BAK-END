def score_lead(features: dict[str, float]) -> float:
    """Compute a simple weighted score for a lead."""
    return round(sum(features.values()), 2)
