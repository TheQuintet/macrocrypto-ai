"""Correlation insight generation.

Turns a correlation coefficient and its derived labels into a short,
human-readable sentence. Pure function — no I/O, no LLM, no external
calls. Deterministic: the same inputs always produce the same output.

The sentence follows a fixed template:

    "When <indicator> rises, BTC typically <rises|falls>
     (<strength> <direction> correlation, <confidence>% confidence)."

The direction of the sentence ("rises" vs "falls") is chosen by the
`direction` label, not by the raw coefficient, so it stays
consistent with the schema's `direction` field. The confidence
clause is dropped when `p_value` is None.

Examples:
    >>> generate_insight("inflation", -0.42, "medium", "negative", 0.03)
    'When inflation rises, BTC typically falls (medium negative correlation, 97% confidence).'
    >>> generate_insight("rates", 0.85, "strong", "positive", 0.001)
    'When rates rises, BTC typically rises (strong positive correlation, 99.9% confidence).'
    >>> generate_insight("gdp", 0.15, "weak", "positive", None)
    'When gdp rises, BTC typically rises (weak positive correlation).'

Design:
    - The function takes the same inputs the API already has on each
      CorrelationEntry. It does no additional computation beyond
      formatting; the derived labels (strength, direction,
      confidence) are computed by the caller via the existing
      helpers in app.correlation.calculator.
    - Sentence fragments are built from fixed vocabulary. There are
      no external templates and no localization in this branch.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ============================================================
# HELPERS
# ============================================================
def _direction_verb(direction: str) -> str:
    """Return the BTC verb for the given direction label.

    Args:
        direction: 'positive' or 'negative'.

    Returns:
        'rises' for positive, 'falls' for negative.

    Raises:
        ValueError: If direction is not a recognized label.
    """
    if direction == "positive":
        return "rises"
    if direction == "negative":
        return "falls"

    raise ValueError(
        f"Unknown direction label '{direction}'. "
        f"Expected one of 'positive', 'negative'."
    )


def _format_confidence(confidence_level: Optional[float]) -> Optional[str]:
    """Format a confidence level as a compact percentage string.

    Rules:
        - None → None
        - Integer values drop the decimal (e.g. 99.0 → "99")
        - Non-integer values keep one decimal (e.g. 97.34 → "97.3")

    Args:
        confidence_level: Confidence level as a percentage, or None.

    Returns:
        Formatted string, or None when input is None.
    """
    if confidence_level is None:
        return None

    # Integer value → no decimals
    if float(confidence_level).is_integer():
        return str(int(confidence_level))

    # Otherwise one decimal place
    return f"{confidence_level:.1f}"


# ============================================================
# PUBLIC FUNCTION
# ============================================================
def generate_insight(
    indicator_name: str,
    coefficient: float,
    strength: str,
    direction: str,
    p_value: Optional[float],
) -> str:
    """Generate a short human-readable insight sentence.

    The sentence is built from the derived labels the caller
    already has:

        "When <indicator> rises, BTC typically <rises|falls>
         (<strength> <direction> correlation[, <confidence>%
         confidence])."

    The confidence clause is omitted when p_value is None.

    The `coefficient` argument is accepted for future extensions
    (e.g. embedding the raw value in the sentence) but is not
    currently used in the output. It is required so the signature
    stays stable when that changes.

    Args:
        indicator_name: Product-facing indicator label (e.g.
            'inflation').
        coefficient: The Pearson correlation coefficient. Unused
            today, reserved for future sentence variants.
        strength: Derived strength label ('strong', 'medium', or
            'weak').
        direction: Derived direction label ('positive' or
            'negative').
        p_value: Two-tailed p-value in [0, 1], or None when the
            correlation was undefined.

    Returns:
        A short insight sentence.

    Raises:
        ValueError: If direction is not 'positive' or 'negative'.
    """
    verb = _direction_verb(direction)

    # Compute the confidence string. This mirrors the rule used by
    # `confidence_from_p_value` in app.correlation.calculator:
    # confidence = (1 - p_value) * 100.
    confidence_str: Optional[str] = None
    if p_value is not None:
        confidence = (1.0 - p_value) * 100.0
        confidence_str = _format_confidence(confidence)

    # Base sentence without the confidence clause
    base = (
        f"When {indicator_name} rises, "
        f"BTC typically {verb} "
        f"({strength} {direction} correlation"
    )

    if confidence_str is not None:
        sentence = f"{base}, {confidence_str}% confidence)."
    else:
        sentence = f"{base})."

    logger.debug(
        f"Generated insight for {indicator_name}: {sentence}"
    )

    return sentence


# ============================================================
# DUNDER
# ============================================================
__all__ = ["generate_insight"]