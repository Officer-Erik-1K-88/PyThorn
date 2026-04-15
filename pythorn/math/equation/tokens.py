from __future__ import annotations

from decimal import Decimal
from typing import Generic, TypeVar

T = TypeVar("T")


class EquationPiece(Generic[T]):
    """Wrap a typed token value used by the equation parser."""

    def __init__(self, value: T):
        self._value = value

    @property
    def value(self) -> T:
        """Return the wrapped token value."""
        return self._value


class Variable(EquationPiece[str]):
    """Represent a variable token referenced inside an equation string."""

    def __init__(self, name: str):
        super().__init__(name)


class Number(EquationPiece[Decimal]):
    """Represent a decimal literal parsed from an equation."""

    def __init__(self, number: Decimal):
        super().__init__(number)
