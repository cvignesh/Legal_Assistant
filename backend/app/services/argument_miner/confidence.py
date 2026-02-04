import logging

logger = logging.getLogger(__name__)


def compute_confidence(pros: list, defs: list) -> int:
    """
    Compute confidence score based on:
    1. Total argument count (more args = more evidence)
    2. Balance between prosecution and defense (roughly equal = more contestable)
    3. Argument strength (length as proxy for detail)
    
    Returns:
        Confidence score 0-100
    """
    if not pros and not defs:
        return 20  # Very low confidence if no arguments at all
    
    total_args = len(pros) + len(defs)
    
    # Base score from argument count (more args = more confident)
    # 0-2 args: 30, 3-4 args: 50, 5-6 args: 65, 7+ args: 75
    if total_args >= 7:
        base_score = 75
    elif total_args >= 5:
        base_score = 65
    elif total_args >= 3:
        base_score = 50
    else:
        base_score = 30
    
    # Balance bonus: if sides are roughly equal, it's more contested/confident
    # If highly skewed, confidence is lower
    if len(pros) == 0 or len(defs) == 0:
        balance_penalty = 15  # One side has no args
    else:
        ratio = max(len(pros), len(defs)) / min(len(pros), len(defs))
        if ratio <= 1.5:  # Well-balanced (e.g., 3 vs 2 or 5 vs 4)
            balance_bonus = 10
        elif ratio <= 2.5:  # Moderately imbalanced
            balance_bonus = 0
        else:  # Highly imbalanced
            balance_bonus = -10
    
    # Argument length bonus: longer arguments = more detail
    avg_pro_len = sum(len(arg) for arg in pros) / len(pros) if pros else 0
    avg_def_len = sum(len(arg) for arg in defs) / len(defs) if defs else 0
    avg_len = (avg_pro_len + avg_def_len) / 2 if (pros or defs) else 0
    
    # If arguments are >100 chars on average, add bonus
    length_bonus = 5 if avg_len > 100 else 0
    
    confidence = max(20, min(90, base_score + balance_bonus + length_bonus))
    
    logger.info(
        f"Confidence calculation: base={base_score}, balance={balance_bonus}, "
        f"length={length_bonus}, total_args={total_args}, avg_len={avg_len:.1f} → {confidence}%"
    )
    
    return int(confidence)
