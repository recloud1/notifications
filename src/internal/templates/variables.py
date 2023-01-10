from typing import Set

import aiomisc
import jinja2schema

from internal.templates import wrapping


def search_variables(template_content: str) -> Set[str]:
    """
    Поиск всех переменных, содержащихся в шаблоне
    """

    if wrapping.is_wrapped(template_content):
        template_content = wrapping.unwrap_template(template_content)

    return set(jinja2schema.infer(template_content).keys())


def search_variables_async(template_content: str):
    return aiomisc.threaded(search_variables)(template_content)
