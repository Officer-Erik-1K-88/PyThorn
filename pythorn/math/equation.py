from abc import abstractmethod, ABC
from decimal import Decimal, Context
from typing import Callable, MutableSequence, overload, Iterable, Sequence, Mapping

from pythorn.collections.char import CharIterator, CharSequence

class Param(ABC):
    @property
    @abstractmethod
    def name(self):
        """The name of the parameter"""
        pass

    @property
    @abstractmethod
    def takes_boolean(self):
        pass

    @property
    @abstractmethod
    def default(self):
        """The default value that is returned if there is no value"""
        pass

    @property
    @abstractmethod
    def value(self):
        """The value of the parameter"""
        pass

    @property
    @abstractmethod
    def required(self):
        """Whether the parameter is required"""
        pass

    @property
    def position_dependent(self):
        """Whether the parameter is position dependent, meaning it has no name"""
        return self.name == ""

    def get(self):
        """Get the value of the parameter"""
        if self.value is None:
            return self.default
        return self.value

    def is_empty(self):
        """Whether the parameter is empty"""
        return self.get() is None

    def new(self, value):
        """Create a new parameter with the given value"""
        return Parameter(
            self.name,
            self.takes_boolean,
            self.default,
            value,
            self.required,
        )


class Parameter(Param):
    def __init__(self, name: str, takes_boolean: bool = False, default=None, value=None, required=False):
        self._name = name
        self._takes_boolean = takes_boolean
        self._default = default
        self._value = value
        self._required = required

    @property
    def name(self):
        """The name of the parameter"""
        return self._name

    @property
    def takes_boolean(self):
        return self._takes_boolean

    @property
    def default(self):
        """The default value that is returned if there is no value"""
        return self._default

    @property
    def value(self):
        """The value of the parameter"""
        return self._value

    @property
    def required(self):
        """Whether the parameter is required"""
        return self._required


class Parameters(Sequence[Param]):
    def __init__(self, parameters: tuple[Param, ...] | None=None):
        self._parameters = tuple() if parameters is None else parameters
        self._param_names: dict[str, int] = {}
        i = 0
        for parameter in self._parameters:
            if not parameter.position_dependent:
                self._param_names[parameter.name] = i
            i += 1

    def check(self, parameters: Parameters):
        """
        Check if the given parameters has all required parameters filled.

        The given `Parameters` must have the same number of parameters as this `Parameters` instance.
        """
        if len(parameters) != len(self):
            return False
        i = 0
        for parameter in self._parameters:
            if parameter.position_dependent:
                if parameter.required:
                    if parameters[i].is_empty():
                        return False
            else:
                if parameter.required:
                    if parameters[i].is_empty():
                        return False
            i += 1
        return True

    def fill(self, parameters: Parameters):
        """
        Create a new `Parameters` with the same parameters as this
        instance and the given `Parameters` instance.

        Any parameters in the given `Parameters` instance that is
        not in this instance will not be added to the new `Parameters`.

        Only the values of the given `Parameters` instance will be
        filled in the new `Parameters`.
        """
        new_list = list(self._parameters)

        i = 0
        for parameter in parameters:
            if parameter.position_dependent:
                if i < len(new_list):
                    new_list[i] = new_list[i].new(parameter.value)
            else:
                if parameter.name in self:
                    index = self._param_names[parameter.name]
                    new_list[index] = new_list[index].new(parameter.value)
            i += 1
        return Parameters(tuple(new_list))

    def required_filled(self):
        """
        Check if this `Parameters` instance has all required parameters
        filled.
        :return:
        """
        for parameter in self._parameters:
            if parameter.required:
                if parameter.is_empty():
                    return False
        return True

    def get_named_parameter(self, name: str) -> Param:
        """Get the parameter with the given name"""
        if name in self._param_names:
            return self._parameters[self._param_names[name]]
        raise KeyError(f"Parameter `{name}` not found")

    def __getitem__(self, item) -> Param:
        return self._parameters[item]

    def __len__(self):
        return len(self._parameters)

    def __iter__(self):
        for parameter in self._parameters:
            yield parameter

    def __contains__(self, item):
        if isinstance(item, str):
            return item in self._param_names
        return item in self._parameters

    def __add__(self, other):
        if isinstance(other, Parameters):
            return Parameters(self._parameters + other._parameters)
        elif isinstance(other, tuple):
            return Parameters(self._parameters + other)
        elif isinstance(other, Iterable):
            return Parameters(self._parameters + tuple(other))
        return Parameters(self._parameters + (other,))

    def __radd__(self, other):
        if isinstance(other, Parameters):
            return Parameters(other._parameters + self._parameters)
        elif isinstance(other, tuple):
            return Parameters(other + self._parameters)
        elif isinstance(other, Iterable):
            return Parameters(tuple(other) + self._parameters)
        return Parameters((other,) + self._parameters)


