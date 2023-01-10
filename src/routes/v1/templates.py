from http import HTTPStatus
from typing import Any

import jinja2
from fastapi import Body, Depends, HTTPException, Path, Query
from fastapi.routing import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse

from dependencies.auth import user_info_dep
from internal.templates.environment import DbLoader, TemplateEnvironment
from internal.templates.templates import (
    base_template_installed,
    get_base_template,
    template_crud,
)
from internal.templates.variables import search_variables_async
from models import Template, fresh_timestamp
from schemas.auth import UserInfo
from schemas.templates import TemplateBare, TemplateList, TemplateUpdate
from utils.db_session import get_db_session

templates = APIRouter()


@templates.get(
    "/",
    description="Получение информации обо всех шаблонах, доступных в системе",
    summary="Получение шаблонов",
    response_model=TemplateList,
)
async def get_templates(
    page: int = Query(1),
    rows_per_page: int = Query(None, alias="rowsPerPage", le=101),
    session: AsyncSession = Depends(get_db_session),
    author: UserInfo = user_info_dep,
) -> TemplateList:
    results, count = await template_crud.get_multi(session, page, rows_per_page)

    return TemplateList(data=results, rows_per_page=rows_per_page, page=page)


@templates.get(
    "/{template_id}",
    description="Получение информации о конкретном шаблоне",
    summary="Получение шаблона",
    response_model=TemplateBare,
)
async def get_template(
    template_id: int = Path(..., ge=1),
    session: AsyncSession = Depends(get_db_session),
    author: UserInfo = user_info_dep,
) -> TemplateBare:
    result = await template_crud.get(session, template_id)

    return TemplateBare.from_orm(result)


@templates.post(
    "/",
    description="Создание нового шаблона",
    summary="Создание шаблона",
    response_model=TemplateBare,
    status_code=HTTPStatus.CREATED,
)
async def create_template(
    data: TemplateUpdate,
    author: UserInfo = user_info_dep,
    session: AsyncSession = Depends(get_db_session),
) -> TemplateBare:
    if data.is_base:
        existing_base_template = await get_base_template(session)
        if existing_base_template:
            raise HTTPException(
                HTTPStatus.BAD_REQUEST,
                detail="Базовый шаблон для данного сервиса уже создан",
            )

    result = await template_crud.create(
        session,
        data,
        created_by=author.id,
        updated_by=author.id,
        variables=list(await search_variables_async(data.content)),
    )

    DbLoader().clear_cache()

    return TemplateBare.from_orm(result)


@templates.put(
    "/{template_id}",
    description="Обновление информации о шаблоне",
    summary="Обновление шаблона",
    response_model=TemplateBare,
)
async def update_template(
    data: TemplateUpdate,
    template_id: int = Path(..., ge=1),
    author: UserInfo = user_info_dep,
    session: AsyncSession = Depends(get_db_session),
) -> TemplateBare:
    db_object = await template_crud.get(session, template_id)
    result = await template_crud.update(
        session,
        db_object,
        data,
        updated_at=fresh_timestamp(),
        updated_by=author.id,
        variables=list(await search_variables_async(data.content)),
        exclude={"is_base"},
    )

    DbLoader().clear_cache()

    return TemplateBare.from_orm(result)


@templates.delete(
    "/{template_id}",
    description="Удаление шаблона",
    summary="Удаление шаблона",
    response_model=TemplateBare,
)
async def delete_template(
    template_id: int = Path(..., ge=1),
    author: UserInfo = user_info_dep,
    session: AsyncSession = Depends(get_db_session),
) -> TemplateBare:
    result = await template_crud.get(session, template_id)

    if result.is_base:
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            detail="Невозможно удалить базовый шаблон. Обратитесь к администратору",
        )

    try:
        await session.delete(result)
        await session.flush()

        DbLoader().clear_cache()
    except Exception:
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            detail="Данный шаблон используется. Удаление запрещено",
        )

    return TemplateBare.from_orm(result)


@templates.post(
    "/{template_id}/render",
    description="Рендеринг HTML-шаблона",
    summary="Рендеринг шаблона",
)
async def render_template(
    template_id: int = Path(..., ge=1),
    variables: dict[str, Any] = Body(None),
    session: AsyncSession = Depends(get_db_session),
    author: UserInfo = user_info_dep,
) -> HTMLResponse:
    """
    Рендер шаблона с тестовым набором данных
    """
    template_obj: Template = await template_crud.get(session, template_id)

    async with base_template_installed(session):

        env = TemplateEnvironment()

        env.loader.pre_load_template(template_obj)

        rendering_template = env.get_template(
            template_obj.slug, wrap_by_base_template=True
        )

        if variables is None:
            variables = {
                name: f"переменная {str(i)}"
                for i, name in enumerate(template_obj.variables)
            }

        try:
            rendered = rendering_template.render(**variables)
        except jinja2.TemplateNotFound:
            # мы только что убедились, что текущий шаблон в бд точно есть (да и мы его уже подгрузили).
            # Значит проблемы с унаследованным шаблоном, т.е. с базовым
            raise HTTPException(
                HTTPStatus.BAD_REQUEST,
                detail="Не удалось найти базовый шаблон. Обратитесь к администратору",
            )

        return HTMLResponse(content=rendered)
