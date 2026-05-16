def risk_level(score: float) -> str:
    if score < 30:
        return "Low"
    if score < 55:
        return "Moderate"
    if score < 75:
        return "High"
    return "Extreme"


YOUNG_SCHOOL_TYPES = frozenset({"Kindergarten", "Primary School"})


def calculate_risk_score(
    max_temp: float,
    humidity: int,
    apparent_temp: float | None,
    us_aqi: float | None,
    school_type: str,
    outdoor_activity: bool,
    insufficient_shade: bool,
    insufficient_water: bool,
) -> float:
    """HeatSafe Campus MVP additive risk score (0–100). Uses daily max weather metrics."""
    score = 0.0
    if max_temp >= 35:
        score += 20
    if max_temp >= 38:
        score += 35
    if humidity >= 65:
        score += 15
    if apparent_temp is not None and apparent_temp >= 40:
        score += 25
    if us_aqi is not None and us_aqi >= 100:
        score += 10
    if outdoor_activity:
        score += 15
    if school_type in YOUNG_SCHOOL_TYPES:
        score += 10
    if insufficient_shade:
        score += 10
    if insufficient_water:
        score += 10
    return round(min(100, score), 1)
