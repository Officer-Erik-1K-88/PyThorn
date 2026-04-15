from __future__ import annotations

from decimal import Context

from pythorn.collections.char import CharSequence

from .parser import _EvalParser


class Equation:
    """Parse an equation string into a reusable tokenized representation."""

    def __init__(self, equation: str, context: Context):
        self._equation = equation
        self._context = context
        parser = _EvalParser(CharSequence(equation), context)
        parser.parse()
        self._parsed_equation = parser.parsed

    @property
    def equation(self):
        """Return the original equation string."""
        return self._equation

    @property
    def context(self):
        """Return the decimal context associated with this equation."""
        return self._context

    def has_variables(self):
        """Return whether the original equation string references variables."""
        return "$" in self._equation