class Function:
    def __init__(
            self,
            name: str,
            value: Decimal | None = None,
            parameters: Parameters | None = None,
            action: Callable[[Parameters], Decimal] | None = None,
    ):
        if action is None and value is None:
            raise TypeError("One of `action` or `value` must be specified")
        if action is not None:
            if parameters is None or len(parameters) == 0:
                raise TypeError("`parameters` must be specified when `action` is specified")
        self._name = name
        self._value = value
        self._parameters = parameters
        self._action = action

    @property
    def name(self):
        return self._name

    @property
    def parameters(self):
        return self._parameters

    def is_value(self):
        return self._value is not None

    def __call__(self, parameters: Parameters) -> Decimal:
        if parameters is None:
            raise TypeError("`parameters` must be specified")
        new_parameters = self._parameters.fill(parameters)
        if not new_parameters.required_filled():
            raise TypeError("all required `parameters` must be filled")
        return self._action(new_parameters)

    def apply(self, param_handler: Callable[[Parameters], Parameters] | None = None) -> Decimal:
        if self._action is None:
            return self._value

        if param_handler is None:
            raise TypeError("`param_handler` must be specified when `action` is specified")
        return self._action(param_handler(self._parameters))


class Functions:
    def __init__(self, functions: tuple[Function, ...]):
        self._functions = functions
        self._func_names: dict[str, int] = {}
        i = 0
        for func in functions:
            self._func_names[func.name] = i
            i += 1

    def get(self, name: str) -> Function:
        """Get the function with the given name"""
        if name in self._func_names:
            return self._functions[self.index(name)]
        raise KeyError(f"Parameter `{name}` not found")

    def index(self, name: str) -> int:
        """Get the index of the given name"""
        return self._func_names[name]

    def names(self):
        return self._func_names.keys()

    def __getitem__(self, item):
        return self._functions[item]

    def __len__(self):
        return len(self._functions)

    def __iter__(self):
        return iter(self._functions)

    def __contains__(self, item):
        return item in self._func_names

FUNCTIONS = Functions(())


class EquationPiece[T]:
    def __init__(self, value: T):
        self._value = value

    @property
    def value(self) -> T:
        return self._value


class Variable(EquationPiece[str]):
    def __init__(self, name: str):
        super().__init__(name)


