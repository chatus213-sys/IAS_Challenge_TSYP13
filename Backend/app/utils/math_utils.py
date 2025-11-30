def avg(values):
    if not values:
        return None
    return sum(values) / len(values)


def clamp(v, low, high):
    return max(low, min(high, v))


def safe_div(a, b):
    return a / b if b != 0 else 0
