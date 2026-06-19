THRESHOLD_LOW    = 30   # [x < 30 seamless access], [30 < x < 60 SMS verification], [60 < x : Biometric + 2FA]
THRESHOLD_MEDIUM = 60

def score_to_level(score: int) -> str:
    if score < THRESHOLD_LOW:
        return "low"
    elif score <= THRESHOLD_MEDIUM:
        return "medium"
    return "high"

def level_to_verification(level: str) -> list[str]:
    return {
        "low":    [],
        "medium": ["sms"],
        "high":   ["biometric", "2fa"],
    }.get(level, [])