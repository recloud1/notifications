import threading
from typing import Any, Optional, TypeVar

import cachetools

SetType = TypeVar("SetType", bound=set)


def add_to_set(set_: Optional[SetType], value: Any) -> SetType:
    if set_ is None:
        set_ = set()
    set_.add(value)

    return set_


class SingletonMeta(type):
    """
    Реализация класса Singleton
    """

    _instances = {}

    _lock: threading.Lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            key = cachetools.keys.hashkey(cls, *args, **kwargs)
            if key not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[key] = instance
        return cls._instances[key]
