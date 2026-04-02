from typing import Any, MutableMapping

# TODO: Merge everything in this file into a single class

_FORMAT_Typing = {} # where the types are stored

def validate_format_value(key, value, throw: bool=True) -> bool:
    """
    Checks to see if there is a typing set for ``key``.
    If one exists, then ``value`` will be type checked.

    :param key: The format to validate the value for
    :param value: The value paired with the key
    :param throw: Whether to throw a ``TypeError`` instead of returning ``False`` when value is invalid
    :return: Whether the value is valid
    """
    if key in _FORMAT_Typing:
        type_check = _FORMAT_Typing.get(key)
        if not isinstance(value, type_check[0]):
            if throw:
                raise TypeError(f"Type mismatch for {key}: expected {type_check[0]}, got {type(value)}")
            return False
        elif type_check[1] is not None:
            if value not in type_check[1]:
                if throw:
                    raise TypeError(f"Value of '{value}' is invalid for {key}")
                return False
    return True


class TypeChecker(MutableMapping[str, Any]):
    def __init__(
            self,
            seq=None,
            **kwargs,
    ) -> None:
        self._kwargs = dict(seq, **kwargs)
        self.validate()

    def ensure_defaults(self, *keys: str | tuple[str, Any]):
        """
        Ensures that the provided keys exist.

        If a given key is a ``tuple``, then the first item is the key and the second item is the default value.
        If this isn't given, then will check the internal store for a default value of key, if one isn't found,
        then ``None`` is used as default value.

        If the default value is given via a ``tuple`` here, then we will run the key and value through ``validate_format_value``.

        :param keys: The keys to ensure
        :return:
        """
        for k in keys:
            is_tuple = isinstance(k, tuple)
            key, default_value = k if is_tuple else (k, None)
            if not is_tuple:
                default_value = _FORMAT_Typing.get(key)[2]
            else:
                if not validate_format_value(key, default_value, False):
                    raise TypeError(f"Cannot define '{default_value}' as the default of '{key}'")
            self._kwargs.setdefault(key, default_value)

    def validate(self):
        """
        Runs all key-value pairs through ``validate_format_value``.
        Throws ``TypeError`` if the value of a key is invalid for that specific key.
        :return:
        """
        for key, value in self._kwargs.items():
            validate_format_value(key, value, True)

    def __len__(self):
        return len(self.keys())

    def __iter__(self):
        for key in self._kwargs:
            yield key

    def __getitem__(self, name: str) -> Any:
        return self._kwargs[name]

    def __setitem__(self, name: str, value: Any) -> None:
        validate_format_value(name, value, True)
        self._kwargs[name] = value

    def __delitem__(self, key):
        del self._kwargs[key]

    def __getattr__(self, name: str) -> Any:
        return self[name]

    def __setattr__(self, name: str, value: Any) -> None:
        if hasattr(self, name):
            super().__setattr__(name, value)
        else:
            self[name] = value

    def __delattr__(self, name: str) -> None:
        if hasattr(self, name):
            super().__delattr__(name)
        else:
            del self[name]