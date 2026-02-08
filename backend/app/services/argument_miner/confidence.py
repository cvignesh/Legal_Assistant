import logging

logger = logging.getLogger(__name__)


def compute_confidence(prosecution_args, defense_args):

    p = len(prosecution_args or [])
    d = len(defense_args or [])

    # -----------------------------
    # Base Score
    # -----------------------------
    base_score = 40

    # -----------------------------
    # Initialize Bonuses SAFELY
    # -----------------------------
    balance_bonus = 0
    length_bonus = 0

    # -----------------------------
    # Balance Bonus
    # -----------------------------
    if p > 0 and d > 0:
        balance_bonus = 20
    elif p > 0 or d > 0:
        balance_bonus = 10

    # -----------------------------
    # Length Bonus
    # -----------------------------
    total = p + d

    if total >= 6:
        length_bonus = 20
    elif total >= 3:
        length_bonus = 10
    elif total > 0:
        length_bonus = 5

    # -----------------------------
    # Final Score
    # -----------------------------
    confidence = max(
        20,
        min(90, base_score + balance_bonus + length_bonus)
    )

    return confidence
