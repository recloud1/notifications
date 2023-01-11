from aiohttp import ClientSession
from sqlalchemy.orm import joinedload

from core.config import envs
from internal.notifications.handlers import EmailNotificationHandler
from models import Backend, Notification
from utils.db_session import db_session_manager

# dramatiq нужно корректно инициализировать, поэтому мы достаём пропатченный вариант из своего файла
from .core import dramatiq


@dramatiq.actor
def send_notification(notification_id: str):
    backend_handlers = {Backend.email.value: send_email, Backend.sms.value: send_sms}

    with db_session_manager() as session:
        notification: Notification = session.get(
            Notification, notification_id, options=[joinedload(Notification.template)]
        )
        for backend, send_to in notification.contacts.items():
            if not send_to:
                send_to = enrichment_notification.send([notification.user_id])

            handler = backend_handlers.get(backend)

            handler.send(notification_id=notification_id, send_to=send_to)


@dramatiq.actor
def send_email(notification_id: str, send_to: str):
    with db_session_manager() as session:
        email_handler = EmailNotificationHandler(notification_id, send_to)
        email_handler(session)


@dramatiq.actor
def enrichment_notification(user_ids: list[str]):
    async with ClientSession() as session:
        url = f"{envs.external.auth}/user-info-batch/"
        async with session.post(url=url, data={"ids": user_ids}) as response:
            data = await response.json()
            result = [i.email for i in data]

            return result


@dramatiq.actor
def send_sms(notification_id: str, send_to: str):
    """
    Заглушка для отправки уведомления с помощью СМС
    """
