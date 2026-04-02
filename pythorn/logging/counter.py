import math
from typing import Optional, Iterable, Sequence

from pythorn.collections.views import SequenceView


__all__ = ["Counter", "Percent"]

from pythorn.logging.logger import Logger


class Counter:
    def __init__(self, name: str, visible: int=0, hidden: int=0, only_visible=True, *, step: float=1.0, logger: Optional[Logger] = None):
        if visible < 0:
            raise ValueError("The visible count must not be less than zero.")
        if hidden < 0:
            raise ValueError("The hidden count must not be less than zero.")
        if step < 0.0001:
            raise ValueError("The step must not be less than 0.0001.")
        self._name = name
        self._visible = visible
        self._hidden = hidden
        self._decimal: float = 0.0
        self.only_visible = only_visible
        self._step = step
        self._logger: Logger | None = logger
        self.allow_messages = True

    @property
    def name(self):
        return self._name

    @property
    def long_name(self):
        return self.name

    @property
    def visible(self):
        return self._visible

    @property
    def hidden(self):
        return self._hidden

    @property
    def decimal(self):
        return self._decimal

    @property
    def total(self):
        return self._visible + self._hidden

    @property
    def current(self) -> float:
        return (self._visible if self.only_visible else self.total) + self._decimal

    @current.setter
    def current(self, amount: float):
        if amount <= 0:
            self._visible = 0
            self._decimal = 0.0
        else:
            self._visible = math.floor(amount)
            decimal = amount - self._visible
            self._decimal = decimal
        if not self.only_visible:
            self._hidden = 0

    @property
    def step(self) -> float:
        """
        How much to add per tick.
        """
        return self._step

    def _msg_format(
            self,
            titles: Iterable[str],
            messages: Iterable[str],
            compact: bool,
            allow_lr: bool,
    ) -> str:
        title = ""
        message = ""
        add_msg = ""

        for t in titles:
            if title != "":
                title += f" | {t}"
            else:
                title = t

        for m in messages:
            add_m = m
            if add_m.endswith("\r"):
                add_m = add_m.removesuffix("\r")
                allow_lr = True
            if message != "":
                message = add_msg
            else:
                add_msg += f" (INFO: {add_m})"

        msg = message + add_msg

        if title != "":
            msg = f"[{title}] {msg}"

        msg = f"'{self.name if compact else self.long_name}' : {msg}"

        if allow_lr:
            if not msg.endswith("\r"):
                msg += "\r"

        return msg

    def build_message(self, compact: bool=False, allow_lr: bool=False) -> tuple[list[str], list[str], bool]:
        title: list[str] = []
        message: list[str] = [f"Count at {self.current}"]

        if not compact:
            message[0] = f"{message[0]} with {self.visible} visible and {self.hidden} hidden"
            if self.only_visible:
                message.append("Count only includes visible")

        return title, message, allow_lr

    def message_send(
            self,
            title: Optional[str | Iterable[str]] = None,
            message: Optional[str | Iterable[str]] = None,
            compact: bool = False,
            allow_lr: bool=False,
            include_default_msg: bool=False,
    ):
        """
        Sends a message to the logger that this Counter was instantiated with.

        This method does nothing when ``self.allow_messages`` is False or when no
        logger was defined at instantiation.

        If both ``title`` and ``message`` are not provided, the message will be
        created from ``self.build_message(compact, allow_lr)``.

        :param title: The title(s) of the message.
        :param message: The message(s) to send.
        :param compact: Whether to enforce a compact message.
        :param allow_lr: Whether the next item sent to the logger will replace this message.
        :param include_default_msg: Whether to include the message created by ``self.build_message`` regardless of title or message.
        :return:
        """
        if self.allow_messages and self._logger is not None:
            no_title = title is None or len(title) == 0
            no_message = message is None or len(message) == 0
            include_default_msg = include_default_msg or (no_title and no_message)
            if include_default_msg:
                built_msg = self.build_message(compact, allow_lr)
                if not no_title:
                    if isinstance(title, str):
                        built_msg[0].append(title)
                    else:
                        built_msg[0].extend(title)
                if not no_message:
                    if isinstance(message, str):
                        built_msg[1].append(message)
                    else:
                        built_msg[1].extend(message)
                title, message, allow_lr = built_msg
            msg = self._msg_format(title, message, compact, allow_lr)
            if msg.endswith("\r"):
                msg = msg.removesuffix("\r")
                allow_lr = True
            self._logger.log(self.__class__.__name__.upper(), msg, end="\r" if allow_lr else "\n")

    def add(self, amount: int, hidden=False):
        """
        Adds `amount` to the counter.

        :param amount: The amount to add.
        :param hidden: Whether to apply the tick to the hidden count (True) or visible count (False).
        :return:
        """
        if amount != 0:
            amount = abs(amount)
            if hidden:
                self._hidden += amount
            else:
                self._visible += amount
            self.message_send()

    def float_add(self, amount: float, hidden=False):
        """
        Adds `amount` to the counter.

        This is the same as ``self.add``, except that the value added to
        ``self.visible`` or ``self.hidden`` is the floor of ``amount``.
        The rest of ``amount`` is added to ``self.decimal``, given that
        ``self.only_visible`` or ``hidden`` is ``False``.

        :param amount: The amount to add.
        :param hidden: Whether to apply the tick to the hidden count (True) or visible count (False).
        :return:
        """
        if amount != 0:
            amount = abs(amount)
            amt = math.floor(amount)
            decimal = amount - amt
            if hidden:
                self._hidden += amt
            else:
                self._visible += amt
            if (not self.only_visible) or (not hidden):
                self._decimal += decimal
            self.message_send()

    def tick_worth(self, tick_count: int, worth: float, linear: bool) -> float:
        """
        Gets the tick worth of a tick given a tick count and a worth.

        A tick worth defines how much to multiply ``self.step`` by
        to get the amount to add to the counter.

        When a tick is linear, then the worth of that tick is
        defined as ``worth * tick_count``.
        While when it is a non-linear tick, then the
        worth of that tick is defined as ``worth / tick_count``.

        :param tick_count: The number of ticks.
        :param worth: The worth of the tick count.
        :param linear: Whether the tick is linear (True) or not (False).
        :return: the worth of the tick.
        """
        return worth * tick_count if linear else worth / tick_count

    def tick(self, tick_count: int=1, worth: float=1.0, linear=True, hidden=False):
        """
        Moves the counter by the specified number of ticks.

        The amount a tick will add to the counter is defined as
        ``self.step * self.tick_worth(tick_count,worth,linear)``.

        When ``linear`` is False, the tick generated will only be the
        smallest portion of a non-linear tick.
        Use ``non_linear_tick`` when needing the full non-linear tick.

        :param tick_count: The number of ticks.
        :param worth: The worth of the tick count.
        :param linear: Weather or not the tick is linear (Default: False)
        :param hidden: Whether to apply the tick to the hidden count (True) or visible count (False).
        :return:
        """
        if tick_count < 1:
            tick_count = 1
        tick_worth = self.tick_worth(tick_count, worth, linear)
        to_add = self.step * tick_worth
        self.float_add(to_add, hidden)

    def non_linear_tick(self, tick_count: int=1, worth: float=1.0, hidden=False):
        """
        Moves the counter by the specified number of ticks.

        Unlike ``tick``, ``non_linear_tick`` handles non-linear ticks in a
        trustworthy way.

        The logic of a non-linear tick is defined as ``self.step * tick_worth``
        where each number in a loop that starts at `1` and ends at ``tick_count``
        adds ``self.tick_worth(number_item,worth,False)`` to ``tick_worth``.

        :param tick_count: The number of ticks.
        :param worth: The worth of the tick count.
        :param hidden: Whether to apply the tick to the hidden count (True) or visible count (False).
        :return:
        """
        if tick_count < 1:
            tick_count = 1
        tick_worth = 0.0
        for count in range(1, tick_count+1):
            tick_worth += self.tick_worth(count, worth, False)
        to_add = self.step * tick_worth
        self.float_add(to_add, hidden)

    def reset(self):
        self._visible = 0
        self._hidden = 0

    def __str__(self):
        return str(self.__int__())

    def __int__(self):
        return self.current

    def __float__(self):
        return float(self.__int__())

    def __bool__(self):
        """ True if ``self.current`` is greater than zero else False """
        return self.current > 0

    def compare(self, other):
        num_to_check = 0
        if isinstance(other, Counter):
            num_to_check = other.current
        elif isinstance(other, (int, float)):
            num_to_check = other
        elif hasattr(other, '__float__'):
            num_to_check = float(other)
        elif hasattr(other, '__int__'):
            num_to_check = int(other)
        elif hasattr(other, '__bool__'):
            num_to_check = 1 if bool(other) else 0

        current = self.current
        if current < num_to_check:
            return -1
        elif current > num_to_check:
            return 1
        return 0

    def __eq__(self, other):
        return self.compare(other) == 0

    def __ne__(self, other):
        return self.compare(other) != 0

    def __ge__(self, other):
        return self.compare(other) >= 0

    def __gt__(self, other):
        return self.compare(other) == 1

    def __le__(self, other):
        return self.compare(other) <= 0

    def __lt__(self, other):
        return self.compare(other) < 0


