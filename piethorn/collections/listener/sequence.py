from abc import abstractmethod, ABC
from typing import Iterable, MutableSequence, Sequence

from piethorn.collections.listener.listenable import Listenable
from piethorn.collections.listener.listens import listens


class ListenerSequence[T](Listenable, Sequence[T], ABC):
    def __init__(self):
        super().__init__("get")

    @listens("get")
    @abstractmethod
    def __getitem__(self, index: int | slice):
        pass


class MutableListenerSequence[T](ListenerSequence[T], MutableSequence[T]):
    def __init__(self):
        super().__init__()
        for name in ("add", "set", "remove"):
            self.__listeners__.add(name)

    @listens("add")
    @abstractmethod
    def insert(self, index, value):
        pass

    @listens("set")
    @abstractmethod
    def __setitem__(self, key: int | slice, value: T | Iterable[T]):
        pass

    @listens("remove")
    @abstractmethod
    def __delitem__(self, index):
        pass