from abc import abstractmethod, ABC
from functools import wraps
from typing import Callable, Iterable, TypeVar, Any, Sequence, MutableSequence, overload, TypeAlias

from piethorn.collections.mapping import Map
from piethorn.collections.views import SequenceView, MapView
from piethorn.typing import argument


def _listener_name(name: int | str) -> str:
    if isinstance(name, int):
        return f"event_{name}"
    return name

class EventEnd(BaseException):
    def __init__(self, event: Event):
        super().__init__(f"Event {event.name} ended")
        self.event = event

class Event:
    """
    Actions
    -------

    The actions of an ``Event`` is defined by whether it's ``EventBuilder`` is
    static. If it is static, then the event's actions are deemed to span across
    the entire caller chain of the ``Listener``. While when it isn't static,
    the event's actions are deemed to only span the workings of a single ``caller_type``.
    """
    def __init__(
            self,
            builder: EventBuilder,
            caller: Listener,
    ):
        self._builder = builder
        self._caller = caller
        self._args: tuple = ()
        self._kwargs: dict = {}
        self._in_use: bool = False
        self._end: bool = False

    @property
    def name(self):
        """The name of the event"""
        return self._builder.name

    @property
    def caller(self):
        """The ``Listener`` that called this event"""
        return self._caller

    @property
    def listener(self):
        """The ``Listener`` that built this event"""
        return self._builder.listener

    @property
    def end_chain(self):
        return self._end

    @property
    def active(self):
        return self._in_use

    @property
    def args(self):
        return self._args

    @property
    def kwargs(self):
        return self._kwargs

    def pass_values(self, args: tuple=(), kwargs: dict | None=None):
        if not self.active:
            self._args = args
            self._kwargs = kwargs if kwargs is not None else {}

    def end(self, force: bool = False, end_chain_when_forced: bool = False):
        """
        Used to call the end of this event.

        If ``force`` is ``True``, then the ``EventEnd`` exception will be raised,
        this will end all event actions of the current ``caller_type``,
        but will not trigger ``end_chain``.
        To have ``end_chain`` set to ``True`` when ``force``, then ``end_chain_when_forced``
        must be ``True``, it's default to ``False``.

        While if ``force`` is ``False``, then the ``end_chain`` boolean will be set to ``True``
        and will finish event actions of the current ``caller_type`` before ending the caller chain of the ``Listener``.

        :param force: Whether to force end all further event actions.
        :param end_chain_when_forced: Whether to end the caller chain of the ``Listener`` when ``force`` is ``True``.
        :return:
        """
        if force:
            if end_chain_when_forced:
                self._end = True
            raise EventEnd(self)
        else:
            self._end = True


