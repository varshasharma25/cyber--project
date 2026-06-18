import random

def calculate_risk(user_id: int, behavior: dict) -> int:

    score = 0
    factors = 0

    if "new_device" in behavior:
        factors += 1
        score += 70 if behavior["new_device"] else 10

    if "typing_speed" in behavior:
        factors += 1
        speed = behavior["typing_speed"]
        score += 60 if (speed < 100 or speed > 600) else 15

    if "transaction_amount" in behavior:
        factors += 1
        amount = behavior["transaction_amount"]
        score += 80 if amount > 50000 else (40 if amount > 10000 else 10)

    if "login_hour" in behavior:
        factors += 1
        hour = behavior["login_hour"]
        score += 50 if (hour < 5 or hour > 23) else 10

    if factors == 0:
        return random.randint(10, 90)

    return min(100, round(score / factors))