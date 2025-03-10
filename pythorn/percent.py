from math import floor, ceil, trunc


class Percent:
    def __init__(self, name: str, current=0, cap=100, step=1, limit_0_1=True):
        self.limit_0_1 = limit_0_1
        if self.limit_0_1:
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
        self._worth = 0
        self._index: int | None = None
        self.always_add_lr = False
        self.allow_messages = True
    
    def __call__(self, name: str, current=0, cap=100, step=1, worth=0):
        child = Percent(name, current, cap, step)
        child._parent = self
        child._worth = worth
        child._index = len(self._children)
        self._children.append(child)
        return child

    def _child_transfer(self, children: list):
        i = 0
        for child in children:
            child._parent = self
            child._index = len(self._children)
            self._children.append(child)
            i += 1
            self.message_send("CHILD TRANSFER", f"{i} of {len(children)} transferred", allow_lr=i!=len(children))

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

    def msg_build(self, title: str = None, message: str = None, compact=False, allow_lr=False, auto_make=False):
        add_title = None
        add_msg = None
        if auto_make:
            add_title = title
            add_msg = message
            title = None
            message = None
        if title is None and message is None:
            if self.is_complete():
                message = "COMPLETE"
            else:
                if compact:
                    message = f"{self} complete"
                else:
                    message = f"At {self} complete"
            if self.is_child():
                title = "CHILD"
                if not compact:
                    parent_saved_alr = self._parent.always_add_lr
                    self._parent.always_add_lr = False
                    message = f"({self._parent.msg_build(compact=True)}) {message}"
                    self._parent.always_add_lr = parent_saved_alr
            if self.is_parent():
                if title is not None:
                    title += " | PARENT"
                else:
                    title = "PARENT"
                if not compact:
                    message = f"{message} with {len(self._children)} children left"
        elif message is None:
            message = title
            title = None
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
        if title is not None:
            msg = f"[{title}] {msg}"
        if self.always_add_lr or allow_lr:
            if not msg.endswith("\r"):
                msg += "\r"
        msg = f"{self.long_name} : {msg}"
        return msg

    def message_send(self, title: str = None, message: str = None, allow_lr=False, auto_make=False):
        if self.allow_messages:
            msg = self.msg_build(title, message, False, allow_lr, auto_make)
            if msg.endswith("\r"):
                msg = msg.removesuffix("\r")
                print(msg, end="\r")
            else:
                print(msg)

    def is_child(self):
        return self._parent is not None

    def is_parent(self):
        return len(self._children) != 0
    
    def is_complete(self):
        return self.percent >= 1
    
    @property
    def percent(self):
        return self.current / self.cap

    @percent.setter
    def percent(self, value):
        if self.limit_0_1:
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
        self._current = amount
        if self.limit_0_1:
            if self._current >= self.cap:
                self._current = self.cap
            elif self._current < 0:
                self._current = 0

    @property
    def cap(self):
        return self._cap

    @cap.setter
    def cap(self, amount):
        self._cap = amount
        if self.limit_0_1:
            if self._cap < self.current:
                self._cap = self.current

    @property
    def step(self):
        return self._step

    @step.setter
    def step(self, count):
        self._step = count
        if self.limit_0_1:
            if self._step <= 0.0001:
                self._step = 0.0001
            elif self._step > self.cap:
                self._step = self.cap
                #if self.current == 0:
                #    self._step = self.cap / 2
                #else:
                #    self._step = self.cap / self.current

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
        self.message_send()

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
        self.message_send()

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
            for t in range(1, times+1):
                to_add += self.step * (worth / t)
            #to_add = round(to_add, 2)
        self.current += to_add
        if not self.is_complete():
            self.message_send()
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
        cur_index = 0
        for child in self._children:
            if self.is_complete():
                break
            child._index = cur_index
            if child.is_complete():
                self._pass_child(child._worth)
                child._parent = None
                to_remove.append(i)
                cur_index -= 1
            i += 1
            cur_index += 1
            self.message_send(allow_lr=i!=len(self._children))
        rem_count = 0
        for rem in to_remove:
            del self._children[rem-rem_count]
            rem_count += 1
        if self.is_complete():
            self.message_send()
            if self.is_child():
                del self._parent._children[self._index]
                self._parent._pass_child(self._worth)
                #if self.is_parent():
                #    self.message_send("CHILD TRANSFER", "This child is complete, moving it's children to the parent.")
                #    self._parent._child_transfer(self._children)
                self.message_send("CHECK", "Launching check of parent.")
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
        return ceil(self.percent)

    def __floor__(self):
        """ Return the floor as an Integral. """
        return floor(self.percent)

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
        return trunc(self.percent)