class EventBuilder:
    def __init__(
            self,
            listener: Listener | None = None,
            static: bool = False,
            copies_to_new: bool = False,
    ):
        self._listener: Listener | None = None
        self._name = "UNKNOWN_EVENT"
        self._static = static
        self._copies_to_new = copies_to_new
        self._values: dict[str, Any] = {}
        self._values_view = MapView(self._values)
        self._build = None
        if listener is not None:
            self._set_listener(listener)

    @property
    def listener(self):
        """The ``Listener`` that this ``EventBuilder`` is attributed to"""
        return self._listener

    @property
    def name(self):
        return self._name

    @property
    def static(self):
        return self._static

    @property
    def copies_to_new(self):
        return self._copies_to_new

    @property
    def values(self):
        return self._values_view

    def add_value(self, key: str, value: Any):
        self._values[key] = value

    def build(self, *args, **kwargs) -> Event:
        """
        Builds an ``Event``.

        If this ``EventBuilder`` is ``static``,
        then this builder will only build one ``Event``.

        Use ``clear_event`` to clear the built ``Event``.

        :param args:
        :param kwargs:
        :return:
        """
        caller = kwargs.pop("caller", self.listener)
        if not self._static or self._build is None:
            self._build = self.make_event(caller)
        self._build.pass_values(args, kwargs)
        return self._build
    
    def make_event(self, caller: Listener) -> Event:
        return Event(self, caller)

    def clear_event(self) -> Event | None:
        """
        Used to clear the built ``Event``.

        This method is mainly used in ``Listener.use``
        to clear the built ``Event`` at the end
        of the built ``Event``'s life cycle.

        :return: The removed ``Event``.
        """
        event = self._build
        self._build = None
        if event is not None:
            event._builder = None
            if event.active:
                pass
        return event
    
    def copy(self, **kwargs) -> EventBuilder:
        event_builder = EventBuilder(
            listener=kwargs.pop("listener", self.listener),
            static=kwargs.pop("static", self.static),
            copies_to_new=kwargs.pop("copies_to_new", self.copies_to_new),
        )
        return event_builder
    
    def _set_listener(self, listener: Listener):
        self._listener = listener
        name = listener.name if listener.name.lower().startswith("event") else f"event_{listener.name}"
        self._name = name.replace("_", " ").title().replace(" ", "")
        self._build = None
    
    def new_listener(self, listener: Listener) -> EventBuilder:
        """
        Updates this ``EventBuilder``'s ``Listener``.

        If ``copies_to_new`` is true, then this method will
        create a ``copy`` of this ``EventBuilder`` with the
        new ``Listener``.

        :param listener: The new ``Listener``.
        :return: This ``EventBuilder`` or a new ``EventBuilder``.
        """
        event_builder = self
        if self.copies_to_new:
            event_builder = self.copy(listener=listener)
        else:
            if listener is not self.listener:
                event_builder._set_listener(listener)
        return event_builder

DEFAULT_EVENT_BUILDER = EventBuilder(static=True, copies_to_new=True)

caller_type: TypeAlias = Callable[[Event], bool]

class Listener:
    def __init__(
            self,
            name: int | str,
            event_builder: EventBuilder=DEFAULT_EVENT_BUILDER,
    ):
        self._name = _listener_name(name)
        self.__callers__: list[caller_type] = []
        self._event_builder = event_builder.new_listener(self)
        self._builder = None

    @property
    def name(self):
        return self._name

    @property
    def event_builder(self):
        return self._event_builder

    def event(self, args: tuple, kwargs: dict, *, caller: Listener | None=None) -> Event:
        """
        Builds an event with ``event_builder``.

        Refer to ``EventBuilder.build`` for further information on how events are built.

        :param args:
        :param kwargs:
        :param caller: The ``Listener`` that called the event. Leave empty to default to ``event_builder.listener``.
        :return: The created ``Event``.
        """
        return self.event_builder.build(*args, **kwargs, caller=caller)

    def use(self, *args, **kwargs):
        """
        Calls this ``Listener``'s caller chain.

        The caller chain is the list of ``caller_type``s
        that are to be called when the ``Listener`` is triggered.

        The boolean returned by a ``caller_type`` is used to determine whether
        the next ``caller_type`` is called. So, if it returns ``False``, then
        no further callers in the caller chain will be called.

        :param args: The values to be passed to the ``Event.args`` property.
        :param kwargs: The key-value pairs to be passed to the ``Event.kwargs`` property.
        :return:
        """
        for calling in self.__callers__:
            if callable(calling):
                try:
                    if not self._event_builder.static:
                        self._event_builder.clear_event()
                    caller_event = self.event(args, kwargs)
                    caller_event._in_use = True
                    cont = calling(caller_event)
                    caller_event._in_use = False
                    if caller_event.end_chain or not cont:
                        break
                except EventEnd as e:
                    e.event._in_use = False
                    if e.event.end_chain:
                        break
        self._event_builder.clear_event()

    def __call__(self, event: Event) -> bool:
        """
        A ``Listener`` callable so that they can be passed as a ``caller_type``.

        :param event: The event from the calling ``Listener``.
        :return: Whether this caller should end the calling Listener's caller chain.
        """
        cont = True
        for calling in self.__callers__:
            if callable(calling):
                cont = calling(event)
                if not cont:
                    break
        return cont

    def add(self, caller: caller_type):
        if not callable(caller):
            raise TypeError("Cannot add a caller that isn't callable.")
        self.__callers__.append(caller)

    def get(self, index: int):
        return self.__callers__[index]

    def remove(self, caller):
        self.__callers__.remove(caller)

    def __len__(self):
        return len(self.__callers__)


