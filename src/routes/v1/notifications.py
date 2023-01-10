from http import HTTPStatus
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from core.crud.exceptions import ObjectNotExists
from internal.notifications.notifications import (
    notification_crud,
    notification_recurrence_crud,
)
from internal.templates.templates import (
    base_template_installed,
    ensure_all_variables_specified,
    get_template,
)
from schemas.notifications import NotificationBare, NotificationCreate
from tasks.notifications import send_notification
from utils.db_session import get_db_session

notifications = APIRouter()


@notifications.get(
    "/{notification_id}",
    description="Получение подробной информации об уведомлении",
    summary="Получение информации об уведомлении",
    response_model=NotificationBare,
)
async def get_notification(
    notification_id: str = Path(..., example=str(uuid4()), max_length=36),
    session: AsyncSession = Depends(get_db_session),
) -> NotificationBare:
    notification = await notification_crud.get(session, notification_id)
    return await NotificationBare.from_orm_async(notification, session)


@notifications.post(
    "/",
    description="Создание уведомления",
    summary="Создание уведомления",
    response_model=NotificationBare,
)
async def create_notification(
    data: NotificationCreate,
    notification_slug: str = Path(..., example="send-invite"),
    session: AsyncSession = Depends(get_db_session),
    # service: Service = fastapi.Depends(auth_by_service),
) -> NotificationBare:
    try:
        async with base_template_installed(session):
            template = await get_template(session, notification_slug)
            if data.user_id:
                ensure_all_variables_specified(template, data.template_data)

    except ObjectNotExists:
        raise HTTPException(
            HTTPStatus.NOT_FOUND,
            detail=f'Тип уведомлений "{notification_slug}" не найден.',
        )

    notification = await notification_crud.create(
        session=session, data=data, template_id=template.id, exclude={"recurrence"}
    )

    if data.recurrence:
        await notification_recurrence_crud.create(
            session=session, data=data.recurrence, notification_id=notification.id
        )
    else:
        # без commit'a мы не можем гарантировать, что уведомление будет доступно в базе данных
        # в момент выполнения задачи
        await session.commit()
        await send_notification.send_async()

    packed = await NotificationBare.from_orm_async(notification, session)

    return packed
