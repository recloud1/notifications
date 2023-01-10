import contextlib
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.crud.base import BaseCrud
from core.crud.exceptions import ObjectNotExists
from models import Template

template_crud = BaseCrud(entity=Template)


async def get_template(session: AsyncSession, template_slug: str) -> Template:
    query = select(Template).where(Template.slug == template_slug)
    result = await session.scalar(query)
    if result is None:
        raise ObjectNotExists("Шаблон не найден", [template_slug])

    return result


async def get_base_template(session: AsyncSession) -> Template | None:
    base_template = await session.scalar(
        select(Template).where(Template.is_base == True)
    )
    return base_template


@contextlib.asynccontextmanager
async def base_template_installed(session: AsyncSession):
    """
    Проверка на наличие базового шаблона-обёртки для отправки уведомлений
    """
    base_template = await get_base_template(session)
    if base_template is None:
        raise HTTPException(
            HTTPStatus.BAD_REQUEST, detail="Базовый шаблон не установлен"
        )

    yield


def ensure_all_variables_specified(template: Template, template_data: dict):
    """
    Проверка на наличие всех переменных перед созданием уведомления.

    :param template: шаблон по которому будет создано уведомление.
    :param template_data: данные для заполнения шаблона.
    """
    try:
        required_vars = set(template.variables)
    except ValueError as e:
        raise ValueError(
            f"Expected a list of required variable names "
            f'for a template. Got: "{type(template.variables)}"'
        ) from e
    specified_vars = set(template_data.keys())

    if not required_vars.issubset(specified_vars):
        v = (", ".join([f'"{i}"' for i in (required_vars - specified_vars)]),)

        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            detail=f"Не удалось создать уведомление. Не указаны переменные: {v}",
        )