class Symbol[**P, R]:
    def __init__(
            self,
            symbol: str,
            name: str,
            *,
            param_count: int=0,
            after_loop:bool=False,
            action: Callable[P, R] | None = None
    ):
        self._symbol = symbol
        self._name = name
        self._param_count = param_count
        self._after_loop = after_loop
        self._action = action

    @property
    def symbol(self) -> str:
        return self._symbol

    @property
    def name(self) -> str:
        return self._name

    @property
    def param_count(self) -> int:
        return self._param_count

    @property
    def after_loop(self) -> bool:
        return self._after_loop

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R:
        if self._action is None:
            return None
        return self._action(*args, **kwargs)

    def compare(self, other):
        if self is other:
            return 0
        other_symbol = None
        this_symbol = self._symbol
        if isinstance(other, Symbol):
            other_symbol = other._symbol
        else:
            other_symbol = other
            if isinstance(other, (int, float)):
                this_symbol =  ord(self._symbol)

        if this_symbol == other_symbol:
            return 0
        elif this_symbol < other_symbol:
            return -1
        elif this_symbol > other_symbol:
            return 1
        raise RuntimeError(f"Failed to compare `{this_symbol}` to `{other_symbol}`")

    def __eq__(self, other):
        return self.compare(other) == 0
    def __ne__(self, other):
        return self.compare(other) != 0
    def __lt__(self, other):
        return self.compare(other) < 0
    def __le__(self, other):
        return self.compare(other) <= 0
    def __gt__(self, other):
        return self.compare(other) > 0
    def __ge__(self, other):
        return self.compare(other) >= 0

    def __str__(self):
        return self.symbol


class Symbols(Mapping[str, Symbol]):
    def __init__(self, symbols: Iterable[Symbol]):
        self._symbol_list: list[str] = []
        self._param_counts: dict[int, list[str]] = {}
        self._symbols: dict[str, Symbol] = {}
        for symbol in symbols:
            sym = symbol.symbol
            self._symbols[sym] = symbol
            self._symbol_list.append(sym)
            self._param_counts.setdefault(symbol.param_count, []).append(sym)

    def index(self, value: str | Symbol, start: int = 0, stop=None) -> int:
        value = str(value)
        return self._symbol_list.index(value, start, stop)

    def at(self, index: int) -> Symbol:
        return self._symbols[self._symbol_list[index]]

    def contains_any(self, values: Iterable[object]):
        for value in values:
            if value in self._symbols:
                return True
        return False

    def __getitem__(self, key, /):
        return self._symbols[key]

    def __len__(self):
        return len(self._symbol_list)

    def iter(self, param_count: int | None = None, after_loop: bool = True, during_loop: bool = True):
        loop_list = self._symbol_list if param_count is None else self._param_counts.get(param_count, [])
        for symbol in loop_list:
            sym = self[symbol]
            if sym.after_loop and not after_loop:
                continue
            elif not sym.after_loop and not during_loop:
                continue
            yield symbol

    def __iter__(self):
        for symbol in self._symbol_list:
            yield symbol

    def __contains__(self, key):
        return str(key) in self._symbols


MATH_SYMBOLS = Symbols([
    Symbol("^", "exponentiation", param_count=2, action = lambda a, b: a ** b),
    Symbol("*", "times", param_count=2, action = lambda a, b: a * b),
    Symbol("/", "divide", param_count=2, action = lambda a, b: a / b),
    Symbol("%", "modulus", param_count=2, action = lambda a, b: a % b),
    Symbol("+", "plus", param_count=2, action = lambda a, b: a + b),
    Symbol("-", "minus", param_count=2, action = lambda a, b: a - b),
])

COMPARISON_SYMBOLS = Symbols([
    Symbol("=", "equal", param_count=2, action = lambda a, b: a == b),
    Symbol("<", "less", param_count=2, action = lambda a, b: a < b),
    Symbol(">", "greater", param_count=2, action = lambda a, b: a > b),
    Symbol("<=", "lessOrEqual", param_count=2, action = lambda a, b: a <= b),
    Symbol(">=", "greaterOrEqual", param_count=2, action = lambda a, b: a >= b),
    Symbol("!=", "notEqual", param_count=2, action = lambda a, b: a != b),
])

UNION_SYMBOLS = Symbols([
    Symbol("&", "and", param_count=2, action = lambda a, b: a and b),
    Symbol("|", "or", param_count=2, action = lambda a, b: a or b),
    Symbol("~", "imp", param_count=2, action = lambda a, b: (not a) or b),
    Symbol("^", "ex", param_count=2, action = lambda a, b: a != b),
    Symbol("!", "not", param_count=1, after_loop=True, action = lambda a: not a),
])