class Percent:
    def __init__(self, name: str, current: float=0, cap: int=100, step: float=1, logger: Optional[Logger]=None):
        if current < 0:
            raise ValueError("The current must not be less than zero.")
        if cap < current:
            raise ValueError("The cap must not be less than current.")
        if step < 0.0001:
            raise ValueError("The step must not be less than 0.0001.")
        elif step > cap:
            raise ValueError("The step must not be greater than cap.")
        self._name = name
        self._current = current
        self._cap = cap
        self._step = step
        self._parent: Percent | None = None
        self._children: list[Percent] = []
        self._child_view: SequenceView[Percent] | None = None
        self._worth = 0
        self._logger: Logger | None = logger
        self.allow_messages = True

    def __call__(self, name: str, current: float=0, cap: int=100, step: float=1, worth: float=0):
        child = Percent(name, current, cap, step, self._logger)
        child._parent = self
        child._worth = worth
        self._children.append(child)
        return child

    @property
    def parent(self):
        return self._parent

    @property
    def children(self) -> Sequence[Percent]:
        if self._child_view is None:
            self._child_view = SequenceView(self._children)
        return self._child_view

    @property
    def name(self):
        return self._name

    @property
    def long_name(self):
        name = self.name
        if self.is_child():
            parent = self
            while parent.is_child():
                parent = parent._parent
                name = f"{parent.name} ; {name}"
        return name

    @property
    def percent(self):
        return self.current / self.cap

    @percent.setter
    def percent(self, value):
        if value < 0:
            raise ValueError("percent cannot be less than zero.")
        elif value > 1:
            raise ValueError("percent cannot be greater than one.")
        self.current = self.cap * value

    def larger_percent(self):
        return self.percent * 100

    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, amount):
        if amount >= self.cap:
            self._current = self.cap
        elif amount <= 0:
            self._current = 0
        else:
            self._current = amount

    @property
    def cap(self):
        return self._cap

    @cap.setter
    def cap(self, amount):
        if amount <= self.current:
            self._cap = self.current
        else:
            self._cap = amount

    @property
    def step(self):
        return self._step

    @step.setter
    def step(self, count):
        if count <= 0.0001:
            self._step = 0.0001
        elif count >= self.cap:
            self._step = self.cap
            # if self.current == 0:
            #    self._step = self.cap / 2
            # else:
            #    self._step = self.cap / self.current
        else:
            self._step = count

    @property
    def worth(self):
        return self._worth

    def is_child(self):
        return self._parent is not None

    def is_parent(self):
        return len(self._children) != 0

    def is_complete(self):
        return self.percent >= 1

    def _msg_format(self, title: Optional[str], message: Optional[str], allow_lr: bool) -> str:
        msg = message or ""
        if title is not None:
            msg = f"[{title}] {msg}"
        if allow_lr:
            if not msg.endswith("\r"):
                msg += "\r"
        msg = f"{self.long_name} : {msg}"
        return msg

    def msg_build(self, compact: bool=False, allow_lr: bool=False, add_title: Optional[str] = None, add_msg: Optional[str] = None):
        title = None
        message = None
        if self.is_complete():
            message = "COMPLETE"
        else:
            message += f"{'' if compact else 'At '}{self} complete"
        if self.is_child():
            title = "CHILD"
            if not compact:
                message = f"({self._parent.msg_build(compact=True)}) {message}"
        if self.is_parent():
            if title is not None:
                title += " | PARENT"
            else:
                title = "PARENT"
            if not compact:
                message = f"{message} with {len(self._children)} children left"
        msg = message
        if add_msg is not None:
            if add_msg.endswith("\r"):
                add_msg = add_msg.removesuffix("\r")
                allow_lr = True
            msg += f" (INFO: {add_msg})"
        if add_title is not None:
            if title is None:
                title = add_title
            else:
                title = f"{title} | {add_title}"
        return self._msg_format(title, msg, allow_lr)

    def _message_send(self, title: str = None, message: str = None, allow_lr=False, auto_make=False):
        if self.allow_messages and self._logger is not None:
            auto_make = auto_make or (title is None and message is None)
            if auto_make:
                msg = self.msg_build(False, allow_lr, title, message)
            else:
                msg = self._msg_format(title, message, allow_lr)
            if msg.endswith("\r"):
                msg = msg.removesuffix("\r")
                allow_lr = True
            self._logger.log("PERCENT", msg, end="\r" if allow_lr else "\n")

    def tick(self, times=1, worth=0, linear=True):
        """
        this method is the same as quick_tick if linear,
        otherwise will be non_linear_tick.
        However, unlike those two methods, this method
        will check for completion.

        :param times: The location of the tick or the number of ticks.
        :param worth: The worth of the tick.
        :param linear: Weather or not, it is a linear tick.
        :return:
        """
        if linear:
            self.quick_tick(times, worth)
        else:
            self.non_linear_tick(times, worth)
        self.check()

    def quick_tick(self, times=1, worth=0):
        """
        A quick tick that isn't officially checked for completion.

        :param times: The number of ticks to process.
        :param worth: The worth to add with the total process.
        :return:
        """
        if times < 1:
            times = 1
        self.current += worth + (self.step * times)
        self._message_send()

    def non_linear_tick(self, times=1, worth=0):
        """
        A single tick from the non-linear tick loop.

        :param times: The location of the tick.
        :param worth: The worth of the tick, plus one.
        :return:
        """
        if times < 1:
            times = 1
        worth += 1
        self.current += self.step * (worth / times)
        self._message_send()

    def tick_loop(self, times=1, worth=0, linear=False):
        """
        Will do several ticks, this method is best used for
        no-linear ticks.
        When used for linear ticks, the number of ticks preformed is
        equivalent to calling quick_tick `times` number of times with
        `times` as quick_tick's `times` argument.

        :param times: The number of loops to do, and ticks to complete.
        :param worth: The worth of each tick.
        :param linear: Weather or not the ticks are linear (Default: False)
        :return:
        """
        if times < 1:
            times = 1
        times = int(times)
        to_add = 0
        if linear:
            to_add += pow(worth, 2) + (self.step * pow(times, 2))
        else:
            worth += 1
            for t in range(1, times + 1):
                to_add += self.step * (worth / t)
            # to_add = round(to_add, 2)
        self.current += to_add
        if not self.is_complete():
            self._message_send()
        self.check()

    def _pass_child(self, worth):
        self.current += worth if worth != 0 else self.step

    def check(self):
        """
        Checks to see for completion of child requirements
        and detection of completion own self's percent bar.
        :return:
        """
        to_remove = []
        i = 0
        for child in self._children:
            if self.is_complete():
                break
            if child.is_complete():
                self._pass_child(child._worth)
                child._parent = None
                to_remove.append(i)
            i += 1
            self._message_send(allow_lr=i != len(self._children))
        rem_count = 0
        for rem in to_remove:
            del self._children[rem - rem_count]
            rem_count += 1
        if self.is_complete():
            self._message_send()
            if self.is_child():
                self._parent._children.remove(self)
                self._parent._pass_child(self._worth)
                # if self.is_parent():
                #    self.message_send("CHILD TRANSFER", "This child is complete, moving it's children to the parent.")
                #    self._parent._child_transfer(self._children)
                self._message_send("CHECK", "Launching check of parent.")
                self._parent.check()
                self._parent = None

    def reset(self):
        """
        Resets this Percent back to zero.
        And removes all child Percent.
        :return:
        """
        self.current = 0
        for child in self._children:
            child._parent = None
        self._children.clear()

    def __str__(self):
        return f"{self.percent:.4%}"

    def __int__(self):
        return int(self.larger_percent())

    def __float__(self):
        return self.percent

    def __bool__(self):
        """ True if this Percent is 100% else False """
        return self.is_complete()

    def __eq__(self, other):
        if isinstance(other, Percent):
            return self.percent == other.percent
        elif isinstance(other, int):
            return self.larger_percent() == other
        elif isinstance(other, float):
            return self.percent == other
        return False

    def __ne__(self, other):
        if isinstance(other, Percent):
            return self.percent != other.percent
        elif isinstance(other, int):
            return self.larger_percent() != other
        elif isinstance(other, float):
            return self.percent != other
        return False

    def __ge__(self, other):
        if isinstance(other, Percent):
            return self.percent >= other.percent
        elif isinstance(other, int):
            return self.larger_percent() >= other
        elif isinstance(other, float):
            return self.percent >= other
        return False

    def __gt__(self, other):
        if isinstance(other, Percent):
            return self.percent > other.percent
        elif isinstance(other, int):
            return self.larger_percent() > other
        elif isinstance(other, float):
            return self.percent > other
        return False

    def __le__(self, other):
        if isinstance(other, Percent):
            return self.percent <= other.percent
        elif isinstance(other, int):
            return self.larger_percent() <= other
        elif isinstance(other, float):
            return self.percent <= other
        return False

    def __lt__(self, other):
        if isinstance(other, Percent):
            return self.percent < other.percent
        elif isinstance(other, int):
            return self.larger_percent() < other
        elif isinstance(other, float):
            return self.percent < other
        return False

    def __iadd__(self, other):
        self.percent += other
        return self

    def __isub__(self, other):
        self.percent -= other
        return self

    def __imul__(self, other):
        self.percent *= other
        return self

    def __itruediv__(self, other):
        self.percent /= other
        return self

    def __ifloordiv__(self, other):
        self.percent //= other
        return self

    def __imod__(self, other):
        self.percent %= other
        return self

    def __ipow__(self, other):
        self.percent **= other
        return self

    def __abs__(self):
        """ abs(self) """
        return abs(self.percent)

    def __ceil__(self):
        """ Return the ceiling as an Integral. """
        return math.ceil(self.percent)

    def __floor__(self):
        """ Return the floor as an Integral. """
        return math.floor(self.percent)

    def __neg__(self):
        """ -self """
        return -self.percent

    def __pos__(self):
        """ +self """
        return +self.percent

    def __add__(self, value):
        """ Return self+value. """
        return self.percent + value

    def __radd__(self, value):
        """ Return value+self. """
        return value + self.percent

    def __sub__(self, value):
        """ Return self-value. """
        return self.percent - value

    def __rsub__(self, value):
        """ Return value-self. """
        return value - self.percent

    def __truediv__(self, value):
        """ Return self/value. """
        return self.percent / value

    def __rtruediv__(self, value):
        """ Return value/self. """
        return value / self.percent

    def __divmod__(self, value):
        """ Return divmod(self, value). """
        return divmod(self.percent, value)

    def __rdivmod__(self, value):
        """ Return divmod(value, self). """
        return divmod(value, self.percent)

    def __floordiv__(self, value):
        """ Return self//value. """
        return self.percent // value

    def __rfloordiv__(self, value):
        """ Return value//self. """
        return value // self.percent

    def __mod__(self, value):
        """ Return self%value. """
        return self.percent % value

    def __rmod__(self, value):
        """ Return value%self. """
        return value % self.percent

    def __mul__(self, value):
        """ Return self*value. """
        return self.percent * value

    def __rmul__(self, value):
        """ Return value*self. """
        return value * self.percent

    def __round__(self, ndigits=4):
        """
        Return the Integral closest to x, rounding half toward even.

        When an argument is passed, work like built-in round(x, ndigits).
        """
        return round(self.percent, ndigits)

    def __pow__(self, value, mod):
        """ Return pow(self, value, mod). """
        return pow(self.percent, value, mod)

    def __rpow__(self, value, mod):
        """ Return pow(value, self, mod). """
        return pow(value, self.percent, mod)

    def __trunc__(self):
        """ Return the Integral closest to x between 0 and x. """
        return math.trunc(self.percent)

