def detect_pain_points(text: str) -> list[str]:
    """Very small placeholder rule-based detector."""
    keywords = ["slow", "expensive", "manual", "delay"]
    text_lower = text.lower()
    return [word for word in keywords if word in text_lower]
