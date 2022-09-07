import abc


class SingletonMeta(type):
    """Metaclass for defining Singletons."""

    __instances: dict[type, type] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls.__instances:
            cls.__instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls.__instances[cls]


class Singleton(metaclass=SingletonMeta):
    ...


class SingletonABCMeta(SingletonMeta, abc.ABCMeta):
    """Metaclass subclassing SingletonMeta and ABCMeta."""


class SingletonABC(metaclass=SingletonABCMeta):
    ...