class Operator(EquationPiece[str]):
    def __init__(self, operator: str):
        super().__init__(operator)

    def calculate(self, num1: Decimal, num2: Decimal) -> Decimal:
        if self.value in MATH_SYMBOLS:
            return MATH_SYMBOLS[self.value](num1, num2)
        raise ParseError("`operator` isn't a mathematical operator")

    def compare(self, num1: Decimal, num2: Decimal) -> bool:
        if self.value in COMPARISON_SYMBOLS:
            return COMPARISON_SYMBOLS[self.value](num1, num2)
        raise ParseError("`operator` isn't a comparison operator")

    def union(self, *args: bool) -> bool:
        """
        Reduce one or more boolean operands using a flag-driven composite logic operator.

        This method performs a left-to-right fold over the given boolean arguments.
        The behavior is determined by which operator flags are present in ``self.value``.
        Multiple flags may be active at the same time; when they are, they are applied
        in a fixed sequence of logical stages for every reduction step.

        Enabled operator flags
        ----------------------
        The presence of the following characters in ``self.value`` enables the
        corresponding stage:

        ``"&"``  AND stage
            Combines the accumulator and the current value using logical AND.

        ``"|"``  OR stage
            If ``"|"`` is present, this stage performs logical OR.

        ``"~"``  IMPLICATION stage
            Applies material implication using the rule:
                ``A → B == (not A) or B``
            where ``A`` is the intermediate result from previous stages.

        ``"^"`` EXCLUSIVE stage
            Exclusive modifier.
            Preforms XOR.

        ``"!"``  NOT stage
            Negates the final result after all operands have been reduced.

        Evaluation order
        ----------------
        For each pairwise reduction step, the enabled stages are applied in
        the fixed order defined by ``UNION_SYMBOLS``.

        Common gate interpretations
        ---------------------------
        With this staged model, several standard logic gates emerge naturally:

        - ``"&"``     → AND
        - ``"|"``     → OR
        - ``"^"``    → XOR
        - ``"!&"``    → NAND
        - ``"!|"``    → NOR
        - ``"!^"``   → XNOR
        - ``"!"``     → NOT (final inversion)

        Other combinations form composite or non-standard gates whose behavior
        is fully defined by the staged evaluation rules above.

        Parameters
        ----------
        *args : bool
            One or more boolean values to be reduced.

        Returns
        -------
        bool
            The result of reducing all operands using the enabled operator flags.

        Raises
        ------
        ParseError
            - If no operands are provided.
            - If ``self.value`` contains none of the supported operator flags.
        """
        if len(args) == 0:
            raise ParseError("`args` can't be empty")
        last = None

        if not UNION_SYMBOLS.contains_any(self.value):
            raise ParseError("`operator` isn't an union operator")
        for current in args:
            if last is None:
                last = current
                if len(args) > 1:
                    continue
            future = last
            for symbol in UNION_SYMBOLS.iter(2, after_loop=False):
                if symbol in self.value:
                    future = UNION_SYMBOLS[symbol](future, current)
            last = future
        for symbol in UNION_SYMBOLS.iter(1, during_loop=False):
            if symbol in self.value:
                last = UNION_SYMBOLS[symbol](last)
        return last


class Number(EquationPiece[Decimal]):
    def __init__(self, number: Decimal):
        super().__init__(number)


class ChildError(RuntimeError):
    """ Exception raised when in a child process doesn't exist. """


