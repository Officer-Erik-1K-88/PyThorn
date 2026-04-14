from types import UnionType
from typing import Any, MutableMapping, Collection, TypeAlias

_TypeInfo: TypeAlias = type | UnionType
_ClassInfo: TypeAlias = _TypeInfo | tuple[_TypeInfo, ...]

class Argument:
    """
    Used to define information on an argument to a
    class, method, or function.

    The Argument class is used for typing that
    python's built in type check system doesn't allow for.
    """

    def __init__(self, key: str, type_var: _ClassInfo, **kwargs) -> None:
        """
        Creates an argument for the given key.

        :param key: The name of the argument
        :param type_var: The valid type that this argument is allowed to store.
        :param kwargs: The optional keyword arguments. These include ``default``, ``allowed_values``, and ``value``.
        """
        self._key = key
        self._type_var = type_var
        self._kwargs = kwargs
        self._has_value = "value" in self._kwargs
        self._value = self._kwargs.pop("value") if self._has_value else None

    @property
    def key(self) -> str:
        """
        The name of the argument.
        :return:
        """
        return self._key

    @property
    def type_var(self) -> _ClassInfo:
        """
        The type of the argument.
        :return:
        """
        return self._type_var

    @property
    def has_default(self) -> bool:
        """
        Whether the argument has a default value.
        :return:
        """
        return "default" in self._kwargs

    @property
    def default(self):
        """
        The default value of the argument.
        :return:
        """
        return self._kwargs.get("default", None)

    def set_default(self, default: Any):
        """
        Sets the default value of the argument.
        :param default: The default value of the argument
        :return:
        """
        valid = self.validate(default, False)
        if not valid:
            raise TypeError(f"Default value '{default}' is invalid for argument '{self._key}'")
        self._kwargs["default"] = default

    @property
    def allowed_values(self) -> Collection[Any] | None:
        """
        The allowed values of the argument.
        :return:
        """
        return self._kwargs.get("allowed_values", None)

    @property
    def has_value(self) -> bool:
        """
        Whether the argument has a value.
        :return:
        """
        return self._has_value

    @property
    def value(self):
        """
        The value of the argument.

        If ``has_value`` is ``False``, then ``default`` is returned.
        :return:
        """
        if self.has_value:
            return self._value
        return self.default

    def set(self, value: Any):
        """
        Sets the value of the argument.

        ``validate`` is called on the value.

        :param value: The value to set.
        :return: The old value
        """
        self.validate(value)
        old = self.value
        self._has_value = True
        self._value = value
        return old

    def remove(self):
        """
        Removes the value from the argument.
        :return: The removed value
        """
        value = self.value
        self._has_value = False
        self._value = None
        return value

    def validate(self, value: Any, throw: bool=True) -> bool:
        """
        Checks whether the provided value is valid.

        :param value: The value to be checked
        :param throw: Whether to throw a ``TypeError`` instead of returning ``False`` when value is invalid
        :return: Whether the value is valid
        """
        if not isinstance(value, self.type_var):
            if throw:
                raise TypeError(f"Type mismatch for {self.key}: expected {self.type_var}, got {type(value)}")
            return False
        elif self.allowed_values is not None:
            if value not in self.allowed_values:
                if throw:
                    raise TypeError(f"Value of '{value}' is invalid for {self.key}")
                return False
        return True

    def copy(self, **kwargs):
        """
        Makes a copy of the argument.

        ``value`` is the only property not given to the new Argument.

        :param kwargs: The properties to override.
        :return: A new Argument with the same properties
        """
        kwargs.setdefault("key", self.key)
        kwargs.setdefault("type_var", self.type_var)
        for k, v in self._kwargs.items():
            kwargs.setdefault(k, v)
        return type(self)(**kwargs)


