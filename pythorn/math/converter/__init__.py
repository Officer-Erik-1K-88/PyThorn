"""
pythorn.math.converter

One-to-one Python port of the Java `cache` utility.

This module intentionally preserves Java behavior, including:
- Naming quirks
- Edge cases
- Large-number Latin prefix rules
- Fraction handling semantics

This module intentionally preserves the Java behavior so outputs and parsing
round-trip the same way.

Notable behaviors preserved from Java:
- Fractions are expressed using "and" + an ordinal place name
  (e.g., 0.25 -> "Zero and Twenty Five Hundredth").
- Large-number names are generated using the same Latin-prefix construction.
- `convert_partial_word()` returns a numeric string followed by a scale word,
  matching Java's formatting logic.

Public API (mirrors Java, with snake_case aliases):
- find_number_name(exponent: int) -> str
- find_number_name_from_value(number: Decimal) -> Pair[str, Decimal]
- convert_to_words(number: Any) -> str
- convert_partial_word(number: Any, places_before_word: int = 0, round_to: int = 2**31-1) -> str
- convert_to_number(number_words: str) -> Decimal
- convert_to_big(number: Any) -> Decimal
"""

__all__ = [
    "find_number_name",
    "find_number_name_from_value",
    "convert_to_words",
    "convert_partial_word",
    "convert_to_number",
    "convert_to_big",
]

from ._num_name import find_number_name_from_value, find_number_name

from ._to_number import convert_to_number, convert_to_big

from ._to_words import convert_to_words, convert_partial_word