class ParsedEquation(EquationPiece[list[EquationPiece]], MutableSequence[EquationPiece]):
    def __init__(self, parsed_equation: Iterable[EquationPiece]=None):
        super().__init__(list(parsed_equation))
        self._in_sub = False
        self._in_function = False

    @property
    def in_sub(self):
        return self._in_sub

    def enter_sub(self):
        self.get_current()._in_sub = True

    def exit_sub(self):
        try:
            self.get_current()._in_sub = False
        except ChildError:
            self._in_sub = False

    def get_sub(self, throw_on_not_found=False, throw_on_zero=False):
        if self._in_sub:
            if len(self._value) == 0:
                if throw_on_zero:
                    raise ChildError("The parent ParsedEquation is empty")
                self._value.append(ParsedEquation())
            last_val = self._value[len(self._value) - 1]
            if not isinstance(last_val, ParsedEquation):
                if throw_on_not_found:
                    raise ChildError(f"The last value `{last_val}` is not a ParsedEquation")
                last_val = ParsedEquation()
                self._value.append(last_val)
            if last_val.in_sub:
                return last_val.get_sub(throw_on_not_found, throw_on_zero)
            return last_val
        raise ChildError("Not in a child process")

    def get_current(self, sub_tonf=False, sub_toz=False) -> ParsedEquation:
        if self._in_sub:
            return self.get_sub(sub_tonf, sub_toz)
        if self._in_function:
            return self.get_function().get_param().get_current(sub_tonf, sub_toz)
        return self

    @property
    def in_function(self):
        return self._in_function

    def enter_function(self, name: str, index: int):
        current = self.get_current(sub_tonf=True, sub_toz=True)
        current._value.append(EquationFunc(index, name))
        current._in_function = True

    def exit_function(self):
        self.get_current(sub_tonf=True, sub_toz=True)._in_function = False

    def get_function(self):
        if self._in_function:
            if len(self._value) == 0:
                raise ChildError("The parent ParsedEquation is empty")
            last_val = self._value[len(self._value) - 1]
            if not isinstance(last_val, EquationFunc):
                raise ChildError(f"The last value `{last_val}` is not a EquationFunc")
            return last_val
        raise ChildError("Not in a child process")

    def index(self, value, start=0, stop=None):
        return self.get_current(True, True)._value.index(value, start, stop)

    def count(self, value):
        return self.get_current(True, True)._value.count(value)

    def insert(self, index: int, value: EquationPiece):
        self.get_current(True, True)._value.insert(index, value)

    def append(self, value: EquationPiece):
        self.get_current()._value.append(value)

    def extend(self, values: Iterable[EquationPiece]):
        current = self.get_current()
        if values is current:
            raise ValueError("Cannot extend because `values` is `current` ParsedEquation")
        for v in values:
            current._value.append(v)

    def reverse(self):
        """Not available on ParsedEquation"""
        raise NotImplementedError("`reverse` not implemented")

    def clear(self):
        current = self.get_current(True, True)
        current._value.clear()
        current._in_function = False
        current._in_sub = False

    def pop(self, index: int=-1):
        return self.get_current(True, True)._value.pop(index)

    def remove(self, value):
        return self.get_current(True, True)._value.remove(value)

    def __iadd__(self, values):
        self.extend(values)
        return self

    @overload
    def __getitem__(self, index: int) -> EquationPiece: ...
    @overload
    def __getitem__(self, index: slice) -> MutableSequence[EquationPiece]: ...
    def __getitem__(self, index):
        value = self.get_current(True, True)._value[index]
        if isinstance(value, EquationPiece):
            return value
        return ParsedEquation(value)

    @overload
    def __setitem__(self, index: int, value: EquationPiece) -> None: ...
    @overload
    def __setitem__(self, index: slice, value: Iterable[EquationPiece]) -> None: ...
    def __setitem__(self, index, value):
        self.get_current(True, True)._value[index] = value

    @overload
    def __delitem__(self, index: int) -> None: ...
    @overload
    def __delitem__(self, index: slice) -> None: ...
    def __delitem__(self, index):
        del self.get_current(True, True)._value[index]

    def __len__(self):
        try:
            return len(self.get_current(True, True)._value)
        except ChildError:
            return 0

    def __iter__(self):
        try:
            return iter(self.get_current(True, True)._value)
        except ChildError:
            return iter(())

    def __contains__(self, value):
        try:
            return self.get_current(True, True)._value.__contains__(value)
        except ChildError:
            return False

    def __reversed__(self):
        return self.get_current(True, True)._value.__reversed__()


