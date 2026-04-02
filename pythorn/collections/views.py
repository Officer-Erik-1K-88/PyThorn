from typing import Mapping, Iterator, Sequence, Optional

from pythorn.collections.range import slice_len


class SequenceView[T](Sequence[T]):
    def __init__(self, origin: Sequence[T], *, reverse: bool = False, cut: Optional[slice]=None):
        """
        Creates a view of a sequence.

        :param origin: The original sequence to make a view of.
        :param reverse: Whether to make the view reversed or not.
        :param cut: The viewable area of the original sequence. Defaults to full origin.
        """
        self._origin = origin
        self._reverse = reverse
        self._cut = cut if cut is not None else slice(0, None, 1)
        self._parent: Optional[SequenceView[T]] = None

    @property
    def origin_size(self):
        return len(self._origin)

    @property
    def is_reversed(self):
        return self._reverse

    @property
    def parent(self):
        return self._parent

    @property
    def has_parent(self):
        return self._parent is not None

    @property
    def cut(self):
        # Fully normalize against the real origin length.
        return slice(*self._cut.indices(self.origin_size))

    @property
    def has_cut(self):
        return self.cut != slice(0, self.origin_size, 1)

    def _view_range(self) -> range:
        base = range(*self.cut.indices(self.origin_size))
        return base[::-1] if self._reverse else base

    def _index_helper(self, index: int | slice) -> int | slice:
        r = self._view_range()
        if isinstance(index, slice):
            sub = r[index]
            return slice(sub.start, sub.stop, sub.step)
        length = len(r)

        if index < 0:
            index += length
        if index < 0 or index >= length:
            raise IndexError(f"The index is out of range: {index}")

        return r[index]

    def __len__(self):
        return slice_len(self.cut, self.origin_size)

    def __contains__(self, value) -> bool:
        if self.has_cut:
            return value in self._origin[self.cut]
        return value in self._origin

    def count(self, value) -> int:
        if self.has_cut:
            return self._origin[self.cut].count(value)
        return self._origin.count(value)

    def index(self, value, start: int = 0, stop: Optional[int] = None) -> int:
        r = self._view_range()
        length = len(r)

        if start < 0:
            start += length
        if stop is None:
            stop = length
        elif stop < 0:
            stop += length

        start = max(0, start)
        stop = min(length, stop)

        for view_i in range(start, stop):
            if self._origin[r[view_i]] == value:
                return view_i

        raise ValueError(f"{value!r} is not in SequenceView")

    def __getitem__(self, index: int | slice) -> Sequence[T] | T:
        new_index = self._index_helper(index)
        if isinstance(index, slice):
            view = SequenceView[T](self._origin, cut=new_index)
            view._parent = self
            return view
        return self._origin[new_index]

    def __iter__(self) -> Iterator[T]:
        for i in self._view_range():
            yield self._origin[i]

    def __reversed__(self) -> Iterator[T]:
        for i in reversed(self._view_range()):
            yield self._origin[i]


class MapView[KT, VT](Mapping[KT, VT]):
    """
    Wraps a `Mapping` to make an immutable view of it.
    """
    def __init__(self, origin: Mapping[KT, VT]):
        self._origin = origin

    def __len__(self):
        return len(self._origin)

    def get(self, key: KT, default=None, /) -> VT:
        return self._origin.get(key, default)

    def __getitem__(self, key, /):
        return self._origin[key]

    def __iter__(self):
        return iter(self._origin)

    def __contains__(self, key: KT) -> bool:
        return key in self._origin

    def __eq__(self, other):
        return self._origin == other
