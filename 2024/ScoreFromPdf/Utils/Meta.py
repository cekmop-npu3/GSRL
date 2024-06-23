from typing import Any


__all__ = (
    'ReadOnly',
    'Singleton'
)


class ReadOnlyMeta(type):
    class Attr:
        def __init__(self, value: Any) -> None:
            self.value = value

        def __get__(self, instance, owner) -> Any:
            return self.value

        def __set__(self, instance, value):
            raise AttributeError("Can't set attribute")

    def __new__(mcs, name, bases, attrs) -> object:
        new_attrs = {}
        for key, value in attrs.items():
            if not key.startswith('__'):
                value = mcs.Attr(value)
            new_attrs[key] = value
        return super().__new__(mcs, name, bases, new_attrs)

    def __setattr__(cls, key, value) -> None:
        if hasattr(cls, key):
            raise AttributeError("Can't set attribute")
        super().__setattr__(key, value)


class ReadOnly(metaclass=ReadOnlyMeta):
    pass


class Singleton(type):
    classes_ = {}

    def __call__(cls, *args, **kwargs) -> object:
        if cls not in cls.classes_.keys():
            cls.classes_[cls] = super().__call__(*args, **kwargs)
        return cls.classes_.get(cls)