class ListenerBuilder:
    def __init__(
            self,
            default_event_builder: EventBuilder=DEFAULT_EVENT_BUILDER,
    ):
        self.__listeners__: Map[str, Listener] = Map()
        self._listenable: Listenable | None = None
        self._event_builder: EventBuilder = default_event_builder

    def get(self, name: int | str) -> Listener:
        if isinstance(name, int):
            return self.__listeners__.value_at_index(name)
        return self.__listeners__[_listener_name(name)]

    def build(self, name: int | str, event_builder: EventBuilder | None=None):
        return Listener(name, event_builder if event_builder is not None else self._event_builder)

    def add(self, name: int | str, event_builder: EventBuilder | None=None):
        listener = self.build(name, event_builder)
        listener._builder = self
        self.__listeners__[listener.name] = listener

    def __len__(self):
        return len(self.__listeners__)

    def __iter__(self):
        return iter(self.__listeners__.values())


class Listenable:
    def __init__(self, *named: str, listener_builder: ListenerBuilder | None = None):
        """

        :param event_count: The number of unnamed events.
        :param named: The names of each event listener to be created.
        """
        self.__listeners__: ListenerBuilder = listener_builder if listener_builder is not None else ListenerBuilder()
        self.__listeners__._listenable = self

        for name in named:
            self.__listeners__.add(name)

    @property
    def listener_count(self):
        return  len(self.__listeners__)

    def get_listener(self, name: int | str) -> Listener:
        """
        Gets a ``Listener`` for use.

        :param name: The name of the ``Listener`` to get. May also be the index of the ``Listener``.
        :return: The ``Listener`` with the provided name.
        """
        return self.__listeners__.get(name)

    def add_listener(self, name: int | str, caller: caller_type):
        """
        Adds a function to a ``Listener``.

        :param name: The name of the ``Listener`` to add a caller to.
        :param caller: The function to call when it's ``listener``'s use method is called.
        """
        self.get_listener(name).add(caller)

    def remove_listener(self, name: int | str, caller):
        """
        Removes a function from a ``Listener``.

        :param name: The name of the ``Listener`` to remove a caller from.
        :param caller: The function to remove.
        :return:
        """
        self.get_listener(name).remove(caller)

    def event_trigger(self, name: int | str, args: tuple, kwargs: dict):
        self.get_listener(name).use(*args, **kwargs)



class ListenerSequence[T](Listenable, Sequence[T], ABC):
    def __init__(self):
        super().__init__("get")

    @abstractmethod
    def __getter__(self, index):
        pass

    def __getitem__(self, index: int | slice):
        value = self.__getter__(index)
        self.get_listener("get").use(value, index)
        return value


class MutableListenerSequence[T](ListenerSequence[T], MutableSequence[T]):
    def __init__(self):
        super().__init__()
        for name in ("add", "set", "remove"):
            self.__listeners__.add(name)

    @abstractmethod
    def __setter__(self, index: int | slice, value: T | Iterable[T]) -> T:
        pass

    @abstractmethod
    def __adder__(self, index: int | slice, value: T | Iterable[T]):
        pass

    @abstractmethod
    def __remover__(self, index: int | slice | argument.Argument.empty) -> tuple[T, bool]:
        pass

    def insert(self, index, value):
        self.__adder__(index, value)
        self.get_listener("add").use(index, value)

    def __setitem__(self, key: int | slice, value: T | Iterable[T]):
        self.get_listener("set").use(key, self.__setter__(key, value), value)

    def __delitem__(self, index):
        value, removed = self.__remover__(index)
        self.get_listener("remove").use(index, value, removed)