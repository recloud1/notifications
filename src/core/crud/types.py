from typing import NewType, TypeVar

Entity = TypeVar("Entity")

Id = int | str

Count = NewType("Count", int)
