import re


def slug_validator(value: str) -> str:
    """
    Проверка служебного имени на соответствие нотации.

    :param value: значение для проверки
    :raises: ValueError: при некорректном значении
    :return: значение, при его корректности
    """
    if not re.fullmatch(r"[a-z]+[a-z0-9-]*", value):
        raise ValueError(f"Incorrect slug {value}")
    return value
