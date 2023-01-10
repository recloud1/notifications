BASE_TEMPLATE_NAME = "base-template"


def content_block(template_content: str) -> str:
    return f"{{% block content %}}\n{template_content}{{% endblock %}}"


wrap_template_str = "{{% extends '{BASE_TEMPLATE_NAME}' %}}\n{block_wrapped_content}"


def is_wrapped(template_content: str):
    return template_content.startswith(
        wrap_template_str.format(
            BASE_TEMPLATE_NAME=BASE_TEMPLATE_NAME, block_wrapped_content=""
        )[:11]
    )


def wrap_template(template_content: str) -> str:
    """
    Обёртка для полноценной шаблонизации c использованием базового шаблона
    """
    block_wrapped_content = content_block(template_content + "\n")
    return wrap_template_str.format(
        BASE_TEMPLATE_NAME=BASE_TEMPLATE_NAME,
        block_wrapped_content=block_wrapped_content,
    )


def unwrap_template(template_content: str) -> str:
    """
    Убираем обёртку в базовый шаблон для корректного отображения пользователю
    (или для шаблонизации без обёртки в базовый шаблон).
    """
    return "\n".join(template_content.split("\n")[2:-1])