class FuncParam(ParsedEquation, Param):
    def __init__(
            self,
            name: str,
            takes_boolean: bool,
            required: bool,
            default=None,
            value: Iterable[EquationPiece]=None,
    ):
        super().__init__(value)
        self._name = name
        self._takes_boolean = takes_boolean
        self._required = required
        self._default = default

    @property
    def name(self):
        return self._name

    @property
    def takes_boolean(self):
        return self._takes_boolean

    @property
    def required(self):
        return self._required

    @property
    def default(self):
        return self._default


class EquationFunc(EquationPiece[int]):
    def __init__(self, index: int, name: str):
        super().__init__(index)
        self._name = name
        self._parameters = Parameters()

    @property
    def name(self) -> str:
        return self._name

    @property
    def parameters(self) -> Parameters:
        return self._parameters

    def get(self) -> Function:
        return FUNCTIONS[self.value]

    def get_param(self) -> FuncParam:
        param = self._parameters[len(self._parameters) - 1]
        if isinstance(param, FuncParam):
            return param
        raise TypeError("EquationFunc's 'parameters' property isn't composed correctly")

    def add_param(self, param: FuncParam):
        self._parameters = self._parameters + param


class ParseError(RuntimeError):
    """ The generic Exception raised when parsing fails. """
    pass

class SyntaxParseError(ParseError):
    """ Exception raised when syntax is invalid when parsing. """
    pass