class Arguments(MutableMapping[str, Any]):
    """
    Used to store all the arguments of a class, method, or function.
    """

    def __init__(self, *args: Argument, strict_keys: bool=True, silent_strict: bool=False, typing_with_value: bool=False) -> None:
        """
        Creates a new Arguments object.

        :param args: The arguments
        :param strict_keys: Whether a key must exist for calls to it.
        :param silent_strict: Whether to silence errors from strict keys.
        :param typing_with_value: Whether to type created arguments with the type that it's value has.
        """
        self._typings: dict[str, Argument] = {}
        self._strict_keys = strict_keys
        self._silent_strict = silent_strict
        self._typing_with_value = typing_with_value
        for arg in args:
            self.set(arg)

    @property
    def strict_keys(self):
        """
        Whether the key to an argument must exist when
        validating, setting, or removing.
        :return:
        """
        return self._strict_keys

    @property
    def silent_strict(self):
        """
        Whether to silence errors from strict keys.
        :return:
        """
        return self._silent_strict

    @property
    def typing_with_value(self):
        """
        Whether to type internally created arguments with the
        type that it's value has.

        If ``False``, then will type new arguments with ``Any``.
        Otherwise, will type new arguments with ``type(value)``.
        :return:
        """
        return self._typing_with_value

    def _get_type(self, value) -> type:
        return Any if self._typing_with_value or value is None else type(value)

    def validate(self, key: str, value: Any, throw: bool=True) -> bool:
        """
        Checks to see if there is an argument for ``key``.
        If one exists, then ``value`` will be type checked.

        If ``throw`` is ``True``, then will raise a ``TypeError`` when value is invalid.

        If ``strict_keys`` is ``True``, then will return ``False`` when key is not in the map.
        However, will raise a ``KeyError`` when ``throw`` is ``True``, this error only occurs when
        ``silent_strict`` is ``False``.

        If ``strict_keys`` is ``False`` and key is not in the map, then ``True`` is returned.

        :param key: The name of the argument to get the typing set for
        :param value: The value to be checked
        :param throw: Whether to raise an error instead of returning ``False``
        :return: Whether the key-value pair is valid
        """
        if key not in self._typings:
            if self._strict_keys:
                if throw and not self._silent_strict:
                    raise KeyError(f"Key '{key}' is invalid")
                return False
            return True
        return self._typings[key].validate(value, throw)

    def get_arg(self, key: str):
        """
        Gets the Argument for ``key``.

        If ``strict_keys`` is ``True``, then will raise ``KeyError`` if ``key`` is not in the map,
        otherwise ``None`` is returned.

        :param key: The name of the argument to get
        :return: The Argument for ``key``
        """
        if key not in self._typings:
            if self._strict_keys and not self._silent_strict:
                raise KeyError(f"Key '{key}' is invalid")
            return None
        return self._typings[key]

    def set(self, typing: Argument) -> bool:
        """
        Adds ``typing`` to the typing map.

        If the key defined by ``typing`` is already present in the typing map,
        then, given ``strict_keys`` is ``True``, then will raise a ``KeyError``.
        This error only occurs when ``strict_keys`` is ``False``,
        otherwise ``False`` is returned.

        While if ``strict_keys`` is ``False``, then the key is overridden.

        :param typing: The typing to add
        :return: Whether the ``typing`` has been added to the typing map
        """
        if self._strict_keys:
            if typing.key in self._typings:
                if self._silent_strict:
                    return False
                raise KeyError(f"Key '{typing.key}' is already present in the kwargs")
        self._typings[typing.key] = typing
        return True

    def ensure_defaults(self, **kwargs):
        """
        Ensures that all the provided keys has a default value.
        If the key doesn't have a default value, then the given value is set
        as the default value.
        :param kwargs: The key-value pairs
        :return:
        """
        for key, value in kwargs.items():
            if key not in self._typings:
                if self._strict_keys:
                    if self._silent_strict:
                        continue
                    raise KeyError(f"Key '{key}' is invalid")
                self._typings[key] = Argument(key, self._get_type(value), default=value)
            else:
                if not self._typings[key].has_default:
                    self._typings[key].set_default(value)

    def remove(self, key: str):
        """
        Removes ``key`` from the typing map.

        If key is not present in the typing map, then ``None`` is returned.
        However, a ``KeyError`` is raised when ``strict_keys`` is ``True``,
        error is only raised when ``silent_strict`` is ``False``.

        :param key: The argument to remove from the typing map
        :return: The removed argument
        """
        if key not in self._typings:
            if self._strict_keys:
                if self._silent_strict:
                    return None
                raise KeyError(f"Key '{key}' is not present in the kwargs")
            return None
        return self._typings.pop(key, None)

    def __len__(self) -> int:
        return len(self._typings)

    def __contains__(self, key: str) -> bool:
        return key in self._typings

    def __iter__(self):
        return iter(self._typings)

    def __setitem__(self, key, value, /):
        if key not in self._typings:
            if self._strict_keys:
                raise KeyError(f"Key '{key}' is not present in the kwargs")
            self._typings[key] = Argument(key, self._get_type(value), value=value)
        else:
            self._typings[key].set(value)

    def __getitem__(self, key, /):
        if key not in self._typings:
            raise KeyError(f"Key '{key}' is not present in the kwargs")
        return self._typings[key].value

    def __delitem__(self, key, /):
        if key not in self._typings:
            raise KeyError(f"Key '{key}' is not present in the kwargs")
        self._typings[key].remove()