class _EvalParser(CharIterator):
    def __init__(self, chars: CharSequence, context: Context):
        super().__init__(chars, skip_space=True, skip_empty=True)
        self._context = context
        self._parsed = ParsedEquation()

    @property
    def context(self):
        return self._context

    @property
    def parsed(self):
        return self._parsed

    def parse(self):
        self._parse_expression()
        if not self.next_ended():
            raise ParseError("Ended too Early")

    def _parse_expression(self):
        self._parse_term()
        while True:
            if self.eat("+"): # Addition
                self._parsed.append(Operator("+"))
                self._parse_term()
            elif self.eat("-"): # Subtraction
                self._parsed.append(Operator("-"))
                self._parse_term()
            else:
                break

    def _parse_term(self):
        self._parse_factor()
        while True:
            if self.eat("*"):  # Multiplication
                self._parsed.append(Operator("*"))
                self._parse_factor()
            elif self.eat("/"):  # Division
                self._parsed.append(Operator("/"))
                self._parse_factor()
            else:
                break

    def _parse_factor(self):
        if self.eat("+"):
            self._parsed.append(Operator("+"))
            self._parse_factor()
            return
        elif self.eat("-"):
            self._parsed.append(Operator("-"))
            self._parse_factor()
            return


        if self.eat("("): # parentheses
            self._parsed.enter_sub()
            self._parse_expression()
            self._parsed.exit_sub()
            if not self.eat(")"):
                raise SyntaxParseError("Missing closing parenthesis: ')'")
        elif self.eat("$"):
            var_name = ""
            while not self.eat("$"):
                var_name += self.next()
                if self.next_ended():
                    raise SyntaxParseError("Missing variable closer: '$'")
            self._parsed.append(Variable(var_name))
        elif self._peek_num_check(): # number
            str_val = ""
            while self._peek_num_check():
                str_val += self.next()
            self._parsed.append(Number(Decimal(str_val, self.context)))
        elif self._peek_letter_check(): # function
            func = ""
            while self._peek_letter_check():
                func += self.next()
            if func in FUNCTIONS:
                self._parsed.enter_function(func, FUNCTIONS.index(func))
                func_val = FUNCTIONS.get(func)
                if func_val.is_value():
                    self._parse_parameters(func_val.parameters)
                self._parsed.exit_function()
            else:
                raise SyntaxParseError(f"Unknown symbol '{func}'")
        else:
            raise SyntaxParseError("Unexpected character: '%s'" % self.peek())

        # TODO: Add logic check to ensure parsing passed


    def _peek_num_check(self):
        return self.peek_check(lambda future: future >= "0" or future <= "9" or future == ".")

    def _peek_letter_check(self):
        return self.peek_check(lambda future: future >= "a" or future <= "z" or future >= "A" or  future <= "Z")

    def _parse_statement(self):
        if self.eat("!"):
            self._parsed.append(Operator("!"))
            self._parse_statement()
            return

        if self.eat("("):
            self._parsed.enter_sub()
            self._parse_union(True)
            self._parsed.exit_sub()
            if not self.eat(")"):
                raise SyntaxParseError("Missing closing parenthesis: `)`")
        else:
            self._parse_comparison()
            # TODO: Add logic check to ensure parsing passed and if more needs parsing

        if self._needs_union(): # if statement has more union symbols
            # TODO: Add logic check to see if statement is incomplete
            self._parse_union(False)

        # TODO: Add logic check to ensure parsing passed

    def _parse_union(self, inst_state: bool):
        if inst_state:
            self._parse_statement()
        while True:
            if self.eat("&"):
                self._parsed.append(Operator("&"))
                self._parse_statement()
            elif self.eat("|"):
                self._parsed.append(Operator("|"))
                self._parse_statement()
            else:
                break

    def _parse_comparison(self):
        self._parse_expression()
        # TODO: Add logic check to see if comparison is possible

        while True:
            if self.eat(">"):
                has_equal = self.eat("=")
                self._parsed.append(Operator(f">{'=' if has_equal else ''}"))
                self._parse_expression()
            elif self.eat("<"):
                has_equal = self.eat("=")
                self._parsed.append(Operator(f"<{'=' if has_equal else ''}"))
                self._parse_expression()
            elif self.eat("="):
                self.eat("=")
                self._parsed.append(Operator("="))
                self._parse_expression()
            elif self.eat("!"):
                if self.eat("="):
                    self._parsed.append(Operator("!="))
                    self._parse_expression()
                else:
                    raise SyntaxParseError("Missing '='")
            else:
                break
            # TODO: Add logic check to see if there is more to compare


    def _needs_union(self):
        return self.peek_check(lambda ch: ch == "&" or ch == "|")

    def _needs_compare(self):
        return self.peek_check(lambda ch: ch == ">" or ch == "<" or ch == "=" or ch == "!")

    def _parse_parameters(self, parameters: Parameters):
        if self.eat("("):
            end = False
            for parameter in parameters:
                self._parsed.get_function().add_param(
                    FuncParam(
                        parameter.name,
                        parameter.takes_boolean,
                        parameter.required,
                        parameter.default
                    )
                )
                if not end:
                    if parameter.takes_boolean:
                        self._parse_statement()
                    else:
                        self._parse_expression()
                    if self.eat(")"):
                        end = True
                else:
                    if parameter.required:
                        if parameter.is_empty():
                            raise ParseError(f"Parameter `{parameter.name}` is required")
            if not end:
                raise SyntaxParseError("Missing closing parenthesis: ')'")
        else:
            raise SyntaxParseError("Missing starting parenthesis: '('")


class Equation:
    def __init__(self, equation: str, context: Context):
        self._equation = equation
        self._context = context
        parser = _EvalParser(CharSequence(equation), context)
        parser.parse()
        self._parsed_equation = parser.parsed

    @property
    def equation(self):
        return self._equation

    @property
    def context(self):
        return self._context

    def has_variables(self):
        return "$" in self._equation
